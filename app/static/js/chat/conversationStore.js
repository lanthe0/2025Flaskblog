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
        console.log(`[ConversationStore] 开始加载会话 ${conversationId} 的消息`);
        try {
            const response = await fetch(`/api/chat/messages?conversation_id=${conversationId}`);
            console.log(`[ConversationStore] 收到会话 ${conversationId} 的响应`);
            if (!response.ok) {
                const error = await response.json();
                console.error(`[ConversationStore] 加载会话 ${conversationId} 失败:`, error);
                throw new Error(error.error || '加载消息失败');
            }
            const data = await response.json();
            console.log(`[ConversationStore] 会话 ${conversationId} 加载完成，共 ${data.messages?.length || 0} 条消息`);
            this.eventTarget.dispatchEvent(new CustomEvent('messages-loaded', {
                detail: {
                    conversationId,
                    messages: data.messages
                }
            }));
            return data.messages || [];
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
