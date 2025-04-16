from datetime import datetime
from zoneinfo import ZoneInfo

from app.constants import DiseaseGrade, TaskStatus
from app.models import db


class Detection(db.Model):
    """
    检测分割记录类，表示数据库中的 'detection' 表。

    每一条记录对应一次检测任务，包含检测分割结果图像，
    以及与检测分割任务相关的各类统计信息（如病害数量、面积、形状复杂度等）及评估描述。

    Attributes:
        detection_id (int): 检测记录的唯一标识符（主键）。
        result_path (str): 检测和分割的结果存储路径。
        disease_count (int): 病害的数量。
        disease_perimeter (float): 病害的周长。
        disease_area (float): 病害的面积。
        shape_complexity (float): 病害形状的复杂度。
        texture_roughness (float): 病害的纹理粗糙度。
        crack_width (float): 裂缝的宽度（适用于裂缝病害）。
        avg_hue (float): 病害的平均色调（适用于锈蚀等病害）。
        disease_severity_score (float): 病害严重性得分。
        disease_grade (str): 病害的评估等级，使用枚举类型（'mild', 'moderate', 'severe', 'critical'）。
        disease_description (str): 病害评估的描述信息。
        detection_duration (float): 检测分割耗时（ms）。
        avg_frame_detection_duration (float): 帧平均检测分割耗时（ms）。
        status (str): 任务状态，使用枚举类型（'pending', 'in_progress', 'completed', 'failed'）。
        detection_at (datetime): 检测任务执行的时间，自动生成。
        updated_at (datetime): 记录最后更新时间，自动更新。
        owner_id (int): 执行该检测任务的用户 ID（外键）。
        model_id (int): 使用的模型 ID（外键）。
        media_id (int): 使用的媒体文件 ID（外键）。

    Relationships:
        owner (User): 每条检测记录关联一个用户，表示该任务由哪个用户执行。
        model (Model): 每条记录关联一个模型，表示该任务使用的模型。
        media (Media): 每条记录关联一个媒体文件，表示该任务使用的媒体文件。
    """
    __tablename__ = 'detection'

    detection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 检测分割记录 ID
    result_path = db.Column(db.String(255))  # 检测分割结果路径
    disease_count = db.Column(db.Integer, default=0)  # 病害数量
    disease_perimeter = db.Column(db.Float, default=0.0)  # 病害周长
    disease_area = db.Column(db.Float, default=0.0)  # 病害面积
    shape_complexity = db.Column(db.Float, default=0.0)  # 形状复杂度
    texture_roughness = db.Column(db.Float, default=0.0)  # 纹理粗糙度
    crack_width = db.Column(db.Float, default=0.0)  # 裂缝宽度（适用裂缝等）
    avg_hue = db.Column(db.Float, default=0.0)  # 平均色调（适用锈蚀等）
    disease_severity_score = db.Column(db.Float, default=0.0, nullable=False)  # 病害严重性得分
    disease_grade = db.Column(db.Enum(DiseaseGrade), default=DiseaseGrade.MILD, nullable=False)  # 病害评估等级
    disease_description = db.Column(db.Text, default='暂无描述')  # 病害评估描述
    detection_duration = db.Column(db.Float, default=0.0)  # 检测分割耗时（ms）
    avg_frame_detection_duration = db.Column(db.Float, default=0.0)  # 帧平均检测分割耗时（ms）
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)  # 任务状态
    detection_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 检测时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")),
                           onupdate=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 最后更新时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户 ID（外键）
    model_id = db.Column(db.Integer, db.ForeignKey('model.model_id'), nullable=False)  # 使用模型 ID（外键）
    media_id = db.Column(db.Integer, db.ForeignKey('media.media_id'), nullable=False)  # 使用媒体 ID（外键）

    # 设置与 User 表的关系：一次检测分割只属于一个用户
    owner = db.relationship('User', backref=db.backref('detections', lazy=True))
    # 设置与 Model 表的关系：一次检测分割只使用一个模型
    model = db.relationship('Model', backref=db.backref('detections', lazy=True))
    # 设置与 Media 表的关系：一次检测分割只使用一份媒体文件
    media = db.relationship('Media', backref=db.backref('detections', lazy=True))

    def __repr__(self):
        return (f"Detection(detection_id={self.detection_id}, "
                f"result_path={self.result_path}, "
                f"disease_count={self.disease_count}, "
                f"disease_perimeter={self.disease_perimeter}, "
                f"disease_area={self.disease_area}, "
                f"shape_complexity={self.shape_complexity}, "
                f"texture_roughness={self.texture_roughness}, "
                f"crack_width={self.crack_width}, "
                f"avg_hue={self.avg_hue}, "
                f"disease_severity_score={self.disease_severity_score}, "
                f"disease_grade={self.disease_grade.name}, "
                f"disease_description={self.disease_description}, "
                f"detection_duration={self.detection_duration}, "
                f"avg_frame_detection_duration={self.avg_frame_detection_duration}, "
                f"status={self.status.name}, "
                f"detection_at={self.detection_at}, "
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
            'result_path': self.result_path,
            'disease_count': self.disease_count,
            'disease_perimeter': self.disease_perimeter,
            'disease_area': self.disease_area,
            'shape_complexity': self.shape_complexity,
            'texture_roughness': self.texture_roughness,
            'crack_width': self.crack_width,
            'avg_hue': self.avg_hue,
            'disease_severity_score': self.disease_severity_score,
            'disease_grade': self.disease_grade.name,
            'disease_description': self.disease_description,
            'detection_duration': self.detection_duration,
            'avg_frame_detection_duration': self.avg_frame_detection_duration,
            'status': self.status.name,
            'detection_at': self.detection_at,
            'updated_at': self.updated_at,
            'owner_id': self.owner_id,
            'model_id': self.model_id,
            'media_id': self.media_id
        }
