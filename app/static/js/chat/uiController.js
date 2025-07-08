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
        this.clearMessages();
        data.messages.forEach(msg => {
            this.addMessage(msg.content, msg.is_user ? 'user' : 'assistant');
        });
    }

    /**
     * 添加新消息
     * @param {string} content 
     * @param {string} role 
     */
    addMessage(content, role) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${role}-message`;
        messageElement.dataset.role = role;
        
        // 添加头像（仅AI消息）
        if (role === 'assistant') {
            const avatarDiv = document.createElement('div');
            avatarDiv.className = 'message-avatar';
            avatarDiv.innerHTML = `<img src="/static/guga/tomorin.jpg" alt="AI头像">`;
            messageElement.appendChild(avatarDiv);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString();
        
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
