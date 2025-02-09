import os
import time

from PIL import Image
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from moviepy import VideoFileClip
from werkzeug.utils import secure_filename

from app.constants import OperationType
from app.models import Operation, User, Media, db
from app.routes import media_routes
from app.utils import handle_operation_failure, is_valid_file_type, handle_file_upload, handle_operation_success


@media_routes.route('/upload', methods=['POST'])
@jwt_required()
def upload_media():
    start_time = time.time()  # 记录操作开始时间

    media_file = request.files.get('media_file')
    description = request.form.get('description', '暂无描述')

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.CREATE,
        description="上传媒体文件",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 校验字段
    validation_checks = [
        (not current_user, f"【上传媒体文件失败】服务器数据异常，用户 ID: {current_user_id} 不存在"),
        (media_file and not is_valid_file_type(media_file), "【上传媒体文件失败】媒体文件类型不合规")
    ]
    for condition, message in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message)
            return jsonify({'operation': new_operation.to_dict()}), 400

    # 获取文件名并进行安全处理
    file_name = secure_filename(media_file.filename)

    # 保存文件到指定目录（返回相对路径）
    file_path = handle_file_upload(media_file, 'medias')

    # 获取文件的类型（文件后缀）
    file_type = file_name.rsplit('.', 1)[1].lower()

    # 绝对路径
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
        owner_id=current_user_id
    )
    db.session.add(new_media)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【上传媒体文件成功】media: {new_media}")
    return jsonify({'operation': new_operation.to_dict(), 'media': new_media.to_dict()}), 201
