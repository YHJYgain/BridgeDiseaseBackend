from enum import Enum


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = 'admin'  # 管理员
    DEVELOPER = 'developer'  # 开发者
    USER = 'user'  # 普通用户

    @classmethod
    def list(cls):
        """返回所有用户角色"""
        return [item.value for item in cls]


class UserStatus(Enum):
    """用户状态枚举"""
    ACTIVE = 'active'  # 在线
    INACTIVE = 'inactive'  # 离线
    BANNED = 'banned'  # 封禁
    DELETED = 'deleted'  # 注销

    @classmethod
    def list(cls):
        """返回所有用户状态"""
        return [item.value for item in cls]


class DiseaseGrade(Enum):
    """病害评估等级枚举"""
    MILD = 'mild'  # 轻度
    MODERATE = 'moderate'  # 中度
    SEVERE = 'severe'  # 重度
    CRITICAL = 'critical'  # 严重

    @classmethod
    def list(cls):
        """返回所有病害等级"""
        return [item.value for item in cls]


class TaskStatus(Enum):
    """检测任务状态枚举"""
    PENDING = 'pending'  # 待处理
    IN_PROGRESS = 'in_progress'  # 检测中
    COMPLETED = 'completed'  # 已完成
    FAILED = 'failed'  # 检测失败

    @classmethod
    def list(cls):
        """返回所有任务状态"""
        return [item.value for item in cls]


class OperationType(Enum):
    """操作类型枚举"""
    AUTHENTICATE = 'authenticate'  # 鉴权
    CREATE = 'create'  # 创建
    READ = 'read'  # 读取
    UPDATE = 'update'  # 更新
    DELETE = 'delete'  # 删除
    EXECUTE = 'execute'  # 执行任务
    MANAGE = 'manage'  # 管理操作

    @classmethod
    def list(cls):
        """获取所有操作类型的列表"""
        return [item.value for item in cls]


class OperationStatus(Enum):
    """操作状态枚举"""
    SUCCESS = 'success'  # 操作成功
    FAILURE = 'failure'  # 操作失败

    @classmethod
    def list(cls):
        """获取所有操作状态的列表"""
        return [item.value for item in cls]
