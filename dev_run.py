from flaskr import create_app

app = create_app()

if __name__ == '__main__':
    # 开发服务器配置
    app.run(
        host='::', 
        port=5000,
        debug=True,
        use_reloader=True
    )
