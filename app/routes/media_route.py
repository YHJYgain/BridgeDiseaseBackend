import os
import time

from PIL import Image
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from moviepy import VideoFileClip
from werkzeug.utils import secure_filename

from app.constants import OperationType, UserRole
from app.decorators import login_required
from app.models import Operation, Media, db, User
from app.routes import media_routes
from app.utils import handle_operation_failure, is_valid_file_type, handle_file_upload, handle_operation_success, \
    adjust_page_if_needed, get_pagination_params


@media_routes.route('/upload', methods=['POST'])
@jwt_required()
@login_required
def upload():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    media_file = request.files.get('media_file')
    description = request.form.get('description', '暂无描述')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.CREATE,
        description="上传媒体文件",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()

    if media_file and not is_valid_file_type(media_file):
        failure_message = "【上传媒体文件失败】媒体文件不合规"
        new_operation = handle_operation_failure(new_operation, start_time, failure_message, current_user_id)
        current_app.logger.error(failure_message)
        return jsonify({'operation': new_operation.to_dict()}), 400

    # 获取文件名并进行安全处理
    file_name = secure_filename(media_file.filename)

    # 保存文件到指定目录（返回相对路径）
    file_path = handle_file_upload(media_file, 'medias')

    # 获取文件类型（文件后缀）
    file_type = file_name.rsplit('.', 1)[1].lower()

    # 获取文件绝对路径
    absolute_path = os.path.join(current_app.root_path, file_path)

    # 获取分辨率
    resolution_width = resolution_height = None
    if file_type in {'png', 'jpg', 'jpeg'}:  # 图片
        with Image.open(absolute_path) as img:
            resolution_width, resolution_height = img.size
    elif file_type in {'mp4', 'avi', 'mov'}:  # 视频
        with VideoFileClip(file_path) as video:
            resolution_width, resolution_height = video.size

    new_media = Media(
        file_name=file_name,
        file_path=file_path,
        description=description,
        file_size=os.path.getsize(absolute_path) / 1024,  # 转换为 KB
        file_type=file_type,
        resolution_width=resolution_width,
        resolution_height=resolution_height,
        owner_id=current_user_id,
    )
    db.session.add(new_media)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【上传媒体文件成功】new_media: {new_media}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'new_media': new_media.to_dict(),
    }), 201


@media_routes.route('/medias/<int:user_id>', methods=['GET'])
@jwt_required()
@login_required
def user_medias(user_id):
    start_time = time.time()  # 记录操作开始时间

    # 获取分页参数（默认为第 1 页，每页 5 条记录）
    page, per_page = get_pagination_params()

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.READ,
        description=f"获取用户 ID={user_id} 媒体文件",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定用户身份
    user = User.query.get(user_id)

    # 校验字段
    validation_checks = [
        (not user, f"【获取用户 ID={user_id} 媒体文件失败】该用户不存在", 404),
        (current_user_id != user_id and current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【获取用户 ID={user_id} 操作记录失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.error(message)
            return jsonify({'operation': new_operation.to_dict()}), code

    # 获取指定用户媒体文件
    query = Media.query.filter_by(owner_id=user_id)
    page, medias_total, pages = adjust_page_if_needed(query, page, per_page)
    medias = query.paginate(page=page, per_page=per_page, error_out=False)

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(
        f"【获取用户 ID={user_id} 媒体文件成功】total: {medias_total}, per_page: {per_page}, page: {page}, pages: {pages}, medias: {[media.to_dict() for media in medias]}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'medias': [media.to_dict() for media in medias],
        'total': medias_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200


@media_routes.route('/detail/<int:media_id>', methods=['GET'])
@jwt_required()
@login_required
def media_detail(media_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.READ,
        description=f"获取媒体文件 ID={media_id} 详情",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定媒体文件
    media = Media.query.get(media_id)

    # 校验字段
    validation_checks = [
        (not media, f"【获取媒体文件 ID={media_id} 详情失败】该媒体文件不存在", 404),
        (
            media and media.owner_id != current_user_id and current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
            f"【获取媒体文件 ID={media_id} 详情失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.error(message)
            return jsonify({'operation': new_operation.to_dict()}), code

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【获取媒体文件 ID={media_id} 详情成功】media: {media.to_dict()}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'media': media.to_dict(),
    }), 200


@media_routes.route('/update/<int:media_id>', methods=['PUT'])
@jwt_required()
@login_required
def update(media_id):
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    description = request.form.get('description')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.READ,
        description=f"更新媒体文件 ID={media_id} 信息",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定媒体文件
    updated_media = Media.query.get(media_id)

    # 校验字段
    validation_checks = [
        (not updated_media, f"【更新媒体文件 ID={media_id} 信息失败】该媒体文件不存在", 404),
        (
            updated_media and updated_media.owner_id != current_user_id and current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
            f"【更新媒体文件 ID={media_id} 信息失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.error(message)
            return jsonify({'operation': new_operation.to_dict()}), code

    # 更新媒体文件信息
    updated_media.description = description
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)
    current_app.logger.info(f"【更新媒体文件 ID={media_id} 信息成功】updated_media: {updated_media.to_dict()}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'updated_media': updated_media.to_dict(),
    }), 200
