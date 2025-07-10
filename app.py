from app import create_app, db
from app.models import User
from flask_login import current_user

app = create_app()

# 创建上下文处理器，确保current_user在模板中可用
@app.context_processor
def inject_user():
    """注入用户信息到模板上下文"""
    return dict(current_user=current_user)

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表
        db.create_all()
    
    import socket
    
    # 获取网络信息
    hostname = socket.gethostname()
    ipv6_addrs = [str(addr[4][0]) for addr in socket.getaddrinfo(hostname, None, socket.AF_INET6)
                 if not str(addr[4][0]).startswith('fe80::')]
    
    print("\n=== 服务器启动后可通过以下方式访问 ===")
    print(f" - IPv4本地: http://localhost:5000")
    if ipv6_addrs:
        print(f" - IPv6网络: http://[{ipv6_addrs[0]}]:5000")
    
    # 开发服务器配置(双栈IPv4/IPv6)
    app.run(
        host='0.0.0.0',  # 同时监听IPv4和IPv6
        port=5000,
        debug=True,
        use_reloader=True
    )
