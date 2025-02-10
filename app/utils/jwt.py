from flask_jwt_extended import JWTManager


def init_jwt(app):
    jwt = JWTManager(app)

    # 处理 refresh token 过期，强制用户登出
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        # 延迟导入，避免循环导入
        from app.routes import logout

        # 模拟调用登出接口
        with app.test_request_context():
            return logout()

    return jwt
