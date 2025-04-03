import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
import numpy as np
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ultralytics import YOLO

from app.constants import TaskStatus, OperationType, UserRole
from app.decorators import login_required
from app.models import Detection, Media, Model, Operation, User, db
from app.routes import detection_routes
from app.utils import handle_operation_success, handle_operation_failure, compute_count, compute_perimeter, \
    compute_area, compute_shape_complexity, compute_texture_roughness, compute_crack_width, compute_avg_hue, \
    convert_detection_results, evaluate_disease_severity, get_pagination_params, adjust_page_if_needed


@detection_routes.route('/detection_segmentation', methods=['POST'])
@jwt_required()
@login_required
def detection_segmentation():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的 JSON 参数
    data = request.get_json()
    model_id = data.get('model_id')
    media_id = data.get('media_id')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.EXECUTE,
        description="执行病害检测分割",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取模型和媒体
    model = Model.query.get(model_id)
    media = Media.query.get(media_id)

    # 校验字段
    validation_checks = [
        (not model_id or not media_id, "【检测分割失败】媒体/模型 ID 为空", 400),
        (not model, f"【检测分割失败】模型 ID={model_id} 不存在", 404),
        (not media, f"【检测分割失败】媒体 ID={media_id} 不存在", 404),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.error(message)
            return jsonify({'operation': new_operation.to_dict()}), code

    # 创建新的检测分割记录
    new_detection = Detection(
        detection_at=datetime.now(ZoneInfo("Asia/Shanghai")),
        owner_id=current_user_id,
        model_id=model_id,
        media_id=media_id
    )
    db.session.add(new_detection)
    db.session.commit()

    try:
        # 更新任务状态为进行中
        new_detection.status = TaskStatus.IN_PROGRESS
        db.session.commit()

        # 获取文件夹配置
        models_folder = current_app.config['MODELS_FOLDER']
        medias_folder = current_app.config['MEDIAS_FOLDER']
        results_folder = current_app.config['RESULTS_FOLDER']

        # 确保目录存在
        os.makedirs(models_folder, exist_ok=True)
        os.makedirs(medias_folder, exist_ok=True)
        os.makedirs(results_folder, exist_ok=True)

        # 导入模型/媒体并执行预测
        model_path = Path(models_folder) / os.path.basename(model.model_path)
        source_path = Path(medias_folder) / os.path.basename(media.media_path)
        image = cv2.imread(str(source_path))
        yolo_model = YOLO(model_path)
        results = yolo_model.predict(
            source=source_path,
            imgsz=1024,
            retina_masks=True,
            save=True,
            save_crop=True,
            project=results_folder,
            name=current_user.username,
            exist_ok=True,  # 每次都保存在同一文件夹
        )

        # 前端请求每次都只有一个 media，results 只有一个元素，因此只需要取第一个结果
        result = results[0]

        # 检测分割结果图路径
        result_image_path = os.path.join('static', 'results', current_user.username,
                                         os.path.basename(media.media_path))
        # 裁剪结果图路径
        cropped_image_path = os.path.join('static', 'results', current_user.username, 'crops')

        # 检测分割原始结果（JSON 字符串）
        detection_json_str, segmentation_json_str = convert_detection_results(result)

        # 获取所有 masks 并合并
        masks_data = result.masks.data.cpu().numpy()  # 确保在 CPU 上
        combined_masks = np.any(masks_data, axis=0).astype(np.uint8)  # 确保重复区域只计算一次

        # 获取识别结果的类别
        cls = result.boxes.cls

        # 计算病害指标
        disease_count = compute_count(result.masks)  # 病害数量
        disease_perimeter = compute_perimeter(combined_masks)  # 病害周长（像素）
        disease_area = compute_area(combined_masks)  # 病害面积（像素）
        shape_complexity = compute_shape_complexity(disease_perimeter, disease_area)  # 形状复杂度
        texture_roughness = compute_texture_roughness(combined_masks)  # 纹理粗糙度
        crack_width = compute_crack_width(combined_masks) if "裂缝" in model.disease_category else 0.0  # 裂缝宽度
        avg_hue = compute_avg_hue(combined_masks, image) if "锈蚀" in model.disease_category else 0.0  # 平均色调

        # 根据检测结果计算病害严重性得分、病害等级、病害描述
        disease_severity_score, disease_grade, disease_description = evaluate_disease_severity(disease_count,
                                                                                               disease_perimeter,
                                                                                               disease_area,
                                                                                               shape_complexity,
                                                                                               texture_roughness,
                                                                                               crack_width,
                                                                                               avg_hue, media)

        # 更新检测信息
        new_detection.status = TaskStatus.COMPLETED
        new_detection.raw_detection_result = detection_json_str
        new_detection.raw_segmentation_result = segmentation_json_str
        new_detection.result_image_path = result_image_path
        new_detection.cropped_image_path = cropped_image_path
        new_detection.disease_count = disease_count
        new_detection.disease_perimeter = disease_perimeter
        new_detection.disease_area = disease_area
        new_detection.shape_complexity = shape_complexity
        new_detection.texture_roughness = texture_roughness
        new_detection.crack_width = crack_width
        new_detection.avg_hue = avg_hue
        new_detection.disease_severity_score = disease_severity_score
        new_detection.disease_grade = disease_grade
        new_detection.disease_description = disease_description
        db.session.commit()

        # 记录操作
        new_operation = handle_operation_success(new_operation, start_time, current_user_id)

        current_app.logger.info(f"【检测分割成功】new_detection: {new_detection}")
        return jsonify({
            'operation': new_operation.to_dict(),
            'new_detection': new_detection.to_dict(),
        }), 200

    except Exception as error:
        # 发生错误，更新任务状态为失败
        new_detection.status = TaskStatus.FAILED
        db.session.commit()

        # 记录操作失败
        failure_message = f"【检测分割失败】服务器内部发生错误，请联系管理员"
        new_operation = handle_operation_failure(new_operation, start_time, failure_message, current_user_id)

        # 获取详细的堆栈追踪信息
        stack_trace = traceback.format_exc()

        # 获取请求的相关信息
        request_method = request.method
        request_url = request.url
        request_data = request.get_data(as_text=True)

        # 记录日志，帮助排查问题
        current_app.logger.error(f"Error: {str(error)}\nStack Trace: {stack_trace}\n"
                                 f"Request Method: {request_method}\n"
                                 f"Request URL: {request_url}\n"
                                 f"Request Data: {request_data}")
        return jsonify({'operation': new_operation.to_dict()}), 500


@detection_routes.route('/detections/<int:user_id>', methods=['GET'])
@jwt_required()
@login_required
def user_detections(user_id):
    # 获取分页参数（从请求中获取，默认为第 1 页，每页 5 条记录）
    default_page = request.args.get('page', 1, type=int)
    default_per_page = request.args.get('per_page', 5, type=int)
    page, per_page = get_pagination_params(default_page, default_per_page)

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户身份
    user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (not user, f"【获取用户 ID={user_id} 检测分割记录失败】该用户不存在", 404),
        (current_user_id != user_id and current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【获取用户 ID={user_id} 检测分割记录失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.error(message)
            return jsonify({'failure_message': message}), code

    # 获取指定用户检测分割记录
    query = Detection.query.filter_by(owner_id=user_id)
    page, detections_total, pages = adjust_page_if_needed(query, page, per_page)
    detections = query.paginate(page=page, per_page=per_page, error_out=False)

    current_app.logger.info(
        f"【获取用户 ID={user_id} 检测分割记录成功】total: {detections_total}, per_page: {per_page}, page: {page}, pages: {pages}, detections: {[detection.to_dict() for detection in detections]}")
    return jsonify({
        'detections': [detection.to_dict() for detection in detections],
        'total': detections_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200


@detection_routes.route('/detections/all', methods=['GET'])
@jwt_required()
@login_required
def all_detections():
    # 获取分页参数（从请求中获取，默认为第 1 页，每页 5 条记录）
    default_page = request.args.get('page', 1, type=int)
    default_per_page = request.args.get('per_page', 5, type=int)
    page, per_page = get_pagination_params(default_page, default_per_page)

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER:
        failure_message = f"【获取所有检测分割记录失败】当前登录用户非管理员/开发人员，权限不足"
        current_app.logger.error(failure_message)
        return jsonify({'failure_message': failure_message}), 403

    # 获取所有媒体
    query = Detection.query
    page, detections_total, pages = adjust_page_if_needed(query, page, per_page)
    detections = query.paginate(page=page, per_page=per_page, error_out=False)

    current_app.logger.info(
        f"【获取所有检测分割记录成功】total: {detections_total}, per_page: {per_page}, page: {page}, pages: {pages}, detections: {[detection.to_dict() for detection in detections]}")
    return jsonify({
        'detections': [detection.to_dict() for detection in detections],
        'total': detections_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200


@detection_routes.route('/statistics', methods=['GET'])
@jwt_required()
@login_required
def statistics():
    # 查询检测记录总数
    total_detections = Detection.query.count()

    # 查询不同状态的检测记录数量
    pending_detections = Detection.query.filter(Detection.status == TaskStatus.PENDING).count()
    in_progress_detections = Detection.query.filter(Detection.status == TaskStatus.IN_PROGRESS).count()
    completed_detections = Detection.query.filter(Detection.status == TaskStatus.COMPLETED).count()
    failed_detections = Detection.query.filter(Detection.status == TaskStatus.FAILED).count()

    # 构建统计数据
    detections_statistics = {
        'total': total_detections,
        'pending': pending_detections,
        'in_progress': in_progress_detections,
        'completed': completed_detections,
        'failed': failed_detections
    }

    return jsonify({
        "detections_statistics": detections_statistics,
    }), 200
