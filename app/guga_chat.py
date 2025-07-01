from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from . import db  # 修改为相对导入
from .models import User, Conversation, Message, UserConversation  # 修改为相对导入
import requests

# 检查requests是否可用
try:
    import requests
except ImportError:
    raise ImportError("requests包未安装，请运行: pip install requests")

bp = Blueprint('guga_chat', __name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

@bp.route('/chat')
@login_required
def chat():
    # 获取用户最新会话或创建新会话
    conversation = current_user.conversations.order_by(Conversation.updated_at.desc()).first()
    
    if not conversation:
        # 创建新会话
        conversation = Conversation(
            title=f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            participants=[current_user]
        )
        db.session.add(conversation)
        db.session.commit()
        
        # 添加关联关系
        user_conversation = UserConversation(
            user_id=current_user.id,
            conversation_id=conversation.id
        )
        db.session.add(user_conversation)
        db.session.commit()
    
    return render_template('guga/chat.html', conversation=conversation)

# ... (其余代码保持不变) ...
