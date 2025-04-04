from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import db


class Model(db.Model):
    """
    模型类，表示数据库中的 'model' 表。

    该类存储不同训练模型的基本信息和性能评估指标。
    包括模型名称、存储路径、训练数据增强方法、计算量、目标检测精度与召回率、分割掩膜性能等。
    模型还包含与用户、检测分割记录的关系，支持对不同模型进行评估和管理。

    Attributes:
        model_id (int): 模型的唯一标识符（主键）。
        model_name (str): 模型名称，必须唯一，不能为空。
        model_path (str): 模型存储路径，必须唯一，不能为空。
        augmentation (str): 使用的数据增强方式。
        disease_category (str): 模型所处理的病害类别。
        layers (int): 模型的层数。
        parameters (int): 模型的参数量。
        GFLOPs (float): 模型的计算量（Giga Floating-Point Operations）。
        box_p (float): 目标检测框的精度。
        box_r (float): 目标检测框的召回率。
        box_mAP50 (float): 目标检测框在 IoU=0.5 时的 mAP（mean Average Precision）。
        box_mAP50_95 (float): 目标检测框在 IoU 从 0.5 到 0.95 的 mAP。
        mask_p (float): 分割掩膜的精度。
        mask_r (float): 分割掩膜的召回率。
        mask_mAP50 (float): 分割掩膜在 IoU=0.5 时的 mAP。
        mask_mAP50_95 (float): 分割掩膜在 IoU 从 0.5 到 0.95 的 mAP。
        f1_score (float): 模型的 F1 分数，综合精度和召回率的性能指标。
        fitness_score (float): 模型的适应度分数，用于评估模型的整体性能。
        created_at (datetime): 模型记录的创建时间，自动生成。
        updated_at (datetime): 模型记录的最后更新时间，自动更新。

    Relationships:
        owner (User): 一个模型只属于一个用户，表示该模型的所有者。
        detections (Detection): 一个模型可以有多个检测分割记录（反向关系，表示该模型应用于的检测任务）。
    """
    __tablename__ = 'model'  # 表名

    model_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 模型 ID
    model_name = db.Column(db.String(255), unique=True, nullable=False)  # 模型名称
    model_path = db.Column(db.String(255), unique=True, nullable=False)  # 存储路径
    augmentation = db.Column(db.String(255), default='原图')  # 数据增强方式
    disease_category = db.Column(db.String(100), nullable=False)  # 病害类别
    layers = db.Column(db.Integer, nullable=False, default=0)  # 层数
    parameters = db.Column(db.Integer, nullable=False, default=0)  # 参数量
    GFLOPs = db.Column(db.Float, nullable=False, default=lambda: round(0.0, 1))  # 计算量
    box_p = db.Column(db.Float, default=lambda: round(0.0, 3))  # 目标检测框的精度
    box_r = db.Column(db.Float, default=lambda: round(0.0, 3))  # 目标检测框的召回率
    box_mAP50 = db.Column(db.Float, default=lambda: round(0.0, 3))  # 目标检测框在 IoU=0.5 时的 mAP
    box_mAP50_95 = db.Column(db.Float, default=lambda: round(0.0, 3))  # 目标检测框在 IoU 从 0.5 到 0.95 的 mAP
    mask_p = db.Column(db.Float, default=lambda: round(0.0, 3))  # 分割掩膜的精度
    mask_r = db.Column(db.Float, default=lambda: round(0.0, 3))  # 分割掩膜的召回率
    mask_mAP50 = db.Column(db.Float, default=lambda: round(0.0, 3))  # 分割掩膜在 IoU=0.5 时的 mAP
    mask_mAP50_95 = db.Column(db.Float, default=lambda: round(0.0, 3))  # 分割掩膜在 IoU 从 0.5 到 0.95 的 mAP
    f1_score = db.Column(db.Float, default=lambda: round(0.0, 5))  # F1 分数
    fitness_score = db.Column(db.Float, default=lambda: round(0.0, 5))  # 适应度分数
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 创建时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")),
                           onupdate=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 最后更新时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户 ID（外键）

    # 设置与 User 表的关系：一个模型只属于一个用户
    owner = db.relationship('User', backref=db.backref('models', lazy=True))

    def __repr__(self):
        return (f"Model(model_id={self.model_id}, "
                f"model_name={self.model_name}, "
                f"model_path={self.model_path}, "
                f"augmentation={self.augmentation}, "
                f"disease_category={self.disease_category}, "
                f"layers={self.layers}, "
                f"parameters={self.parameters}, "
                f"GFLOPs={self.GFLOPs}, "
                f"box_p={self.box_p}, "
                f"box_r={self.box_r}, "
                f"box_mAP50={self.box_mAP50}, "
                f"box_mAP50_95={self.box_mAP50_95}, "
                f"mask_p={self.mask_p}, "
                f"mask_r={self.mask_r}, "
                f"mask_mAP50={self.mask_mAP50}, "
                f"mask_mAP50_95={self.mask_mAP50_95}, "
                f"f1_score={self.f1_score}, "
                f"fitness_score={self.fitness_score}, "
                f"created_at={self.created_at}, "
                f"updated_at={self.updated_at}, "
                f"owner_id={self.owner_id})")

    def to_dict(self):
        """
        将 Model 实例转化为字典。
        """
        return {
            'model_id': self.model_id,
            'model_name': self.model_name,
            'model_path': self.model_path,
            'augmentation': self.augmentation,
            'disease_category': self.disease_category,
            'layers': self.layers,
            'parameters': self.parameters,
            'GFLOPs': self.GFLOPs,
            'box_p': self.box_p,
            'box_r': self.box_r,
            'box_mAP50': self.box_mAP50,
            'box_mAP50_95': self.box_mAP50_95,
            'mask_p': self.mask_p,
            'mask_r': self.mask_r,
            'mask_mAP50': self.mask_mAP50,
            'mask_mAP50_95': self.mask_mAP50_95,
            'f1_score': self.f1_score,
            'fitness_score': self.fitness_score,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'owner_id': self.owner_id
        }
