from flask import Blueprint

# 创建蓝图
auth = Blueprint('auth', __name__)

# 导入视图函数
from . import auth as auth_routes
