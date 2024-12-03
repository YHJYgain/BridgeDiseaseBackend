from datetime import datetime

from . import db


class OperationLog(db.Model):
    """
    操作日志模型类，表示数据库中的 'operation_log' 表。

    包括操作类型、描述、耗时、状态、用户信息等，用于系统的审计、监控和分析。

    Attributes:
        log_id (int): 操作日志 ID，自动增长的主键。
        operation_type (str): 操作类型，使用枚举定义，如 'authenticate', 'create', 'read', 'update', 'delete' 等。
        operation_description (str): 对操作的详细描述，帮助理解操作的背景和过程。
        operation_duration (float): 操作的持续时间，单位为秒（s）。
        failure_message (str): 当操作失败时，记录失败信息，帮助诊断问题。
        ip_address (str): 用户进行操作时的 IP 地址，记录操作来源的网络地址。
        device_info (str): 用户操作时的设备信息，通常为浏览器类型、操作系统等。
        status (str): 操作状态，表示操作是否成功，使用枚举定义，'success' 或 'failure'。
        created_at (datetime): 操作记录的时间戳，自动记录每条操作的创建时间。
        owner_id (int): 操作执行者的用户 ID，外键关联用户表，标识执行该操作的用户。

    Relationships:
        owner (User): 每条操作日志记录一个用户，表示该操作由哪个用户执行。
    """
    __tablename__ = 'operation_log'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 操作日志 ID
    operation_type = db.Column(
        db.Enum('authenticate', 'create', 'read', 'update', 'delete', 'execute', 'manage', name='operation_types'),
        default='read', nullable=False)  # 操作类型
    operation_description = db.Column(db.Text)  # 操作描述
    operation_duration = db.Column(db.Float)  # 操作耗时（s）
    failure_message = db.Column(db.Text)  # 失败信息
    ip_address = db.Column(db.String(45))  # IP 地址
    device_info = db.Column(db.String(255))  # 设备信息
    status = db.Column(db.Enum('success', 'failure', name='operation_status'), default='success',
                       nullable=False)  # 操作状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 操作时间
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # 用户 ID（外键）

    # 设置与 User 的关系：一个操作日志只属于一个用户
    owner = db.relationship('User', backref=db.backref('operation_logs', lazy=True))
