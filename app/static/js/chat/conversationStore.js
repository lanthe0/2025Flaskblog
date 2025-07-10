/**
 * 会话状态管理模块
 */
export default class ConversationStore {
    constructor() {
        this.currentConversationId = null;
        this.eventTarget = new EventTarget();
    }

    /**
     * 加载会话列表
     */
    async loadConversations() {
        try {
            const response = await fetch('/api/chat/conversations');
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '加载会话失败');
            }
            const data = await response.json();
            this.eventTarget.dispatchEvent(new CustomEvent('conversations-loaded', {
                detail: data.conversations
            }));
            return data.conversations || [];
        } catch (error) {
            this.eventTarget.dispatchEvent(new CustomEvent('error', {
                detail: error.message
            }));
            throw error;
        }
    }

    /**
     * 创建新会话
     */
    async createNewConversation() {
        try {
            const response = await fetch('/api/chat/conversations', { 
                method: 'POST' 
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '创建会话失败');
            }
            const data = await response.json();
            this.currentConversationId = data.id;
            this.eventTarget.dispatchEvent(new CustomEvent('conversation-created', {
                detail: data
            }));
            return this.currentConversationId;
        } catch (error) {
            this.eventTarget.dispatchEvent(new CustomEvent('error', {
                detail: error.message
            }));
            throw error;
        }
    }

    /**
     * 加载会话消息
     */
    async getMessages(conversationId) {
        console.group(`[ConversationStore] 开始加载会话 ${conversationId} 的消息`);
        try {
            console.log('1. 设置当前会话ID:', conversationId);
            this.currentConversationId = conversationId;
            
            const response = await fetch(`/api/chat/messages?conversation_id=${conversationId}`);
            console.log('2. 收到响应:', response);
            
            if (!response.ok) {
                const error = await response.json();
                console.error('3. 加载失败:', error);
                throw new Error(error.error || '加载消息失败');
            }
            
            const data = await response.json();
            console.log('4. 完整API响应:', JSON.stringify(data, null, 2));
            
            // 使用实际存在的字段
            const processedData = {
                conversationId: conversationId, // 直接使用传入的conversationId
                messages: Array.isArray(data) ? data : (data.messages || [])
            };
            
            console.log('5. 处理后数据:', processedData);
            
            this.eventTarget.dispatchEvent(new CustomEvent('messages-loaded', {
                detail: processedData
            }));
            
            console.log('6. 当前会话ID验证:', this.currentConversationId);
            console.groupEnd();
            return processedData.messages;
        } catch (error) {
            this.eventTarget.dispatchEvent(new CustomEvent('error', {
                detail: error.message
            }));
            throw error;
        }
    }

    /**
     * 添加事件监听
     */
    on(event, callback) {
        this.eventTarget.addEventListener(event, (e) => callback(e.detail));
    }
}
