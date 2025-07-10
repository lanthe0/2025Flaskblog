from waitress import serve
from app import create_app, db
from app.models import User
from flask_login import current_user
import socket
import sys

def get_network_info():
    """获取网络信息并打印"""
    try:
        hostname = socket.gethostname()
        print(f"\n=== 系统主机名: {hostname} ===")
        
        # 获取IPv4地址
        ipv4_addrs = [addr[4][0] for addr in socket.getaddrinfo(hostname, None, socket.AF_INET)]
        print(f"\nIPv4地址: {ipv4_addrs or '无'}")

        # 获取IPv6地址
        ipv6_addrs = [addr[4][0] for addr in socket.getaddrinfo(hostname, None, socket.AF_INET6)
                     if not addr[4][0].startswith('fe80::')]
        print(f"全局IPv6地址: {ipv6_addrs or '无'}")

        return ipv4_addrs, ipv6_addrs
    except Exception as e:
        print(f"\n获取网络信息出错: {e}")
        return [], []

def start_server():
    """启动服务器"""
    app = create_app()
    
    # 添加上下文处理器
    @app.context_processor
    def inject_user():
        """注入用户信息到模板上下文"""
        return dict(current_user=current_user)
    
    port = 5000
    
    print("\n=== 正在启动Flask服务器 ===")
    print("Waitress服务器初始化中...")
    
    # 初始化数据库
    with app.app_context():
        db.create_all()
    
    # 显式绑定到IPv6地址
    serve(app, host='::', port=port)
    
    # 这行代码只有在服务器停止后才会执行
    print("服务器已停止")

if __name__ == '__main__':
    # 显示网络信息
    ipv4, ipv6 = get_network_info()
    
    # 打印访问方式
    print("\n=== 服务器启动后可通过以下方式访问 ===")
    print(f" - IPv4本地: http://localhost:5000")
    if ipv6:
        print(f" - IPv6网络: http://[{ipv6[0]}]:5000")
    
    # 启动服务器
    print("\n=== 服务器日志 ===")
    start_server()
