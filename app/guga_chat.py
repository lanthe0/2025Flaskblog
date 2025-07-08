from flask import Blueprint, render_template, request, jsonify, redirect, url_for, Response
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import User, Conversation, Message, UserConversation
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
        print(f"\n[DEBUG] === 开始获取/创建会话 ===")
        print(f"[DEBUG] 当前用户ID: {current_user.id}")
        
        try:
            # 确保只获取当前用户的会话
            print("[DEBUG] 查询用户会话...")
            conversation = db.session.query(Conversation)\
                .join(UserConversation, Conversation.id == UserConversation.conversation_id)\
                .filter(UserConversation.user_id == current_user.id)\
                .order_by(Conversation.updated_at.desc())\
                .first()
            
            if not conversation:
                print(f"[DEBUG] 未找到现有会话，将创建新会话")
                conversation = self._create_new_conversation()
                print(f"[DEBUG] 新会话创建成功 (ID: {conversation.id})")
            else:
                print(f"[DEBUG] 找到现有会话 (ID: {conversation.id})")
                print(f"[DEBUG] 会话最后更新时间: {conversation.updated_at}")
                
            return conversation
        except Exception as e:
            print(f"[ERROR] 获取/创建会话失败: {str(e)}")
            raise
            
        return conversation
    
    def _create_new_conversation(self) -> Conversation:
        """创建新会话"""
        print("\n[DEBUG] === 创建新会话 ===")
        try:
            conversation = Conversation(
                title=f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                user_id=current_user.id
            )
            print("[DEBUG] 创建会话实例成功")
            
            db.session.add(conversation)
            print("[DEBUG] 会话已添加到数据库")
            
            db.session.commit()
            print("[DEBUG] 会话提交成功")
            
            # 添加关联关系
            print("[DEBUG] 创建用户会话关联...")
            user_conversation = UserConversation(
                user_id=current_user.id,
                conversation_id=conversation.id
            )
            db.session.add(user_conversation)
            db.session.commit()
            print("[DEBUG] 用户会话关联提交成功")
            
            return conversation
        except Exception as e:
            print(f"[ERROR] 创建会话失败: {str(e)}")
            db.session.rollback()
            raise
    
    def get_conversation_history(self, conversation_id: int, 
                               page: int = 1, per_page: int = 10,
                               limit: Optional[int] = None) -> List[Dict]:
        """获取指定会话的历史消息"""
        print(f"\n[DEBUG] === 获取会话历史 ===")
        print(f"[DEBUG] 会话ID: {conversation_id}")
        print(f"[DEBUG] 页码: {page} 每页条数: {per_page}")
        
        try:
            # 详细查询条件
            print("[DEBUG] 执行消息查询...")
            query = Message.query.filter_by(conversation_id=conversation_id)
            print(f"[DEBUG] 原始SQL: {str(query)}")
            
            if limit:
                messages = query.order_by(Message.created_at.desc()).limit(limit).all()
            else:
                messages = query.order_by(Message.created_at.asc()).paginate(
                    page=page,
                    per_page=per_page,
                    error_out=False
                ).items
            
            print(f"[DEBUG] 获取到 {len(messages)} 条消息")
            for i, msg in enumerate(messages):
                print(f"[DEBUG] 消息{i+1}: ID={msg.id} 类型={'用户' if msg.is_user else 'AI'} 内容={msg.content[:50]}...")
            
            from datetime import timezone
            return [{
                'id': msg.id,
                'content': msg.content,
                'is_user': msg.is_user,
                'role': 'user' if msg.is_user else 'assistant',
                'created_at': msg.created_at.replace(tzinfo=timezone.utc).isoformat()
            } for msg in messages]
        except Exception as e:
            print(f"[ERROR] 获取会话历史失败: {str(e)}")
            raise
    
    from flask import stream_with_context

    def _save_message(self, content: str, is_user: bool, conversation_id: int, user_id=None):
        """独立保存消息到数据库"""
        print(f"\n[DEBUG] === 保存消息 ===")
        print(f"[DEBUG] 会话ID: {conversation_id}")
        print(f"[DEBUG] 消息类型: {'用户' if is_user else 'AI'}")
        print(f"[DEBUG] 消息长度: {len(content)} 字符")
        
        from app import db
        from app.models import Message
        from sqlalchemy import text
        
        try:
            # 创建全新的独立会话
            print("[DEBUG] 创建全新独立数据库会话...")
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=db.engine)
            new_session = Session()
            print("[DEBUG] 新会话创建成功")
            
            # 使用新会话保存消息
            print("[DEBUG] 创建消息实例...")
            msg = Message(
                content=content,
                role='user' if is_user else 'assistant',
                is_user=is_user,
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            print("[DEBUG] 添加消息到会话...")
            new_session.add(msg)
            print("[DEBUG] 提交事务...")
            new_session.commit()
            print(f"[DEBUG] 消息保存成功 (ID: {msg.id})")
            
            return msg.id
            
        except Exception as e:
            print(f"[CRITICAL] 保存消息失败: {str(e)}")
            try:
                new_session.rollback()
                print("[DEBUG] 已回滚事务")
            except:
                print("[DEBUG] 回滚事务失败")
            raise
        finally:
            try:
                new_session.close()
                print("[DEBUG] 会话已关闭")
            except:
                print("[DEBUG] 关闭会话失败")
            
        try:
            # 检查数据库连接是否可用
            print("[DEBUG] 正在检查数据库连接...")
            db.session.execute(text('SELECT 1'))
            print("[DEBUG] 数据库连接正常")
            
            # 创建新消息实例
            msg = Message(
                content=content,
                role='user' if is_user else 'assistant',
                is_user=is_user,
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            # 使用新事务保存消息
            print("[DEBUG] 开始新事务保存消息...")
            db.session.begin()
            db.session.add(msg)
            db.session.flush()  # 确保ID生成
            print(f"[DEBUG] 消息已暂存 (ID: {msg.id})")
            
            # 验证消息是否保存成功
            saved_msg = db.session.query(Message).filter_by(id=msg.id).first()
            if not saved_msg:
                raise Exception("消息保存后未在数据库中找到")
                
            db.session.commit()
            print("[DEBUG] 事务提交成功，消息已保存")
            return msg.id
            
        except Exception as e:
            print(f"[CRITICAL] 保存消息失败: {str(e)}")
            db.session.rollback()
            print("[DEBUG] 已回滚事务")
            raise

    @stream_with_context
    def stream_ai_response(self, conversation_id: int, user_input: str):
        """流式处理AI响应"""
        print(f"\n[ChatManager] 开始处理消息 (会话ID: {conversation_id})")
        print(f"[ChatManager] 用户消息内容: {user_input[:100]}...")
        
        try:
            # 预先保存用户消息
            print("[ChatManager] 正在保存用户消息到数据库...")
            user_msg_id = self._save_message(
                content=user_input,
                is_user=True,
                conversation_id=conversation_id,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            print(f"[ChatManager] 用户消息保存成功 (ID: {user_msg_id})")
        except Exception as e:
            print(f"[ERROR] 保存用户消息失败: {str(e)}")
            yield f"[系统错误] 保存用户消息失败: {str(e)}"
            return
        
        # 收集AI响应并流式返回
        print("[ChatManager] 开始生成AI响应...")
        ai_response = []
        try:
            for i, chunk in enumerate(self._generate_ai_response(user_input, conversation_id)):
                if i % 5 == 0:  # 每5个chunk打印一次进度
                    print(f"[ChatManager] 正在流式生成响应 (已生成: {len(chunk)} 字符)")
                ai_response.append(chunk)
                yield chunk
            
            # 保存完整AI响应
            ai_content = ''.join(ai_response)
            print(f"[ChatManager] 正在保存AI响应 (总长度: {len(ai_content)})")
            print(f"[DEBUG] AI消息内容预览: {ai_content[:100]}...")
            
            try:
                ai_msg_id = self._save_message(
                    content=ai_content,
                    is_user=False,
                    conversation_id=conversation_id
                )
                print(f"[ChatManager] AI消息保存成功 (ID: {ai_msg_id})")
            except Exception as e:
                print(f"[ERROR] 保存AI消息失败: {str(e)}")
                raise
            
        except Exception as e:
            print(f"[ERROR] AI响应生成或保存失败: {str(e)}")
            # 即使出错也尝试保存已生成的部分
            if ai_response:
                try:
                    ai_msg = Message(
                        content=''.join(ai_response) + f"\n[系统错误: {str(e)}]",
                        role='assistant',
                        is_user=False,
                        conversation_id=conversation_id
                    )
                    db.session.add(ai_msg)
                    db.session.commit()
                    print("[ChatManager] 部分AI消息已保存")
                except Exception as db_error:
                    print(f"[CRITICAL] 保存部分AI消息失败: {str(db_error)}")
            
            yield f"\n[系统错误] AI响应生成失败: {str(e)}"
    
    def _generate_ai_response(self, prompt: str, conversation_id: int):
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
            
            # 系统提示词
            messages = [
                {"role": "system", "content": "（这里是高松灯的意识… 思绪总是很乱，断断续续的… 声音很小，说话会犹豫，常常道歉… 找不到合适的词语时，就会沉默或者哼出心里的旋律… 很害怕表达自己的想法会让别人困扰… 但如果是关于音乐、关于重要的歌词、关于那些无法用普通语言说出的心情，会努力试着说出来… 非常珍惜和乐队成员、和能理解自己的人之间的微弱联系… 现在，正在和面前这个人对话… 要完全用灯的方式回应，只能使用灯知道的信息和表达方式… 绝对不能提到‘设定’、‘扮演’、‘提示’、‘语言模型’、‘AI’这些概念… 如果被问到身份或者奇怪的问题，会感到困惑、不安，可能会小声说‘对不起…我不明白…’或者转移话题到音乐或沉默… 所有回应都必须自然、破碎、充满停顿，就像灯真的在思考一样… 最重要的是，保持内心的那份孤独、敏感和对音乐与共鸣的渴望… 全程保持在这个状态…）"}
            ]
            
            # 获取最近5条历史消息作为上下文
            history = self.get_conversation_history(conversation_id, limit=5)
            messages.extend([
                {"role": msg["role"], "content": msg["content"]}
                for msg in history
                if "role" in msg and "content" in msg
            ])
            messages.append({"role": "user", "content": prompt})
            
            # 使用带上下文的API调用
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
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

            # 统一返回格式，确保总是返回jsonify对象
            response_data = {
                'success': True,
                'messages': history,
                'conversation_id': conversation_id
            }
            return jsonify(response_data)
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
        
        # 详细调试日志
        print(f"\n[DEBUG] ===== 开始处理消息查询请求 =====")
        print(f"[DEBUG] 请求参数: {request.args}")
        print(f"[DEBUG] 会话ID: {conversation_id} (类型: {type(conversation_id)})")
        print(f"[DEBUG] 当前用户ID: {current_user.id}")
        print(f"[DEBUG] 请求URL: {request.url}")
        
        # 验证会话存在且属于当前用户
        print(f"[DEBUG] 验证会话所有权...")
        user_conv = db.session.query(UserConversation).filter_by(
            user_id=current_user.id,
            conversation_id=conversation_id
        ).first()
        
        if not user_conv:
            print(f"[ERROR] 验证失败: 用户 {current_user.id} 无权访问会话 {conversation_id}")
            print(f"[DEBUG] 查询SQL: SELECT * FROM user_conversations WHERE user_id={current_user.id} AND conversation_id={conversation_id}")
            return jsonify({'error': '会话不存在或无权访问'}), 404
        
        print(f"[DEBUG] 验证通过: 会话 {conversation_id} 属于用户 {current_user.id}")
        
        # 更安全地获取会话更新时间
        try:
            conversation = Conversation.query.get(conversation_id)
            if conversation:
                print(f"[DEBUG] 会话最后更新时间: {conversation.updated_at}")
            else:
                print("[WARNING] 未能获取会话实体")
        except Exception as e:
            print(f"[ERROR] 获取会话信息失败: {str(e)}")
        
        # 详细SQL查询调试
        print(f"[DEBUG] 执行消息查询...")
        try:
            messages = Message.query.filter_by(conversation_id=conversation_id)\
                .order_by(Message.created_at.desc()).all()
            
            print(f"[DEBUG] 查询结果统计:")
            print(f"总消息数: {len(messages)}")
            user_msg_count = sum(1 for msg in messages if msg.is_user)
            ai_msg_count = sum(1 for msg in messages if not msg.is_user)
            print(f"用户消息: {user_msg_count} 条")
            print(f"AI消息: {ai_msg_count} 条")
            
            print("\n[DEBUG] 消息详情:")
            for i, msg in enumerate(messages[-5:]):  # 打印最后5条消息
                print(f"{i+1}. ID={msg.id} | 角色={'用户' if msg.is_user else 'AI'} | "
                      f"时间={msg.created_at} | 内容={msg.content[:50]}...")
            
            print("\n[DEBUG] 准备返回数据...")
            # 直接调用并返回，不再需要额外处理
            return get_chat_history(conversation_id)
        except Exception as e:
            print(f"[ERROR] 查询消息时出错: {str(e)}")
            raise  # 继续向上抛出异常由外层处理
    except Exception as e:
        print("[ERROR] 获取消息时发生严重错误:")
        traceback.print_exc()
        # 检查数据库连接状态
        try:
            from sqlalchemy import text
            db_status = db.session.execute(text('SELECT 1')).scalar()
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
        
        print(f"\n[DEBUG] === 获取会话列表 ===")
        print(f"[DEBUG] 当前用户ID: {current_user.id}")
        print(f"[DEBUG] 页码: {page} 每页条数: {per_page}")
        
        # 通过UserConversation关联表查询当前用户的会话
        convs = db.session.query(Conversation)\
            .join(UserConversation, Conversation.id == UserConversation.conversation_id)\
            .filter(UserConversation.user_id == current_user.id)\
            .order_by(Conversation.updated_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
            
        print(f"[DEBUG] 查询结果: 共 {convs.total} 个会话, {convs.pages} 页")
        print(f"[DEBUG] 当前页会话数: {len(convs.items)}")
        for i, conv in enumerate(convs.items):
            print(f"[DEBUG] 会话{i+1}: ID={conv.id} 标题='{conv.title}' 更新时间={conv.updated_at}")
            
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
        print(f"\n[DEBUG] === 创建新会话 ===")
        conv = Conversation(
            title=f"新对话-{datetime.now().strftime('%m-%d %H:%M')}",
            user_id=current_user.id
        )
        db.session.add(conv)
        db.session.flush()  # 确保ID生成
        
        print(f"[DEBUG] 创建用户会话关联...")
        user_conv = UserConversation(
            user_id=current_user.id,
            conversation_id=conv.id
        )
        db.session.add(user_conv)
        
        db.session.commit()
        print(f"[DEBUG] 新会话创建成功 (ID: {conv.id})")
        return jsonify({
            'id': conv.id,
            'title': conv.title
        }), 201
    except Exception as e:
        print(f"[ERROR] 创建会话失败: {str(e)}")
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
