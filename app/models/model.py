from datetime import datetime

from . import db


class Model(db.Model):
    """
    模型类，表示数据库中的 'model' 表。
    存储不同训练模型的基本信息及其性能评估指标。
    """
    __tablename__ = 'model'  # 表名

    model_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 模型 ID
    model_name = db.Column(db.String(255), unique=True, nullable=False)  # 模型名称
    model_path = db.Column(db.String(255), unique=True, nullable=False)  # 存储路径
    augmentation = db.Column(db.String(255))  # 数据增强方式
    disease_category = db.Column(db.String(100))  # 病害类别
    layers = db.Column(db.Integer)  # 层数
    parameters = db.Column(db.Integer)  # 参数量
    GFLOPs = db.Column(db.Float)  # 计算量
    box_p = db.Column(db.Float)  # 目标检测框的精度
    box_r = db.Column(db.Float)  # 目标检测框的召回率
    box_mAP50 = db.Column(db.Float)  # 目标检测框在 IoU=0.5 时的 mAP
    box_mAP50_95 = db.Column(db.Float)  # 目标检测框在 IoU 从 0.5 到 0.95 的 mAP
    mask_p = db.Column(db.Float)  # 分割掩膜的精度
    mask_r = db.Column(db.Float)  # 分割掩膜的召回率
    mask_mAP50 = db.Column(db.Float)  # 分割掩膜在 IoU=0.5 时的 mAP
    mask_mAP50_95 = db.Column(db.Float)  # 分割掩膜在 IoU 从 0.5 到 0.95 的 mAP
    fitness_score = db.Column(db.Float)  # 适应度分数
    f1_score = db.Column(db.Float)  # F1 分数
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 最后更新时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户ID，外键

    # 设置与 User 表的关系
    owner = db.relationship('User', backref=db.backref('models', lazy=True))
