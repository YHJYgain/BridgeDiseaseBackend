import os
import time

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.constants import OperationType, UserRole
from app.decorators import login_required
from app.models import Operation, Media, db, User, Detection
from app.routes import media_routes
from app.utils import handle_operation_failure, allowed_image_file, handle_file_upload, handle_operation_success, \
    adjust_page_if_needed, get_pagination_params, allowed_video_file, get_media_info, delete_file, user_rate_limit


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
        description="上传媒体",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 先获取文件名
    file_name = secure_filename(media_file.filename) if media_file else None

    # 检查文件名是否已存在
    existing_media = Media.query.filter_by(media_name=file_name).first() if file_name else None

    # 校验字段
    validation_checks = [
        (media_file and not (allowed_image_file(media_file) or allowed_video_file(media_file)),
         "【上传媒体失败】媒体文件不合规", 400),
        (media_file and existing_media, f"【上传媒体失败】媒体 {file_name} 已存在，请重新上传", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 保存文件到指定目录（返回相对路径）
    file_path = handle_file_upload(media_file, 'medias')

    # 获取文件类型（文件后缀）
    file_type = file_name.rsplit('.', 1)[1].lower()

    # 获取文件绝对路径
    abs_path = os.path.join(current_app.root_path, file_path)

    # 获取媒体大小、分辨率、帧数
    file_size, resolution_width, resolution_height, frame_count = get_media_info(abs_path)

    new_media = Media(
        media_name=file_name,
        media_path=file_path,
        description=description,
        file_size=file_size,
        file_type=file_type,
        resolution_width=resolution_width,
        resolution_height=resolution_height,
        frame_count=frame_count,
        owner_id=current_user_id,
    )
    db.session.add(new_media)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【上传媒体成功】new_media: {new_media}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'new_media': new_media.to_dict(),
    }), 201


@media_routes.route('/detail/<int:media_id>', methods=['GET'])
@jwt_required()
@login_required
def detail(media_id):
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定媒体
    media = Media.query.get(media_id)

    # 校验字段
    validation_checks = [
        (not media, f"【获取媒体 ID={media_id} 详情失败】该媒体不存在", 404),
        (media and media.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【获取媒体 ID={media_id} 详情失败】您非管理员/开发人员，无法查看他人的媒体详情", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'failure_message': message,
            }), code

    return jsonify({
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
        operation_type=OperationType.UPDATE,
        description=f"更新媒体 ID={media_id} 信息",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定媒体
    updated_media = Media.query.get(media_id)

    # 校验字段
    validation_checks = [
        (not updated_media, f"【更新媒体 ID={media_id} 信息失败】该媒体不存在", 404),
        (updated_media and updated_media.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【更新媒体 ID={media_id} 信息失败】您非管理员/开发人员，无法更新他人的媒体信息", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 更新媒体信息
    updated_media.description = description if description else updated_media.description
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(
        f"【更新媒体 ID={media_id} 信息成功】updated_media: {updated_media}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'updated_media': updated_media.to_dict(),
    }), 200


@media_routes.route('/delete/<int:media_id>', methods=['DELETE'])
@jwt_required()
@login_required
def delete_media(media_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.DELETE,
        description=f"删除媒体 ID={media_id}",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定媒体
    deleted_media = Media.query.get(media_id)

    # 校验字段
    validation_checks = [
        (not deleted_media, f"【删除媒体 ID={media_id} 失败】该媒体不存在", 404),
        (deleted_media and deleted_media.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【删除媒体 ID={media_id} 失败】您非管理员/开发人员，无法删除他人的媒体", 403),
        (deleted_media and Detection.query.filter_by(media_id=media_id).first(),
         f"【删除媒体 ID={media_id} 失败】该媒体存在关联的检测分割记录，无法删除", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'operation': new_operation.to_dict(),
            }), code

    # 删除实际文件
    file_abs_path = os.path.join(current_app.root_path, deleted_media.media_path)
    delete_file(file_abs_path)

    # 删除数据库记录
    db.session.delete(deleted_media)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【删除媒体 ID={media_id} 成功】deleted_media: {deleted_media}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'deleted_media': deleted_media.to_dict(),
    }), 200


@media_routes.route('/medias/<int:user_id>', methods=['GET'])
@jwt_required()
@login_required
def user_medias(user_id):
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
        (not user, f"【获取用户 ID={user_id} 媒体失败】该用户不存在", 404),
        (current_user_id != user_id and current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER,
         f"【获取用户 ID={user_id} 媒体失败】您非管理员/开发人员，无法查看他人的媒体", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({
                'failure_message': message,
            }), code

    # 获取指定用户媒体
    query = (
        Media.query
        .filter(Media.owner_id == user_id)
        .join(User, Media.owner_id == User.user_id)
        .add_columns(User.username.label('owner_username'))
        .order_by(Media.media_id.asc())
    )
    page, medias_total, pages = adjust_page_if_needed(query, page, per_page)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    medias = []
    for media, owner_username in paginated.items:
        media_dict = media.to_dict()
        media_dict.update({'owner_username': owner_username})
        medias.append(media_dict)

    current_app.logger.info(
        f"【获取用户 ID={user_id} 媒体成功】total: {medias_total}, per_page: {per_page}, page: {page}, pages: {pages}, medias: {medias}, operator: {current_user}")
    return jsonify({
        'medias': medias,
        'total': medias_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200


@media_routes.route('/medias/all', methods=['GET'])
@jwt_required()
@login_required
def all_medias():
    # 获取分页参数（从请求中获取，默认为第 1 页，每页 5 条记录）
    default_page = request.args.get('page', 1, type=int)
    default_per_page = request.args.get('per_page', 5, type=int)
    page, per_page = get_pagination_params(default_page, default_per_page)

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if current_user.role != UserRole.ADMIN and current_user.role != UserRole.DEVELOPER:
        failure_message = f"【获取所有媒体失败】您非管理员/开发人员，权限不足"
        current_app.logger.warning(failure_message + f', operator: {current_user}')
        return jsonify({
            'failure_message': failure_message,
        }), 403

    # 获取所有媒体
    query = (
        Media.query
        .join(User, Media.owner_id == User.user_id)
        .add_columns(User.username.label('owner_username'))
        .order_by(Media.media_id.asc())
    )
    page, medias_total, pages = adjust_page_if_needed(query, page, per_page)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    medias = []
    for media, owner_username in paginated.items:
        media_dict = media.to_dict()
        media_dict.update({'owner_username': owner_username})
        medias.append(media_dict)

    current_app.logger.info(
        f"【获取所有媒体成功】total: {medias_total}, per_page: {per_page}, page: {page}, pages: {pages}, medias: {medias}, operator: {current_user}")
    return jsonify({
        'medias': medias,
        'total': medias_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200


@media_routes.route('/statistics', methods=['GET'])
@jwt_required()
@login_required
def statistics():
    # 查询媒体总数
    total_medias = Media.query.count()

    # 图片类型（png, jpg, jpeg）
    image_count = Media.query.filter(Media.file_type.in_(['png', 'jpg', 'jpeg'])).count()

    # 视频类型（mp4）
    video_count = Media.query.filter(Media.file_type.in_(['mp4'])).count()

    # 构建返回数据
    medias_statistics = {
        'total': total_medias,
        'image': image_count,
        'video': video_count,
    }

    return jsonify({
        "medias_statistics": medias_statistics,
    }), 200
