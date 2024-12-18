from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app, request

from .. import db, Operation


def record_operation(operation_type, description, status, start_time=None, failure_message=None, user_id=None):
    """
    记录操作日志到数据库。

    :param operation_type: 操作类型，如 'create', 'update', 'delete' 等
    :param description: 操作描述
    :param status: 操作状态，'success' 或 'failure'
    :param start_time: 操作开始时间，用于计算操作耗时（秒）
    :param failure_message: 操作失败的消息，若成功则为 None
    :param user_id: 用户 ID, 若为 None 表示不关联用户（仅在注册时可能为 None）
    """
    try:
        # 获取操作结束时间，并计算耗时
        if start_time:
            duration = (datetime.now(ZoneInfo("Asia/Shanghai")) - start_time).total_seconds()
        else:
            duration = None  # 若没有提供 start_time，则 duration 为 None

        # 获取操作的 IP 地址和设备信息
        ip_address = request.remote_addr if request else None
        device_info = request.user_agent.string if request else None

        # 创建操作记录
        operation = Operation(
            operation_type=operation_type,
            description=description,
            duration=duration,
            failure_message=failure_message,
            ip_address=ip_address,
            device_info=device_info,
            status=status,
            created_at=datetime.now(ZoneInfo("Asia/Shanghai")),
            owner_id=user_id,
        )

        # 将操作记录保存到数据库
        db.session.add(operation)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # 如果日志记录失败，记录到 Flask 的日志中
        current_app.logger.error(f"记录操作失败：{str(e)}")
