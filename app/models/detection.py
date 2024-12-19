from datetime import datetime
from zoneinfo import ZoneInfo

from . import db
from ..constants import DiseaseGrade, TaskStatus


class Detection(db.Model):
    """
    检测分割记录类，表示数据库中的 'detection' 表。

    每一条记录对应一次检测任务，包含检测及分割的原始结果，处理后的结果图像，
    以及与检测任务相关的各类统计信息（如病害数量、面积、形状复杂度等）及评估描述。

    Attributes:
        detection_id (int): 检测记录的唯一标识符（主键）。
        raw_detection_result (str): 检测原始结果，以 JSON 格式存储。
        raw_segmentation_result (str): 分割原始结果，以 JSON 格式存储。
        result_image_path (str): 检测和分割的结果图像存储路径。
        cropped_image_path (str): 裁剪后结果图像存储路径。
        disease_count (int): 病害的数量。
        disease_perimeter (float): 病害的周长。
        disease_area (float): 病害的面积。
        shape_complexity (float): 病害形状的复杂度。
        texture_roughness (float): 病害的纹理粗糙度。
        crack_width (float): 裂缝的宽度（适用于裂缝病害）。
        avg_hue (float): 病害的平均色调（适用于锈蚀等病害）。
        disease_grade (str): 病害的评估等级，使用枚举类型（'mild', 'moderate', 'severe', 'critical'）。
        disease_description (str): 病害评估的描述信息。
        detection_time (datetime): 检测任务执行的时间。
        status (str): 任务状态，使用枚举类型（'pending', 'in_progress', 'completed', 'failed'）。
        created_at (datetime): 记录创建时间，自动生成。
        updated_at (datetime): 记录最后更新时间，自动更新。
        owner_id (int): 执行该检测任务的用户 ID（外键）。
        model_id (int): 使用的模型 ID（外键）。
        media_id (int): 使用的影像文件 ID（外键）。

    Relationships:
        owner (User): 每条检测记录关联一个用户，表示该任务由哪个用户执行。
        model (Model): 每条记录关联一个模型，表示该任务使用的模型。
        media (Media): 每条记录关联一个影像文件，表示该任务使用的影像。
    """
    __tablename__ = 'detection'

    detection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 检测分割记录 ID
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
    disease_grade = db.Column(db.Enum(DiseaseGrade), default=DiseaseGrade.MILD, nullable=False)  # 病害评估等级
    disease_description = db.Column(db.Text)  # 病害评估描述
    detection_time = db.Column(db.DateTime)  # 检测时间
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)  # 任务状态
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 创建时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")),
                           onupdate=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 最后更新时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户 ID（外键）
    model_id = db.Column(db.Integer, db.ForeignKey('model.model_id'), nullable=False)  # 使用模型 ID（外键）
    media_id = db.Column(db.Integer, db.ForeignKey('media.media_id'), nullable=False)  # 使用影像 ID（外键）

    # 设置与 User 表的关系：一次检测分割只属于一个用户
    owner = db.relationship('User', backref=db.backref('detections', lazy=True))
    # 设置与 Model 表的关系：一次检测分割只使用一个模型
    model = db.relationship('Model', backref=db.backref('detections', lazy=True))
    # 设置与 Media 表的关系：一次检测分割只能使用一份影像文件
    media = db.relationship('Media', backref=db.backref('detections', lazy=True))

    def __repr__(self):
        return (f"Detection(detection_id={self.detection_id}, "
                f"result_image_path={self.result_image_path}, "
                f"cropped_image_path={self.cropped_image_path}, "
                f"disease_count={self.disease_count}, "
                f"disease_perimeter={self.disease_perimeter}, "
                f"disease_area={self.disease_area}, "
                f"shape_complexity={self.shape_complexity}, "
                f"texture_roughness={self.texture_roughness}, "
                f"crack_width={self.crack_width}, "
                f"avg_hue={self.avg_hue}, "
                f"disease_grade={self.disease_grade.name}, "
                f"disease_description={self.disease_description}, "
                f"detection_time={self.detection_time}, "
                f"status={self.status.name}, "
                f"created_at={self.created_at}, "
                f"updated_at={self.updated_at}, "
                f"owner_id={self.owner_id}, "
                f"model_id={self.model_id}, "
                f"media_id={self.media_id})")

    def to_dict(self):
        """
        将 Detection 实例转化为字典。
        """
        return {
            'detection_id': self.detection_id,
            'result_image_path': self.result_image_path,
            'cropped_image_path': self.cropped_image_path,
            'disease_count': self.disease_count,
            'disease_perimeter': self.disease_perimeter,
            'disease_area': self.disease_area,
            'shape_complexity': self.shape_complexity,
            'texture_roughness': self.texture_roughness,
            'crack_width': self.crack_width,
            'avg_hue': self.avg_hue,
            'disease_grade': self.disease_grade.name,
            'disease_description': self.disease_description,
            'detection_time': self.detection_time,
            'status': self.status.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'owner_id': self.owner_id,
            'model_id': self.model_id,
            'media_id': self.media_id
        }
