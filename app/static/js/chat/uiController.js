/**
 * UI控制模块 - 处理所有界面交互
 */
export default class UIController {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatHistory = document.getElementById('chatHistory');
    }

    /**
     * 设置事件监听器
     * @param {object} handlers 
     */
    setupEventListeners(handlers) {
        this.sendButton.addEventListener('click', () => {
            const message = this.messageInput.value.trim();
            if (message) handlers.onSend(message);
            this.messageInput.value = '';
        });

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const message = this.messageInput.value.trim();
                if (message) handlers.onSend(message);
                this.messageInput.value = '';
            }
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
