import time
from collections import defaultdict
from functools import wraps

from flask import request, jsonify

from app import Config

RATE_LIMIT_DEFAULT_LIMIT = Config.RATE_LIMIT_DEFAULT_LIMIT
RATE_LIMIT_DEFAULT_PERIOD = Config.RATE_LIMIT_DEFAULT_PERIOD


class RateLimiter:
    """
    API 限流器类，用于限制 API 请求频率。
    支持基于 IP、用户 ID 或 API 端点的限流策略。
    
    Attributes:
        storage (dict): 存储请求记录的字典
        default_limit (int): 默认的请求限制次数
        default_period (int): 默认的时间窗口（s）
    """

    def __init__(self):
        # 使用内存存储请求记录
        # 格式: {key: [(timestamp1, count1), (timestamp2, count2), ...]}
        self.storage = defaultdict(list)
        self.default_limit = RATE_LIMIT_DEFAULT_LIMIT  # 默认每分钟 60 次请求
        self.default_period = RATE_LIMIT_DEFAULT_PERIOD  # 默认时间窗口为 60 s（1 min）

    def _generate_key(self, key_func):
        """
        生成限流的键
        
        Args:
            key_func: 生成键的函数或字符串
            
        Returns:
            str: 限流键
        """
        if callable(key_func):
            return key_func()
        elif key_func == 'ip':
            return request.remote_addr
        elif key_func == 'endpoint':
            return request.endpoint
        else:
            return f"{request.remote_addr}:{request.endpoint}"

    def _clean_old_requests(self, key, period):
        """
        清理过期的请求记录
        
        Args:
            key (str): 限流键
            period (int): 时间窗口（s）
        """
        current_time = time.time()
        self.storage[key] = [(ts, count) for ts, count in self.storage[key]
                             if current_time - ts < period]

    def is_allowed(self, key_func='ip', limit=None, period=None):
        """
        检查请求是否被允许
        
        Args:
            key_func: 生成键的函数或字符串
            limit (int): 时间窗口内允许的最大请求次数
            period (int): 时间窗口（s）
            
        Returns:
            tuple: (是否允许, 剩余可用请求数, 重置时间)
        """
        limit = limit or self.default_limit
        period = period or self.default_period

        key = self._generate_key(key_func)
        self._clean_old_requests(key, period)

        current_time = time.time()
        request_count = sum(count for _, count in self.storage[key])

        # 如果没有记录或者请求数量未达到限制
        if not self.storage[key] or request_count < limit:
            self.storage[key].append((current_time, 1))
            return True, limit - request_count - 1, period

        # 计算重置时间
        oldest_timestamp = min(ts for ts, _ in self.storage[key])
        reset_time = oldest_timestamp + period - current_time

        return False, 0, max(0, reset_time)


# 创建全局限流器实例
rate_limiter = RateLimiter()


def rate_limit(key_func='ip', limit=None, period=None):
    """
    API限流装饰器
    
    Args:
        key_func: 生成限流键的函数或预定义字符串('ip'或'endpoint')
        limit (int): 时间窗口内允许的最大请求次数
        period (int): 时间窗口（s）
        
    Returns:
        function: 装饰器函数
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            allowed, remaining, reset_time = rate_limiter.is_allowed(key_func, limit, period)

            # 设置响应头部，包含限流信息
            response_headers = {
                'X-RateLimit-Limit': str(limit or rate_limiter.default_limit),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(int(reset_time))
            }

            if not allowed:
                error_response = jsonify({
                    'error': 'Too Many Requests',
                    'failure_message': '请求频率超过限制，请稍后再试',
                    'retry_after': int(reset_time)
                })

                # 添加响应头部
                for header, value in response_headers.items():
                    error_response.headers[header] = value

                error_response.status_code = 429
                return error_response

            # 执行原始函数
            response = f(*args, **kwargs)

            # 如果响应是元组 (response, status_code)，则只修改 response 部分
            if isinstance(response, tuple) and len(response) >= 1:
                response_obj = response[0]
                if hasattr(response_obj, 'headers'):
                    for header, value in response_headers.items():
                        response_obj.headers[header] = value
                return response

            # 如果响应是直接的响应对象
            if hasattr(response, 'headers'):
                for header, value in response_headers.items():
                    response.headers[header] = value

            return response

        return decorated_function

    return decorator


def user_rate_limit(limit=None, period=None):
    """
    基于用户ID的限流装饰器，需要在JWT认证之后使用
    
    Args:
        limit (int): 时间窗口内允许的最大请求次数
        period (int): 时间窗口（秒）
        
    Returns:
        function: 装饰器函数
    """
    from flask_jwt_extended import get_jwt_identity

    def get_user_key():
        try:
            user_id = get_jwt_identity()
            return f"user:{user_id}"
        except Exception:
            # 如果无法获取用户ID，则回退到IP限流
            return request.remote_addr

    # 将函数对象传递给rate_limit，而不是立即调用它
    return rate_limit(get_user_key, limit, period)


def configure_rate_limiting(app):
    """
    配置应用的全局限流设置
    
    Args:
        app: Flask 应用实例
    """
    # 从配置中读取限流设置
    rate_limiter.default_limit = app.config.get('RATE_LIMIT_DEFAULT_LIMIT', 60)
    rate_limiter.default_period = app.config.get('RATE_LIMIT_DEFAULT_PERIOD', 60)

    app.logger.info(f"已配置 API 限流: {rate_limiter.default_limit}次/{rate_limiter.default_period}秒")
