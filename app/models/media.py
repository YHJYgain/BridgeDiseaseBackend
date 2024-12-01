from datetime import datetime

from . import db


class Media(db.Model):
    __tablename__ = 'media'

    media_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 媒体记录 ID
    file_name = db.Column(db.String(255), nullable=False)  # 文件名
    file_path = db.Column(db.String(255), nullable=False)  # 文件路径
    description = db.Column(db.Text)  # 描述
    file_size = db.Column(db.Integer)  # 文件大小
    file_type = db.Column(db.String(50))  # 文件类型（图片或视频）
    resolution_width = db.Column(db.Integer)  # 分辨率宽度
    resolution_height = db.Column(db.Integer)  # 分辨率高度
    status = db.Column(db.Enum('pending', 'processed', 'deleted', name='media_status'),
                       default='pending', nullable=False)  # 文件状态
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)  # 上传时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 所属用户 ID，外键

    # 设置与 User 表的关系
    owner = db.relationship('User', backref=db.backref('medias', lazy=True))
