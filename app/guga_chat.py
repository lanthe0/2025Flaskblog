from flask import Blueprint, render_template, request, jsonify, redirect, url_for, Response
from flask_login import login_required, current_user
from datetime import datetime
from . import db
from .models import User, Conversation, Message, UserConversation
from config import Config
import requests
from typing import List, Dict, Optional
from openai import OpenAI

class ChatManager:
    """管理聊天相关功能的类"""
    
    def __init__(self):
        self.config = Config()
        try:
            # 从config.yml读取DeepSeek配置
            config = self.config.MODEL_CONFIG
            self.api_key = config.get('api_key')
            self.model = config.get('model')
            self.base_url = config.get('base_url')
            self.timeout = 30  # 默认超时
            
            if not self.api_key or self.api_key == "your_api_key_here":
                raise ValueError("请配置有效的DeepSeek API密钥")
            
            # 清理base_url格式
            if self.base_url:
                self.base_url = self.base_url.rstrip('/')
                
        except Exception as e:
            print(f"AI服务初始化失败: {str(e)}")
            self.api_key = None
    
    def get_or_create_conversation(self) -> Conversation:
        """获取或创建用户会话"""
        # 确保只获取当前用户的会话
        conversation = db.session.query(Conversation)\
            .join(UserConversation, Conversation.id == UserConversation.conversation_id)\
            .filter(UserConversation.user_id == current_user.id)\
            .order_by(Conversation.updated_at.desc())\
            .first()
        
        if not conversation:
            print(f"为用户 {current_user.id} 创建新会话...")
            conversation = self._create_new_conversation()
        else:
            print(f"找到现有会话 {conversation.id} 属于用户 {current_user.id}")
            
        return conversation
    
    def _create_new_conversation(self) -> Conversation:
        """创建新会话"""
        conversation = Conversation(
            title=f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            user_id=current_user.id
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
        return conversation
    
    def get_conversation_history(self, conversation_id: int, 
                               page: int = 1, per_page: int = 10) -> List[Dict]:
        """获取指定会话的历史消息"""
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at.asc()).paginate(page, per_page, False)
        
        from datetime import timezone
        return [{
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'created_at': msg.created_at.replace(tzinfo=timezone.utc).isoformat()
        } for msg in messages.items]
    
    from flask import stream_with_context

    @stream_with_context
    def stream_ai_response(self, conversation_id: int, user_input: str):
        """流式处理AI响应"""
        print(f"\n[ChatManager] 开始处理消息 (会话ID: {conversation_id})")
        print(f"[ChatManager] 用户消息内容: {user_input[:100]}...")
        
        # 预先保存用户消息
        print("[ChatManager] 正在保存用户消息到数据库...")
        user_msg = Message(
            content=user_input,
            role='user',
            is_user=True,
            conversation_id=conversation_id,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(user_msg)
        db.session.commit()
        
        # 收集AI响应并流式返回
        print("[ChatManager] 开始生成AI响应...")
        ai_response = []
        for i, chunk in enumerate(self._generate_ai_response(user_input)):
            if i % 5 == 0:  # 每5个chunk打印一次进度
                print(f"[ChatManager] 正在流式生成响应 (已生成: {len(chunk)} 字符)")
            ai_response.append(chunk)
            yield chunk
        
        # 保存完整AI响应
        print(f"[ChatManager] 正在保存AI响应 (总长度: {len(ai_response)})")
        ai_msg = Message(
            content=''.join(ai_response),
            role='assistant',
            is_user=False,
            conversation_id=conversation_id
        )
        db.session.add(ai_msg)
        db.session.commit()
    
    def _generate_ai_response(self, prompt: str):
        print(f"[ChatManager] 调用AI生成响应 (输入长度: {len(prompt)})")
        """
        调用DeepSeek API生成响应
        参数:
            prompt: 用户输入
        返回:
            生成器，逐块返回AI响应
        """
        if not self.api_key or self.api_key == "your_api_key_here":
            yield "请配置有效的DeepSeek API密钥"
            return
            
        try:
            # 创建OpenAI客户端实例
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            
            # 使用1.0.0+版本的API调用方式
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except ImportError:
            yield "OpenAI客户端库未安装，请运行: pip install openai>=1.0.0"
        except Exception as e:
            print(f"AI API调用失败: {str(e)}")
            # 更友好的错误提示
            yield f"AI服务错误: {str(e)}"

# 初始化聊天管理器
chat_manager = ChatManager()

guga_chat_bp = Blueprint('guga_chat', __name__)

@guga_chat_bp.route('/guga/chat')
@login_required
def chat():
    conversation = chat_manager.get_or_create_conversation()
    return render_template('guga/chat.html', conversation=conversation)

@guga_chat_bp.route('/api/chat/history/<int:conversation_id>')
@login_required
def get_chat_history(conversation_id):
    try:
        # 验证会话所有权
        conv = Conversation.query.get_or_404(conversation_id)
        if conv.user_id != current_user.id:
            return jsonify({'error': '无权访问此会话'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        print(f"[DEBUG] 准备获取会话 {conversation_id} 的历史消息...")
        history = chat_manager.get_conversation_history(conversation_id, page, per_page)
        print(f"[DEBUG] 获取到历史消息: {len(history)} 条")
        
        try:
            # 测试序列化每条消息
            for i, msg in enumerate(history):
                try:
                    import json
                    json.dumps(msg)
                except Exception as e:
                    print(f"[ERROR] 消息 {i} 序列化失败: {str(e)}")
                    print(f"[DEBUG] 问题消息内容: {msg}")

            response = jsonify({
                'success': True,
                'messages': history
            })
            print("[DEBUG] JSON序列化成功")
            return response
        except Exception as e:
            print(f"[ERROR] JSON序列化失败: {str(e)}")
            print(f"[DEBUG] 完整历史消息: {history}")
            return jsonify({
                'error': '消息序列化失败',
                'details': str(e),
                'failed_at': str(e.__traceback__.tb_lineno) if hasattr(e, '__traceback__') else 'unknown'
            }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@guga_chat_bp.route('/api/chat/messages')
@login_required
def get_messages():
    """兼容性路由，处理前端期望的/api/chat/messages请求"""
    try:
        import traceback
        conversation_id = request.args.get('conversation_id')
        if not conversation_id:
            return jsonify({'error': '缺少conversation_id参数'}), 400
        
        # 确保conversation_id是有效整数
        try:
            conversation_id = int(conversation_id)
        except ValueError:
            return jsonify({'error': 'conversation_id必须是整数'}), 400
        
        # 调试日志
        print(f"尝试获取会话 {conversation_id} 的消息...")
        print(f"当前用户ID: {current_user.id}")
        
        # 验证会话存在且属于当前用户
        print(f"[DEBUG] 验证会话 {conversation_id} 属于用户 {current_user.id}")
        user_conv = db.session.query(UserConversation).filter_by(
            user_id=current_user.id,
            conversation_id=conversation_id
        ).first()
        
        if not user_conv:
            print(f"[DEBUG] 验证失败: 用户 {current_user.id} 无权访问会话 {conversation_id}")
            return jsonify({'error': '会话不存在或无权访问'}), 404
        
        print(f"[DEBUG] 验证通过: 会话 {conversation_id} 属于用户 {current_user.id}")
        
        # 调试SQL查询
        print(f"[DEBUG] 准备查询会话 {conversation_id} 的消息...")
        try:
            messages = Message.query.filter_by(conversation_id=conversation_id).all()
            print(f"[DEBUG] 查询到 {len(messages)} 条消息")
            for msg in messages[:3]:  # 打印前3条消息示例
                print(f"[DEBUG] 消息示例: ID={msg.id}, 内容={msg.content[:50]}...")
            
            return get_chat_history(conversation_id)
        except Exception as e:
            print(f"[ERROR] 查询消息时出错: {str(e)}")
            raise  # 继续向上抛出异常由外层处理
    except Exception as e:
        print("[ERROR] 获取消息时发生严重错误:")
        traceback.print_exc()
        # 检查数据库连接状态
        try:
            db_status = db.session.execute('SELECT 1').scalar()
            print(f"[DEBUG] 数据库连接状态: {'正常' if db_status == 1 else '异常'}")
        except Exception as db_error:
            print("[DEBUG] 数据库连接检查失败:", str(db_error))
        return jsonify({
            'error': '获取消息失败',
            'details': str(e),
            'stacktrace': traceback.format_exc()
        }), 500

@guga_chat_bp.route('/api/chat/conversations', methods=['GET'])
@login_required
def list_conversations():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # 通过UserConversation关联表查询当前用户的会话
        convs = db.session.query(Conversation)\
            .join(UserConversation, Conversation.id == UserConversation.conversation_id)\
            .filter(UserConversation.user_id == current_user.id)\
            .order_by(Conversation.updated_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
            
        if not convs.items:
            return jsonify({'conversations': [], 'total': 0, 'pages': 0})
            
        return jsonify({
            'conversations': [{
                'id': c.id,
                'title': c.title,
                'updated_at': c.updated_at.isoformat() if c.updated_at else None
            } for c in convs.items],
            'total': convs.total,
            'pages': convs.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@guga_chat_bp.route('/api/chat/conversations', methods=['POST'])
@login_required
def create_conversation():
    try:
        conv = Conversation(
            title=f"新对话-{datetime.now().strftime('%m-%d %H:%M')}",
            user_id=current_user.id
        )
        db.session.add(conv)
        db.session.commit()
        return jsonify({
            'id': conv.id,
            'title': conv.title
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@guga_chat_bp.route('/api/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        if 'conversation_id' not in data:
            return jsonify({'error': '缺少conversation_id参数'}), 400
        if 'message' not in data or not data['message'].strip():
            return jsonify({'error': '消息内容不能为空'}), 400

        # 验证会话所有权
        conv = Conversation.query.get_or_404(data['conversation_id'])
        if conv.user_id != current_user.id:
            return jsonify({'error': '无权访问此会话'}), 403

        # 处理流式响应
        return Response(
            chat_manager.stream_ai_response(conv.id, data['message']),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': '处理请求时出错',
            'details': str(e)
        }), 500

def handle_chat_request(conversation_id: int, message: str):
    """处理聊天请求的核心函数"""
    conv = Conversation.query.get_or_404(conversation_id)
    if conv.user_id != current_user.id:
        raise PermissionError("无权访问此会话")
    
    return Response(
        chat_manager.stream_ai_response(conv.id, message),
        mimetype='text/event-stream'
    )
