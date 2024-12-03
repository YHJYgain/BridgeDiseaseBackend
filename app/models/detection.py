from datetime import datetime

from . import db


class Detection(db.Model):
    """
    检测分割记录表，表示数据库中的 'detection' 表。
    存储检测分割任务的状态、结果图像、分析数据及其病害评估信息。
    """
    __tablename__ = 'detection'

    detection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 记录 ID
    raw_detection_result = db.Column(db.Text)  # 检测原始结果（JSON 格式）
    raw_segmentation_result = db.Column(db.Text)  # 分割原始结果（JSON 格式）
    result_image_path = db.Column(db.String(255))  # 检测分割结果图路径
    cropped_image_path = db.Column(db.String(255))  # 裁剪结果图路径
    disease_count = db.Column(db.Integer)  # 病害数量
    disease_perimeter = db.Column(db.Float)  # 病害周长
    disease_area = db.Column(db.Float)  # 病害面积
    shape_complexity = db.Column(db.Float)  # 形状复杂度
    texture_roughness = db.Column(db.Float)  # 纹理粗糙度
    crack_width = db.Column(db.Float)  # 裂缝宽度（适用裂缝等）
    avg_hue = db.Column(db.Float)  # 平均色调（适用锈蚀等）
    disease_grade = db.Column(db.Enum('mild', 'moderate', 'severe', 'critical'), default='mild',
                              nullable=False)  # 病害评估等级
    disease_description = db.Column(db.Text)  # 病害评估描述
    detection_time = db.Column(db.DateTime)  # 检测时间
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'failed', name='task_status'),
                       default='pending', nullable=False)  # 任务状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 最后更新时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户 ID（外键）
    model_id = db.Column(db.Integer, db.ForeignKey('model.model_id'), nullable=False)  # 使用模型 ID（外键）
    media_id = db.Column(db.Integer, db.ForeignKey('media.media_id'), nullable=False)  # 使用影像 ID（外键）

    # 设置与 User 表的关系：一次检测分割只属于一个用户
    owner = db.relationship('User', backref=db.backref('detections', lazy=True))
    # 设置与 Model 表的关系：一次检测分割只使用一个模型
    model = db.relationship('Model', backref=db.backref('detections', lazy=True))
    # 设置与 Media 表的关系：一次检测分割只能使用一份影像文件
    media = db.relationship('Media', backref=db.backref('detections', lazy=True))
