from app import create_app

app = create_app()

if __name__ == '__main__':
    """
    启动 Flask 应用。当脚本直接执行时，运行 Flask 应用的开发服务器。
    """
    app.run()
