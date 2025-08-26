import base64
import json
import os
import time
import traceback
from datetime import datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image
from flask import jsonify, request, current_app, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from ultralytics import YOLO

from app import Config
from app.constants import TaskStatus, OperationType, UserRole
from app.decorators import login_required
from app.models import Detection, Media, Model, Operation, User, db
from app.routes import detection_routes
from app.utils import handle_operation_success, handle_operation_failure, compute_count, compute_perimeter, \
    compute_area, compute_shape_complexity, compute_texture_roughness, compute_crack_width, compute_avg_hue, \
    evaluate_disease_severity, get_pagination_params, adjust_page_if_needed, unify_result_media_format, delete_file, \
    user_rate_limit, DateTimeEncoder

# 获取文件夹配置，并确保目录存在
MODELS_FOLDER = Config.MODELS_FOLDER
MEDIAS_FOLDER = Config.MEDIAS_FOLDER
RESULTS_FOLDER = Config.RESULTS_FOLDER
os.makedirs(MODELS_FOLDER, exist_ok=True)
os.makedirs(MEDIAS_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)


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
            current_app.logger.warning(message)
            return jsonify({'operation': new_operation.to_dict()}), code

    # 查找是否已存在相同 owner_id 和 media_id 的检测分割记录
    existing_detection = Detection.query.filter_by(owner_id=current_user_id, media_id=media_id).first()
    if existing_detection:
        # 如果存在则更新检测时间，后续会更新其他字段
        new_detection = existing_detection
        new_detection.model_id = model_id
        new_detection.detection_at = datetime.now(ZoneInfo("Asia/Shanghai"))
        current_app.logger.info("【检测分割】找到已有记录，进行更新")
    else:
        # 如果不存在则创建新的检测分割记录
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

        # 导入模型/媒体并执行预测
        model_path = Path(MODELS_FOLDER) / os.path.basename(model.model_path)
        source_path = Path(MEDIAS_FOLDER) / os.path.basename(media.media_path)
        yolo_model = YOLO(model_path)
        results = yolo_model.predict(
            source=source_path,
            imgsz=1024,
            half=True,
            retina_masks=True,
            save=True,
            project=RESULTS_FOLDER,
            name=current_user.username,
            stream=True,
            exist_ok=True,  # 每次都保存在同一文件夹
        )

        def generate():
            # 初始化媒体帧数
            frame_count = media.frame_count
            disease_frame_count = frame_count

            # 初始化病害指标
            total_disease_count = 0
            total_disease_perimeter = 0.0
            total_disease_area = 0.0
            total_shape_complexity = 0.0
            total_texture_roughness = 0.0
            total_crack_width = 0.0
            total_avg_hue = 0.0

            # 初始化检测分割耗时
            total_detection_duration = 0.0

            # 初始消息
            init_msg = {
                'type': 'START',
                'existing_detection': bool(existing_detection),
            }
            yield json.dumps(init_msg, cls=DateTimeEncoder) + '\n'

            for idx, result in enumerate(results):
                # 计算帧检测时长
                frame_detection_duration = sum(result.speed.values())
                total_detection_duration += frame_detection_duration

                # 统计帧级指标
                if result.masks is None:
                    disease_frame_count = max(disease_frame_count - 1, 0)
                else:
                    masks = result.masks
                    masks_data = masks.data.cpu().numpy()  # 确保在 CPU 上
                    combined_masks = np.any(masks_data, axis=0).astype(np.uint8)  # 确保重复区域只计算一次

                    frame_disease_count = compute_count(masks)  # 病害数量
                    frame_disease_perimeter = compute_perimeter(combined_masks)  # 病害周长（像素）
                    frame_disease_area = compute_area(combined_masks)  # 病害面积（像素）
                    frame_shape_complexity = compute_shape_complexity(frame_disease_perimeter,
                                                                      frame_disease_area)  # 形状复杂度
                    frame_texture_roughness = compute_texture_roughness(combined_masks)  # 纹理粗糙度
                    frame_crack_width = compute_crack_width(
                        combined_masks) if "裂缝" in model.disease_category else 0.0  # 裂缝宽度
                    frame_avg_hue = compute_avg_hue(combined_masks,
                                                    result.orig_img) if "锈蚀" in model.disease_category else 0.0  # 平均色调

                    total_disease_count += frame_disease_count
                    total_disease_perimeter += frame_disease_perimeter
                    total_disease_area += frame_disease_area
                    total_shape_complexity += frame_shape_complexity
                    total_texture_roughness += frame_texture_roughness
                    total_crack_width += frame_crack_width
                    total_avg_hue += frame_avg_hue

                # 绘制并编码图像
                annotated_img = result.plot()  # ndarray
                annotated_pil = Image.fromarray(annotated_img)  # 转为 PIL.Image
                buf = BytesIO()
                annotated_pil.save(buf, format='JPEG')  # 正确保存
                b64 = base64.b64encode(buf.getvalue()).decode('ascii')  # 编码为 base64 字符串

                frame_msg = {
                    'type': 'FRAME',
                    'frame_index': idx,
                    'frame_image': b64,
                    'frame_detection_duration': frame_detection_duration,
                }
                yield json.dumps(frame_msg, cls=DateTimeEncoder) + '\n'

            current_app.logger.info(
                f"【检测分割】total_disease_count: {total_disease_count}, disease_frame_count: {disease_frame_count}")

            # 计算平均病害指标
            average_disease_count = total_disease_count // disease_frame_count if disease_frame_count != 0 else 0
            average_disease_perimeter = total_disease_perimeter / disease_frame_count if disease_frame_count != 0 else 0.0
            average_disease_area = total_disease_area / disease_frame_count if disease_frame_count != 0 else 0.0
            average_shape_complexity = total_shape_complexity / disease_frame_count if disease_frame_count != 0 else 0.0
            average_texture_roughness = total_texture_roughness / disease_frame_count if disease_frame_count != 0 else 0.0
            average_crack_width = total_crack_width / disease_frame_count if disease_frame_count != 0 else 0.0
            average_avg_hue = total_avg_hue / disease_frame_count if disease_frame_count != 0 else 0.0

            # 计算帧平均检测分割耗时
            avg_frame_detection_duration = total_detection_duration / frame_count if frame_count != 0 else 0.0

            # 根据检测结果计算病害严重性得分、病害等级、病害描述
            disease_severity_score, disease_grade, disease_description = evaluate_disease_severity(
                average_disease_count,
                average_disease_perimeter,
                average_disease_area,
                average_shape_complexity,
                average_texture_roughness,
                average_crack_width,
                average_avg_hue, media)

            # 检测分割结果路径
            result_path = unify_result_media_format(media, current_user)

            # 更新检测分割信息
            new_detection.status = TaskStatus.COMPLETED
            new_detection.result_path = result_path
            new_detection.disease_count = average_disease_count
            new_detection.disease_perimeter = average_disease_perimeter
            new_detection.disease_area = average_disease_area
            new_detection.shape_complexity = average_shape_complexity
            new_detection.texture_roughness = average_texture_roughness
            new_detection.crack_width = average_crack_width
            new_detection.avg_hue = average_avg_hue
            new_detection.disease_severity_score = disease_severity_score
            new_detection.disease_grade = disease_grade
            new_detection.disease_description = disease_description
            new_detection.detection_duration = total_detection_duration
            new_detection.avg_frame_detection_duration = avg_frame_detection_duration
            db.session.commit()

            # 记录操作
            success_op = handle_operation_success(new_operation, start_time, current_user_id)

            end_msg = {
                'type': 'END',
                'existing_detection': bool(existing_detection),
                'new_detection': new_detection.to_dict(),
                'operation': success_op.to_dict(),
            }

            current_app.logger.info(f"【检测分割成功】new_detection: {success_op}")
            yield json.dumps(end_msg, cls=DateTimeEncoder) + '\n'

        return Response(stream_with_context(generate()), mimetype='application/json')
    except Exception as error:
        # 发生错误，更新任务状态为失败
        new_detection.status = TaskStatus.FAILED
        db.session.commit()

        # 记录操作失败
        failure_message = f"【检测分割错误】服务器内部发生错误，请联系管理员"
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


@detection_routes.route('/detail/<int:detection_id>', methods=['GET'])
@jwt_required()
@login_required
def detail(detection_id):
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定检测分割记录
    detection = Detection.query.get(detection_id)

    # 校验字段
    validation_checks = [
        (not detection, f"【获取检测分割 ID={detection_id} 详情失败】该检测分割记录不存在", 404),
        (detection and detection.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【获取检测分割 ID={detection_id} 详情失败】您非管理员/开发人员，无法查看他人的检测分割记录详情", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'failure_message': message}), code

    return jsonify({
        'detection': detection.to_dict(),
    }), 200


@detection_routes.route('/delete/<int:detection_id>', methods=['GET'])
@jwt_required()
@login_required
def delete_detection(detection_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.DELETE,
        description=f"删除检测分割 ID={detection_id} 记录",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定媒体
    deleted_detection = Detection.query.get(detection_id)

    # 校验字段
    validation_checks = [
        (not deleted_detection, f"【删除检测分割 ID={detection_id} 记录失败】该检测分割记录不存在", 404),
        (deleted_detection and deleted_detection.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【删除检测分割 ID={detection_id} 记录失败】您非管理员/开发人员，无法删除他人的检测分割记录", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'operation': new_operation.to_dict()}), code

    # 删除实际文件
    file_abs_path = os.path.join(current_app.root_path, deleted_detection.result_path)
    delete_file(file_abs_path)

    # 删除数据库记录
    db.session.delete(deleted_detection)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(
        f"【删除检测分割 ID={detection_id} 记录成功】deleted_detection: {deleted_detection}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'deleted_detection': deleted_detection.to_dict(),
    }), 200


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
         f"【获取用户 ID={user_id} 检测分割记录失败】您非管理员/开发人员，无法查看他人的检测分割记录", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message)
            return jsonify({'failure_message': message}), code

    # 获取指定用户检测分割记录
    query = (
        Detection.query
        .filter(Detection.owner_id == user_id)
        .join(Model, Detection.model_id == Model.model_id)
        .join(Media, Detection.media_id == Media.media_id)
        .join(User, Detection.owner_id == User.user_id)
        .add_columns(
            Model.model_name.label('model_name'),
            Media.media_name.label('media_name'),
            Media.file_type.label('media_type'),
            User.username.label('owner_username'),
        )
    )
    page, detections_total, pages = adjust_page_if_needed(query, page, per_page)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    detections = []
    for detection, model_name, media_name, media_type, owner_username in paginated.items:
        d = detection.to_dict()
        d.update({
            'model_name': model_name,
            'media_name': media_name,
            'media_type': media_type,
            'owner_username': owner_username,
        })
        detections.append(d)

    current_app.logger.info(
        f"【获取用户 ID={user_id} 检测分割记录成功】total: {detections_total}, per_page: {per_page}, page: {page}, pages: {pages}, detections: {detections}, operator: {current_user}")
    return jsonify({
        'detections': detections,
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
        failure_message = f"【获取所有检测分割记录失败】您非管理员/开发人员，权限不足"
        current_app.logger.warning(failure_message)
        return jsonify({'failure_message': failure_message}), 403

    # 获取所有媒体
    query = (
        Detection.query
        .join(Model, Detection.model_id == Model.model_id)
        .join(Media, Detection.media_id == Media.media_id)
        .join(User, Detection.owner_id == User.user_id)
        .add_columns(
            Model.model_name.label('model_name'),
            Media.media_name.label('media_name'),
            Media.file_type.label('media_type'),
            User.username.label('owner_username'),
        )
    )
    page, detections_total, pages = adjust_page_if_needed(query, page, per_page)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    detections = []
    for detection, model_name, media_name, media_type, owner_username in paginated.items:
        detection_dict = detection.to_dict()
        detection_dict.update({
            'model_name': model_name,
            'media_name': media_name,
            'media_type': media_type,
            'owner_username': owner_username,
        })
        detections.append(detection_dict)

    current_app.logger.info(
        f"【获取所有检测分割记录成功】total: {detections_total}, per_page: {per_page}, page: {page}, pages: {pages}, detections: {detections}, operator: {current_user}")
    return jsonify({
        'detections': detections,
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
