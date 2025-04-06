import os
import time

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.constants import OperationType, UserRole
from app.decorators import login_required
from app.models import Operation, Model, db, User, Detection
from app.routes import model_routes
from app.utils import handle_operation_failure, allowed_model_file, handle_file_upload, handle_operation_success, \
    adjust_page_if_needed, get_pagination_params, delete_file


@model_routes.route('/upload', methods=['POST'])
@jwt_required()
@login_required
def upload():
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    model_file = request.files.get('model_file')
    disease_category = request.form.get('disease_category')
    augmentation = request.form.get('augmentation', '原图')
    layers = int(request.form.get('layers'))
    parameters = int(request.form.get('parameters'))
    GFLOPs = float(request.form.get('GFLOPs'))
    box_p = float(request.form.get('box_p', 0.0))
    box_r = float(request.form.get('box_r', 0.0))
    box_mAP50 = float(request.form.get('box_mAP50', 0.0))
    box_mAP50_95 = float(request.form.get('box_mAP50_95', 0.0))
    mask_p = float(request.form.get('mask_p', 0.0))
    mask_r = float(request.form.get('mask_r', 0.0))
    mask_mAP50 = float(request.form.get('mask_mAP50', 0.0))
    mask_mAP50_95 = float(request.form.get('mask_mAP50_95', 0.0))
    f1_score = float(request.form.get('f1_score', 0.0))
    fitness_score = float(request.form.get('fitness_score', 0.0))

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.CREATE,
        description="上传模型",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 先获取文件名
    file_name = secure_filename(model_file.filename) if model_file else None

    # 检查文件名是否已存在
    existing_model = Model.query.filter_by(model_name=file_name).first() if file_name else None

    # 校验字段
    validation_checks = [
        (model_file and not allowed_model_file(model_file), "【上传模型失败】模型文件不合规", 400),
        (current_user.role != UserRole.DEVELOPER, f"【上传模型失败】当前登录用户非开发人员，权限不足", 403),
        (model_file and existing_model, f"【上传模型失败】模型 {file_name} 已存在，请重新上传", 400),
        (not disease_category or not layers or not parameters or not GFLOPs,
         "【上传模型失败】模型病害类别、层数、参数量或计算量为空", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'operation': new_operation.to_dict()}), code

    # 保存文件到指定目录（返回相对路径）
    file_path = handle_file_upload(model_file, 'models')

    new_model = Model(
        model_name=file_name,
        model_path=file_path,
        disease_category=disease_category,
        augmentation=augmentation,
        layers=layers,
        parameters=parameters,
        GFLOPs=GFLOPs,
        box_p=box_p,
        box_r=box_r,
        box_mAP50=box_mAP50,
        box_mAP50_95=box_mAP50_95,
        mask_p=mask_p,
        mask_r=mask_r,
        mask_mAP50=mask_mAP50,
        mask_mAP50_95=mask_mAP50_95,
        f1_score=f1_score,
        fitness_score=fitness_score,
        owner_id=current_user_id,
    )
    db.session.add(new_model)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【上传模型成功】new_model: {new_model}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'new_model': new_model.to_dict(),
    }), 201


@model_routes.route('/detail/<int:model_id>', methods=['GET'])
@jwt_required()
@login_required
def model_detail(model_id):
    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定模型文件
    model = Model.query.get(model_id)

    # 校验字段
    validation_checks = [
        (not model, f"【获取模型 ID={model_id} 详情失败】该模型不存在", 404),
    ]
    for condition, message, code in validation_checks:
        if condition:
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'failure_message': message}), code

    return jsonify({
        'model': model.to_dict(),
    }), 200


@model_routes.route('/update/<int:model_id>', methods=['PUT'])
@jwt_required()
@login_required
def update(model_id):
    start_time = time.time()  # 记录操作开始时间

    # 获取请求中的表单数据
    disease_category = request.form.get('disease_category')
    augmentation = request.form.get('augmentation', '原图')
    layers = int(request.form.get('layers'))
    parameters = int(request.form.get('parameters'))
    GFLOPs = float(request.form.get('GFLOPs'))
    box_p = float(request.form.get('box_p', 0.0))
    box_r = float(request.form.get('box_r', 0.0))
    box_mAP50 = float(request.form.get('box_mAP50', 0.0))
    box_mAP50_95 = float(request.form.get('box_mAP50_95', 0.0))
    mask_p = float(request.form.get('mask_p', 0.0))
    mask_r = float(request.form.get('mask_r', 0.0))
    mask_mAP50 = float(request.form.get('mask_mAP50', 0.0))
    mask_mAP50_95 = float(request.form.get('mask_mAP50_95', 0.0))
    f1_score = float(request.form.get('f1_score', 0.0))
    fitness_score = float(request.form.get('fitness_score', 0.0))

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.UPDATE,
        description=f"更新模型 ID={model_id} 信息",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户的身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定模型文件
    updated_model = Model.query.get(model_id)

    # 校验字段
    validation_checks = [
        (not updated_model, f"【更新模型 ID={model_id} 信息失败】该模型不存在", 404),
        (updated_model and updated_model.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【更新模型 ID={model_id} 信息失败】当前登录用户非管理员/开发人员，权限不足", 403),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'operation': new_operation.to_dict()}), code

    # 更新模型文件信息
    updated_model.disease_category = disease_category
    updated_model.augmentation = augmentation
    updated_model.layers = layers
    updated_model.parameters = parameters
    updated_model.GFLOPs = GFLOPs
    updated_model.box_p = box_p
    updated_model.box_r = box_r
    updated_model.box_mAP50 = box_mAP50
    updated_model.box_mAP50_95 = box_mAP50_95
    updated_model.mask_p = mask_p
    updated_model.mask_r = mask_r
    updated_model.mask_mAP50 = mask_mAP50
    updated_model.mask_mAP50_95 = mask_mAP50_95
    updated_model.f1_score = f1_score
    updated_model.fitness_score = fitness_score
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)
    current_app.logger.info(
        f"【更新模型 ID={model_id} 信息成功】updated_model: {updated_model.to_dict()}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'updated_model': updated_model.to_dict(),
    }), 200


@model_routes.route('/delete/<int:model_id>', methods=['DELETE'])
@jwt_required()
@login_required
def delete(model_id):
    start_time = time.time()  # 记录操作开始时间

    # 创建一个新的操作记录
    new_operation = Operation(
        operation_type=OperationType.DELETE,
        description=f"删除模型 ID={model_id}",
        ip_address=request.remote_addr,
        device_info=request.user_agent.string,
    )

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取指定模型
    model = Model.query.get(model_id)

    # 校验字段
    validation_checks = [
        (not model, f"【删除模型 ID={model_id} 失败】该模型不存在", 404),
        (model and model.owner_id != current_user_id and current_user.role != UserRole.ADMIN
         and current_user.role != UserRole.DEVELOPER,
         f"【删除模型 ID={model_id} 失败】当前登录用户非管理员/开发人员，权限不足", 403),
        (model and Detection.query.filter_by(model_id=model_id).first(),
         f"【删除模型 ID={model_id} 失败】该模型存在关联的检测分割记录，无法删除", 400),
    ]
    for condition, message, code in validation_checks:
        if condition:
            new_operation = handle_operation_failure(new_operation, start_time, message, current_user_id)
            current_app.logger.warning(message + f', operator: {current_user}')
            return jsonify({'operation': new_operation.to_dict()}), code

    # 删除实际文件
    file_abs_path = os.path.join(current_app.root_path, model.model_path)
    delete_file(file_abs_path)

    # 删除数据库记录
    db.session.delete(model)
    db.session.commit()

    # 记录操作
    new_operation = handle_operation_success(new_operation, start_time, current_user_id)

    current_app.logger.info(f"【删除模型 ID={model_id} 成功】deleted_model: {model.to_dict()}, operator: {current_user}")
    return jsonify({
        'operation': new_operation.to_dict(),
        'deleted_model': model.to_dict(),
    }), 200


@model_routes.route('/models/all', methods=['GET'])
@jwt_required()
@login_required
def all_models():
    # 获取分页参数（从请求中获取，默认为第 1 页，每页 5 条记录）
    default_page = request.args.get('page', 1, type=int)
    default_per_page = request.args.get('per_page', 5, type=int)
    page, per_page = get_pagination_params(default_page, default_per_page)

    # 获取当前用户身份（使用 access token）
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # 获取所有模型文件
    query = Model.query
    page, models_total, pages = adjust_page_if_needed(query, page, per_page)
    models = query.paginate(page=page, per_page=per_page, error_out=False)

    current_app.logger.info(
        f"【获取所有模型成功】total: {models_total}, per_page: {per_page}, page: {page}, pages: {pages}, models: {[model.to_dict() for model in models]}, operator: {current_user}")
    return jsonify({
        'models': [model.to_dict() for model in models],
        'total': models_total,
        'per_page': per_page,
        'page': page,
        'pages': pages,
    }), 200


@model_routes.route('/statistics', methods=['GET'])
@jwt_required()
@login_required
def statistics():
    # 查询模型总数
    total_models = Model.query.count()

    # 构建统计数据
    models_statistics = {
        'total': total_models
    }

    return jsonify({
        "models_statistics": models_statistics,
    }), 200
