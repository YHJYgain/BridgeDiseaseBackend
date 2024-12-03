from datetime import datetime

from . import db


class User(db.Model):
    """
    用户模型类，表示数据库中的 'user' 表。
    存储用户的基本信息及其状态。
    """
    __tablename__ = 'user'  # 表名

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 用户 ID
    username = db.Column(db.String(255), unique=True, nullable=False)  # 用户名，唯一
    email = db.Column(db.String(255), unique=True, nullable=False)  # 用户邮箱，唯一
    password = db.Column(db.String(255), nullable=False)  # 密码（加密）
    first_name = db.Column(db.String(100))  # 名字
    last_name = db.Column(db.String(100))  # 姓氏
    role = db.Column(db.Enum('admin', 'developer', 'user', name='user_roles'), default='user', nullable=False)  # 角色
    avatar_path = db.Column(db.String(255))  # 头像路径
    phone = db.Column(db.String(20), unique=True)  # 手机号
    last_login = db.Column(db.DateTime)  # 最后登录时间
    status = db.Column(db.Enum('active', 'inactive', 'banned', name='user_status'), default='active',
                       nullable=False)  # 用户状态（在线、离线、封禁）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 用户创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 最后更新时间

    # 反向关系：一个用户可以有多个模型
    models = db.relationship('Model', backref='owner', lazy=True)
    # 反向关系：一个用户可以有多个影像文件
    medias = db.relationship('Media', backref='owner', lazy=True)
    # 反向关系：一个用户可以有多个检测分割记录
    detections = db.relationship('Detection', backref='owner', lazy=True)
    # 反向关系：一个用户可以有多个操作日志
    operation_logs = db.relationship('OperationLog', backref='owner', lazy=True)
