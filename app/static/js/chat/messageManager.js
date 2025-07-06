/**
 * 消息管理模块 - 处理所有消息相关逻辑
 */
export default class MessageManager {
    constructor(apiBaseUrl, uiController) {
        this.apiBaseUrl = apiBaseUrl;
        this.uiController = uiController;
        this.eventSource = null;
        this.offlineQueue = [];
        this.isOnline = navigator.onLine;
        this.MAX_OFFLINE_MESSAGES = 50;
        this.OFFLINE_STORAGE_KEY = 'chat_offline_messages';
        this.initialized = false;
        
        // 验证必要参数
        if (!apiBaseUrl) throw new Error('缺少apiBaseUrl参数');
        if (!uiController) throw new Error('缺少uiController参数');
        
        this.initEventListeners();
        this.loadOfflineMessages();
        this.initialized = true;
    }

    initEventListeners() {
        window.addEventListener('online', () => this.handleNetworkChange(true));
        window.addEventListener('offline', () => this.handleNetworkChange(false));
    }

    handleNetworkChange(isOnline) {
        this.isOnline = isOnline;
        if (isOnline) {
            this.processOfflineQueue();
        }
    }

    loadOfflineMessages() {
        const storedMessages = localStorage.getItem('offlineMessages');
        if (storedMessages) {
            this.offlineQueue = JSON.parse(storedMessages);
        }
    }

    async processOfflineQueue() {
        while (this.offlineQueue.length > 0) {
            const { conversationId, message } = this.offlineQueue.shift();
            try {
                await this.sendOnlineMessage(conversationId, message);
                localStorage.setItem('offlineMessages', JSON.stringify(this.offlineQueue));
            } catch (error) {
                console.error('处理离线消息失败:', error);
                this.offlineQueue.unshift({ conversationId, message });
                break;
            }
        }
    }

    async sendMessage(conversationId, message) {
        if (this.isOnline) {
            return this.sendOnlineMessage(conversationId, message);
        } else {
            this.addToOfflineQueue(conversationId, message);
            throw new Error('当前处于离线状态，消息已保存到本地');
        }
    }

    async sendOnlineMessage(conversationId, message) {
        console.log('[MessageManager] 准备发送消息', {
            conversationId,
            message: message.length > 50 ? message.substring(0, 50) + '...' : message
        });
        
        const response = await fetch(`${this.apiBaseUrl}/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                conversation_id: conversationId, 
                message: message 
            })
        });
        
        if (!response.ok) {
            throw new Error(`发送失败: ${response.status}`);
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aiResponse = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            console.log('[MessageManager] 收到AI响应片段:', chunk.length, '字符');
            aiResponse += chunk;
            // 触发消息更新事件
            document.dispatchEvent(new CustomEvent('aiMessageChunk', {
                detail: { chunk, fullResponse: aiResponse }
            }));
        }
        
        console.log('[MessageManager] 消息发送完成，总响应长度:', aiResponse.length);
        return { success: true };
    }

    addToOfflineQueue(conversationId, message) {
        this.offlineQueue.push({ conversationId, message });
        localStorage.setItem('offlineMessages', JSON.stringify(this.offlineQueue));
    }

    /**
     * 获取会话消息
     * @param {string} conversationId 
     */
    async getMessages(conversationId) {
        const response = await fetch(`${this.apiBaseUrl}/messages?conversation_id=${conversationId}`);
        if (!response.ok) {
            throw new Error('获取消息失败');
        }
        return response.json();
    }

    /**
     * 关闭SSE连接
     */
    closeSSE() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}
