from datetime import datetime

from . import db


class User(db.Model):
    __tablename__ = 'user'  # 表名

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 用户ID
    username = db.Column(db.String(255), unique=True, nullable=False)  # 用户名，唯一
    email = db.Column(db.String(255), unique=True, nullable=False)  # 用户邮箱，唯一
    password = db.Column(db.String(255), nullable=False)  # 加密后的密码
    first_name = db.Column(db.String(100))  # 用户的名字
    last_name = db.Column(db.String(100))  # 用户的姓氏
    role = db.Column(db.Enum('admin', 'developer', 'user', name='user_roles'), default='user', nullable=False)  # 用户角色
    avatar_path = db.Column(db.String(255))  # 头像路径
    phone = db.Column(db.String(20))  # 用户手机号
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 用户创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 最后更新时间
    last_login = db.Column(db.DateTime)  # 最后登录时间
    status = db.Column(db.Enum('active', 'inactive', 'banned', name='user_status'), default='active',
                       nullable=False)  # 用户状态
