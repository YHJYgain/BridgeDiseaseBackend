from datetime import datetime

from . import db


class Media(db.Model):
    """
    影像模型类，表示数据库中的 'media' 表。

    该类存储与用户相关联的媒体文件的基本信息，如文件名、路径、文件类型、分辨率等。
    影像文件可以是图片或视频，并关联到检测任务记录。每个文件只能属于一个用户，且可进行状态管理。

    Attributes:
        media_id (int): 媒体文件的唯一标识符（主键）。
        file_name (str): 媒体文件的文件名，不能为空。
        file_path (str): 媒体文件的存储路径，不能为空。
        description (str): 媒体文件的描述信息（可选）。
        file_size (int): 媒体文件的大小（字节）。
        file_type (str): 媒体文件的类型，通常为图片或视频。
        resolution_width (int): 媒体文件的宽度（像素）。
        resolution_height (int): 媒体文件的高度（像素）。
        upload_time (datetime): 媒体文件的上传时间，默认为当前时间。
        owner_id (int): 所属用户的唯一标识符（外键）。

    Relationships:
        owner (User): 一个媒体文件只属于一个用户（反向关系），表示该文件的所有者。
        detections (Detection): 一个媒体文件可以有多个检测分割记录（一个对多关系），表示该文件参与的所有检测任务。
    """
    __tablename__ = 'media'

    media_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 媒体记录 ID
    file_name = db.Column(db.String(255), nullable=False)  # 文件名
    file_path = db.Column(db.String(255), nullable=False)  # 文件路径
    description = db.Column(db.Text)  # 影像描述
    file_size = db.Column(db.Integer)  # 文件大小（字节）
    file_type = db.Column(db.String(50))  # 文件类型（图片或视频）
    resolution_width = db.Column(db.Integer)  # 分辨率宽度
    resolution_height = db.Column(db.Integer)  # 分辨率高度
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)  # 上传时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户 ID（外键）

    # 设置与 User 表的关系：一份影像文件只属于一个用户
    owner = db.relationship('User', backref=db.backref('medias', lazy=True))
