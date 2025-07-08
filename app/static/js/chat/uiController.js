/**
 * UI控制模块 - 处理所有界面交互
 */
export default class UIController {
    constructor(conversationStore) {
        console.log('[UIController] 开始初始化');
        
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatHistory = document.getElementById('chatHistory');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.conversationStore = conversationStore;
        
        console.log('[UIController] 元素获取结果:', {
            messageInput: !!this.messageInput,
            sendButton: !!this.sendButton,
            chatMessages: !!this.chatMessages,
            chatHistory: !!this.chatHistory,
            newChatBtn: !!this.newChatBtn
        });
        
        // 初始化事件监听
        this.setupEventListeners = this.initEventListeners;
        this.initEventListeners();
        console.log('[UIController] 初始化完成');
    }

    /**
     * 初始化事件监听
     */
    initEventListeners() {
        // 绑定store事件
        this.conversationStore.on('conversations-loaded', this.renderConversationHistory.bind(this));
        this.conversationStore.on('messages-loaded', this.displayMessages.bind(this));
        this.conversationStore.on('error', this.showError.bind(this));
    }

    /**
     * 设置消息处理器
     * @param {object} handlers 
     */
    setupMessageHandlers(handlers) {
        console.log('[UIController] 设置消息处理器:', handlers);
        console.log('[UIController] Send按钮初始状态:', this.sendButton.disabled ? '禁用' : '启用');
        
        this.sendButton.addEventListener('click', () => {
            console.log('点击发送按钮');
            const message = this.messageInput.value.trim();
            console.log('消息内容:', message);
            if (message) {
                console.log('调用发送处理器');
                handlers.onSend(message);
            }
            this.messageInput.value = '';
        });

        this.messageInput.addEventListener('keypress', (e) => {
            console.log('键盘输入:', e.key);
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const message = this.messageInput.value.trim();
                if (message) handlers.onSend(message);
                this.messageInput.value = '';
            }
        });

        this.messageInput.addEventListener('input', () => {
            const hasText = this.messageInput.value.trim().length > 0;
            this.sendButton.disabled = !hasText;
            console.log('输入变化 - 发送按钮状态:', hasText ? '启用' : '禁用');
        });

        this.newChatBtn.addEventListener('click', handlers.onNewConversation);
        
        // 初始状态检查
        console.log('UI控制器初始化完成');
        console.log('消息输入框:', this.messageInput);
        console.log('发送按钮:', this.sendButton);
    }

    /**
     * 渲染会话历史
     * @param {Array} conversations 
     */
    renderConversationHistory(conversations) {
        console.log('[UIController] 渲染会话历史，共', conversations.length, '个会话');
        this.chatHistory.innerHTML = '';
        
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div>${conv.title}</div>
                <small class="text-muted">${new Date(conv.updated_at).toLocaleString()}</small>
            `;
            item.addEventListener('click', () => {
                console.log('[UIController] 用户点击会话:', conv.id, conv.title);
                // 立即设置currentConversationId
                this.conversationStore.currentConversationId = conv.id;
                console.log('[UIController] 设置当前会话ID:', conv.id);
                this.conversationStore.getMessages(conv.id);
            });
            this.chatHistory.appendChild(item);
        });
    }

    /**
     * 显示消息列表
     * @param {object} data 
     */
    displayMessages(data) {
        console.group('[UIController] 显示消息列表');
        this.clearMessages();
        
        // 调试完整数据
        console.log('收到消息数据:', data);
        
        // 增强会话ID提取逻辑，添加详细调试
        let conversationId = null;
        
        // 检查所有可能的ID位置
        const possibleIdPaths = [
            'conversationId',
            'conversation_id', 
            'detail.conversationId',
            'messages.0.conversation_id',
            'conversation.id',
            'data.conversation_id',
            'payload.conversationId'
        ];
        
        console.log('[DEBUG] 开始搜索会话ID...');
        for (const path of possibleIdPaths) {
            try {
                const value = path.split('.').reduce((obj, key) => obj?.[key], data);
                if (value) {
                    conversationId = value;
                    console.log(`[SUCCESS] 从路径 ${path} 找到会话ID:`, conversationId);
                    break;
                }
            } catch (e) {
                console.log(`[DEBUG] 路径 ${path} 访问失败:`, e.message);
            }
        }
        
        // 检查store中的ID
        console.log('[DEBUG] 检查store中的会话ID...');
        if (!conversationId && this.conversationStore?.currentConversationId) {
            conversationId = this.conversationStore.currentConversationId;
            console.log('[SUCCESS] 使用store中的当前会话ID:', conversationId);
        }
        
        // 如果仍然没有，尝试从URL获取
        if (!conversationId) {
            console.log('[DEBUG] 尝试从URL参数获取会话ID...');
            const urlParams = new URLSearchParams(window.location.search);
            conversationId = urlParams.get('conversation_id');
            if (conversationId) {
                console.log('[SUCCESS] 从URL参数获取会话ID:', conversationId);
            }
        }
        
        if (!conversationId) {
            console.error('[ERROR] 无法从任何来源获取会话ID');
            console.log('[DEBUG] 完整数据对象:', data);
        }
        
        // 提取消息
        const messages = data?.messages || 
                        data?.detail?.messages || 
                        [];
        
        console.log('提取的会话ID:', conversationId);
        console.log('提取的消息数量:', messages.length);
        
        // 只要有ID就更新当前会话
        if (conversationId) {
            this.conversationStore.currentConversationId = conversationId;
            console.log('[UIController] 设置当前会话ID:', conversationId);
        }
        
        // 确保在渲染完成后绑定事件
        setTimeout(() => {
            messages.forEach(msg => {
                const messageElement = this.addMessage(
                    msg.content, 
                    msg.is_user ? 'user' : 'assistant'
                );
                // 确保设置conversationId
                if (conversationId) {
                    messageElement.dataset.conversationId = conversationId;
                }
            });
        }, 0);
        
        console.groupEnd();
    }

    /**
     * 添加新消息
     * @param {string} content 
     * @param {string} role 
     */
    /**
     * 创建并添加消息元素到聊天界面
     * @param {string} content - 消息内容
     * @param {string} role - 消息角色(user/assistant)
     * @returns {HTMLElement} 创建的消息元素
     */
    addMessage(content, role) {
        // 1. 创建消息容器元素
        const messageElement = document.createElement('div');
        if (!messageElement) {
            console.error('无法创建消息容器元素');
            return null;
        }

        // 2. 设置基础属性
        messageElement.className = `message ${role}-message`;
        messageElement.dataset.role = role;
        
        // 3. 设置会话ID（如果存在）
        try {
            if (this.conversationStore?.currentConversationId) {
                messageElement.dataset.conversationId = 
                    this.conversationStore.currentConversationId;
                console.log('设置消息会话ID:', 
                    this.conversationStore.currentConversationId);
            }
        } catch (e) {
            console.error('设置会话ID失败:', e);
        }

        // 4. 创建消息内容区域
        const contentDiv = document.createElement('div');
        if (contentDiv) {
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            messageElement.appendChild(contentDiv);
        }

        // 5. 创建时间显示区域
        const timeDiv = document.createElement('div');
        if (timeDiv) {
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString();
            messageElement.appendChild(timeDiv);
        }

        // 6. 如果是AI消息，添加额外元素
        if (role === 'assistant') {
            // 6.1 添加头像
            const avatarDiv = document.createElement('div');
            if (avatarDiv) {
                avatarDiv.className = 'message-avatar';
                avatarDiv.innerHTML = `<img src="/static/guga/tomorin.jpg" alt="AI头像">`;
                messageElement.insertBefore(avatarDiv, contentDiv);
            }

            // 6.2 添加分享按钮
            const shareBtn = document.createElement('button');
            if (shareBtn && timeDiv) {
                shareBtn.className = 'btn btn-sm btn-outline-primary share-btn';
                shareBtn.innerHTML = '<i class="fas fa-share"></i> 分享到博客';
                shareBtn.addEventListener('click', this.handleShareClick.bind(this));
                timeDiv.appendChild(shareBtn);
            }
        }

        // 7. 添加到聊天界面
        if (this.chatMessages) {
            this.chatMessages.appendChild(messageElement);
            this.scrollToBottom();
        }

        return messageElement;
    }

    /**
     * 处理分享按钮点击事件
     * @param {Event} e - 点击事件对象
     */
    handleShareClick(e) {
        e.stopPropagation();
        console.group('[UIController] 分享按钮点击处理');
        
        try {
            const messageElement = e.target.closest('.message');
            if (!messageElement) {
                throw new Error('找不到关联的消息元素');
            }

            // 获取会话ID（从多个可能的位置）
            const conversationId = messageElement.dataset?.conversationId || 
                                 this.conversationStore?.currentConversationId ||
                                 new URLSearchParams(window.location.search).get('conversation_id');
            
            if (!conversationId) {
                throw new Error('无法确定会话ID');
            }

            // 获取消息内容
            const content = messageElement.querySelector('.message-content')?.textContent || '';
            if (!content) {
                throw new Error('无法获取消息内容');
            }

            // 生成分享URL
            const url = `/post/create?conversation_id=${conversationId}&content=${encodeURIComponent(content)}`;
            console.log('生成的分享URL:', url);

            // 执行跳转
            window.location.href = url;
            
        } catch (error) {
            console.error('分享处理出错:', error);
            alert(`分享失败: ${error.message}`);
        } finally {
            console.groupEnd();
        }
        
        // 添加分享按钮(仅AI消息)
        if (role === 'assistant') {
            const shareBtn = document.createElement('button');
            shareBtn.className = 'btn btn-sm btn-outline-primary share-btn';
            shareBtn.innerHTML = '<i class="fas fa-share"></i> 分享到博客';
            shareBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                console.group('[UIController] 分享按钮点击 - 详细调试信息');
                
                try {
                    const messageElement = e.target.closest('.message');
                    if (!messageElement) {
                        throw new Error('找不到消息元素');
                    }
                    
                    // 从多个位置获取conversationId，添加详细调试
                    let conversationId = messageElement.dataset.conversationId;
                    console.log('从DOM元素获取的会话ID:', conversationId);
                    
                    if (!conversationId) {
                        conversationId = this.conversationStore.currentConversationId;
                        console.log('从store获取的会话ID:', conversationId);
                    }
                    
                    // 如果仍然没有，尝试从URL参数获取
                    if (!conversationId) {
                        const urlParams = new URLSearchParams(window.location.search);
                        conversationId = urlParams.get('conversation_id');
                        console.log('从URL参数获取的会话ID:', conversationId);
                    }
                    console.log('使用的会话ID:', conversationId);
                    
                    if (!conversationId) {
                        throw new Error('无法获取会话ID');
                    }
                    
                    const contentToShare = messageElement.querySelector('.message-content')?.textContent || content;
                    const encodedContent = encodeURIComponent(contentToShare);
                    const url = `/post/create?conversation_id=${conversationId}&content=${encodedContent}`;
                    
                    console.log('生成分享URL:', url);
                    window.location.href = url;
                    
                } catch (error) {
                    console.error('分享失败:', error);
                    alert(`分享失败: ${error.message}`);
                } finally {
                    console.groupEnd();
                }
            });
            timeDiv.appendChild(shareBtn);
        }
        
        messageElement.appendChild(contentDiv);
        messageElement.appendChild(timeDiv);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    /**
     * 清空消息
     */
    clearMessages() {
        this.chatMessages.innerHTML = '';
    }

    /**
     * 追加到最后一条消息
     * @param {string} content 
     */
    appendToLastMessage(content) {
        const lastMessage = this.chatMessages.lastChild;
        if (lastMessage && lastMessage.dataset.role === 'assistant') {
            const contentDiv = lastMessage.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.textContent += content;
                this.scrollToBottom();
            }
        } else {
            this.addMessage(content, 'assistant');
        }
    }

    /**
     * 显示错误信息
     * @param {string} message 
     */
    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'alert alert-danger';
        errorElement.textContent = message;
        this.chatMessages.appendChild(errorElement);
        this.scrollToBottom();
    }

    /**
     * 滚动到底部
     */
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}
