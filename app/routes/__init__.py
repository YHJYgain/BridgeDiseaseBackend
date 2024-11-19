from flask import Blueprint

# 创建蓝图
user = Blueprint('user', __name__, url_prefix='/user')

# 导入视图函数
from . import user as user_routes
