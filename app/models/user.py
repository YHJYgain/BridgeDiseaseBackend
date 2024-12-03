from datetime import datetime

from . import db


class User(db.Model):
    """
    用户模型类，表示数据库中的 'user' 表。

    该类存储用户的基本信息，包括用户名、邮箱、密码（加密存储）、角色、状态等。
    用户可以是不同的角色（管理员、开发者、普通用户），并且支持多个外键关联，
    如模型、影像文件、检测分割记录和系统操作等。

    Attributes:
        user_id (int): 用户的唯一标识符（主键）。自动递增。
        username (str): 用户名，必须唯一，不能为空。
        email (str): 用户的邮箱，必须唯一，不能为空。
        password (str): 用户的密码，经过加密存储，不能为空。
        first_name (str): 用户的名字（可选）。
        last_name (str): 用户的姓氏（可选）。
        role (str): 用户的角色，使用枚举类型（'admin', 'developer', 'user'），默认是 'user'。
        avatar_path (str): 用户头像的存储路径（可选）。
        phone (str): 用户的手机号，必须唯一（可选）。
        last_login (datetime): 用户最后一次登录的时间（可选）。
        status (str): 用户的状态，使用枚举类型（'active', 'inactive', 'banned'），默认是 'active'。
        created_at (datetime): 用户记录的创建时间，自动生成。
        updated_at (datetime): 用户记录的最后更新时间，自动更新。

    Relationships:
        models (Model): 一个用户可以拥有多个模型（反向关系，表示用户的模型）。
        medias (Media): 一个用户可以拥有多个影像文件（反向关系，表示用户的媒体文件）。
        detections (Detection): 一个用户可以有多个检测分割记录（反向关系，表示用户的检测任务）。
        operations (Operation): 一个用户可以执行多个操作（反向关系，表示用户的操作记录）。
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
    # 反向关系：一个用户可以有多个操作记录
    operations = db.relationship('Operation', backref='owner', lazy=True)
