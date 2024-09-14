import os
import secrets


class Config:
    # Flask 密钥，用于签名 cookies 和其他需要加密的操作
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex())

    # SQLAlchemy 数据库 URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///bridgedisease.db')

    # 禁用 SQLAlchemy 的修改追踪
    SQLALCHEMY_TRACK_MODIFICATIONS = False
