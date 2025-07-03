/**
 * 会话状态管理模块
 */
export default class ConversationStore {
    constructor() {
        this.currentConversationId = null;
    }

    /**
     * 加载会话列表
     */
    async loadConversations() {
        const response = await fetch('/api/chat/conversations');
        if (!response.ok) {
            throw new Error('加载会话失败');
        }
        const data = await response.json();
        return data.conversations || [];
    }

    /**
     * 创建新会话
     */
    async createNewConversation() {
        const response = await fetch('/api/chat/conversations', { 
            method: 'POST' 
        });
        if (!response.ok) {
            throw new Error('创建会话失败');
        }
        const data = await response.json();
        this.currentConversationId = data.id;
        return this.currentConversationId;
    }
}
