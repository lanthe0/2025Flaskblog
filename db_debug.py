#!/usr/bin/env python3
"""
数据库调试脚本 - 使用项目现有配置检查聊天记录
"""

import sys
from app import create_app, db
from app.models import Message, Conversation, User

def print_db_info():
    """打印数据库连接信息"""
    app = create_app()
    with app.app_context():
        print("\n=== 数据库连接信息 ===")
        print(f"数据库URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"当前数据库: {db.engine.url.database}")
        
        # 测试连接
        try:
            db.engine.connect()
            print("状态: 连接成功")
        except Exception as e:
            print(f"状态: 连接失败 - {str(e)}")
            return False
        return True

def display_messages(limit=10, page=1):
    """显示分页的聊天记录"""
    app = create_app()
    with app.app_context():
        print(f"\n=== 聊天记录 (第{page}页，每页{limit}条) ===")
        
        # 获取消息及关联的会话和用户信息（使用outerjoin包含AI消息）
        messages = db.session.query(
            Message, Conversation, User
        ).join(
            Conversation, Message.conversation_id == Conversation.id
        ).outerjoin(
            User, Message.user_id == User.id
        ).order_by(
            Message.created_at.desc()
        ).paginate(page=page, per_page=limit, error_out=False)
        
        if not messages.items:
            print("没有找到聊天记录")
            return
        
        for msg, conv, user in messages.items:
            print(f"\n[消息ID: {msg.id}]")
            print(f"会话: {conv.title} (ID: {conv.id})")
            print(f"用户: {user.username if user else 'AI'} (ID: {user.id if user else 'N/A'})")
            print(f"时间: {msg.created_at}")
            print(f"角色: {msg.role} (类型: {'用户' if msg.role == 'user' else 'AI'})")
            print(f"内容: {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
            print("-" * 80)
        
        print(f"\n总记录数: {messages.total}")
        print(f"当前页: {messages.page}/{messages.pages}")

if __name__ == '__main__':
    if not print_db_info():
        sys.exit(1)
        
    try:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        display_messages(limit, page)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        print("\n使用方法:")
        print("python db_debug.py [每页条数] [页码]")
        print("示例:")
        print("python db_debug.py 20 1  # 查看第1页，每页20条")
        sys.exit(1)
