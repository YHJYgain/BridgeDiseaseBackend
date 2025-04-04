from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import db


class Media(db.Model):
    """
    媒体模型类，表示数据库中的 'media' 表。

    该类存储与用户相关联的媒体的基本信息，如文件名、路径、文件类型、分辨率等。
    媒体可以是图片或视频，并关联到用户。每个媒体只能属于一个用户，且可进行状态管理。

    Attributes:
        media_id (int): 媒体的唯一标识符（主键）。
        media_name (str): 媒体名称，必须唯一，不能为空。
        media_path (str): 媒体存储路径，必须唯一，不能为空。
        description (str): 媒体的描述信息（可选）。
        file_size (int): 媒体的大小（字节）。
        file_type (str): 媒体的类型，通常为图片或视频。
        resolution_width (int): 媒体的宽度（像素）。
        resolution_height (int): 媒体的高度（像素）。
        frame_count (int): 媒体的帧数（图片为 1，视频为实际帧数）。
        upload_at (datetime): 媒体的上传时间，默认为当前时间。
        updated_at (datetime): 媒体的最后更新时间，默认为当前时间，并在更新时自动更新。
        owner_id (int): 所属用户的唯一标识符（外键）。

    Relationships:
        owner (User): 一个媒体只属于一个用户（反向关系），表示该媒体的所有者。
        detections (Detection): 一个媒体可以有多个检测分割记录（反向关系，表示该媒体参与的所有检测任务）。
    """
    __tablename__ = 'media'

    media_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 媒体 ID
    media_name = db.Column(db.String(255), unique=True, nullable=False)  # 媒体名称
    media_path = db.Column(db.String(255), unique=True, nullable=False)  # 媒体存储路径
    description = db.Column(db.Text, default='暂无描述')  # 媒体描述
    file_size = db.Column(db.Float, default=0.0)  # 文件大小（KB）
    file_type = db.Column(db.String(50), nullable=False)  # 文件类型（图片或视频）
    resolution_width = db.Column(db.Integer, default=0)  # 分辨率宽度
    resolution_height = db.Column(db.Integer, default=0)  # 分辨率高度
    frame_count = db.Column(db.Integer, default=1)  # 帧数（图片为 1，视频为实际帧数）
    upload_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 上传时间
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")),
                           onupdate=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))  # 最后更新时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户 ID（外键）

    # 设置与 User 表的关系：一份媒体文件只属于一个用户
    owner = db.relationship('User', backref=db.backref('medias', lazy=True))

    def __repr__(self):
        return (f"Media(media_id={self.media_id}, "
                f"media_name={self.media_name}, "
                f"media_path={self.media_path}, "
                f"description={self.description}, "
                f"file_size={self.file_size}, "
                f"file_type={self.file_type}, "
                f"resolution_width={self.resolution_width}, "
                f"resolution_height={self.resolution_height}, "
                f"frame_count={self.frame_count}, "
                f"upload_at={self.upload_at}, "
                f"updated_at={self.updated_at}, "
                f"owner_id={self.owner_id})")

    def to_dict(self):
        """
        将 Media 实例转化为字典。
        """
        return {
            'media_id': self.media_id,
            'media_name': self.media_name,
            'media_path': self.media_path,
            'description': self.description,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'resolution_width': self.resolution_width,
            'resolution_height': self.resolution_height,
            'frame_count': self.frame_count,
            'upload_at': self.upload_at,
            'updated_at': self.updated_at,
            'owner_id': self.owner_id
        }
