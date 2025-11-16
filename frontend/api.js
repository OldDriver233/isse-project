// API Service
class APIService {
  constructor() {
    this.baseURL = 'http://localhost:8000/api/v1';
  }

  async sendMessage(messages, character = 'tocqueville', temperature = 0.5) {
    try {
      const response = await fetch(`${this.baseURL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character: character,
          messages: messages,
          stream: false,
          temperature: temperature,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  async streamMessage(messages, character = 'tocqueville', temperature = 0.5, onChunk, onComplete, onError) {
    try {
      const response = await fetch(`${this.baseURL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character: character,
          messages: messages,
          stream: true,
          temperature: temperature,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.trim() && line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') {
              onComplete();
              return;
            }
            try {
              const json = JSON.parse(data);
              if (json.result?.delta?.content) {
                onChunk(json.result.delta.content);
              }
            } catch (e) {
              console.error('Error parsing chunk:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error streaming message:', error);
      onError(error);
    }
  }

  async submitFeedback(userId, rating, comment, messages) {
    try {
      const response = await fetch(`${this.baseURL}/telemetry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          rating: {
            overall_rating: rating,
            comment: comment || null,
          },
          messages: messages,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  }

  // 本地存储管理（用于历史记录和统计）
  saveConversation(conversation) {
    const conversations = this.getAllConversationsLocal();
    conversations.unshift(conversation);
    // 只保留最近50条
    if (conversations.length > 50) {
      conversations.pop();
    }
    localStorage.setItem('conversations', JSON.stringify(conversations));
  }

  getAllConversationsLocal() {
    try {
      const data = localStorage.getItem('conversations');
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error loading conversations:', error);
      return [];
    }
  }

  getConversationLocal(id) {
    const conversations = this.getAllConversationsLocal();
    return conversations.find(conv => conv.id === id);
  }

  deleteConversationLocal(id) {
    const conversations = this.getAllConversationsLocal();
    const filtered = conversations.filter(conv => conv.id !== id);
    localStorage.setItem('conversations', JSON.stringify(filtered));
  }

  saveFeedback(feedback) {
    const feedbacks = this.getAllFeedbacks();
    feedbacks.push(feedback);
    localStorage.setItem('feedbacks', JSON.stringify(feedbacks));
  }

  getAllFeedbacks() {
    try {
      const data = localStorage.getItem('feedbacks');
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error loading feedbacks:', error);
      return [];
    }
  }

  getStatsLocal() {
    const feedbacks = this.getAllFeedbacks();
    const conversations = this.getAllConversationsLocal();

    if (feedbacks.length === 0) {
      return null;
    }

    const totalRating = feedbacks.reduce((sum, fb) => sum + fb.rating, 0);
    const averageRating = totalRating / feedbacks.length;

    return {
      average_rating: averageRating,
      total_feedback: feedbacks.length,
      total_conversations: conversations.length,
      feedbacks: feedbacks,
    };
  }
}

// Export global instance
const api = new APIService();
