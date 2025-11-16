// Page Modules

// Available Masters Configuration
const MASTERS = {
  tocqueville: {
    id: 'tocqueville',
    name: '托克维尔',
    nameEn: 'Tocqueville',
    avatar: '🎓',
    description: '法国政治思想家，《论美国的民主》作者'
  },
  // 未来可添加更多大师
  // weber: {
  //   id: 'weber',
  //   name: '韦伯',
  //   nameEn: 'Weber',
  //   avatar: '📚',
  //   description: '德国社会学家，现代社会学奠基人之一'
  // }
};

// Chat Page
class ChatPage {
  constructor() {
    this.currentMaster = 'tocqueville';
    this.conversations = {}; // 按大师分组的对话
    this.isStreaming = false;
    this.userId = this.getUserId();
    this.loadConversations();
  }
  
  getUserId() {
    let userId = localStorage.getItem('userId');
    if (!userId) {
      userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('userId', userId);
    }
    return userId;
  }

  loadConversations() {
    try {
      const saved = localStorage.getItem('masterConversations');
      if (saved) {
        this.conversations = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
      this.conversations = {};
    }
    
    // 确保当前大师有对话记录
    if (!this.conversations[this.currentMaster]) {
      this.conversations[this.currentMaster] = [];
    }
  }

  saveConversations() {
    try {
      localStorage.setItem('masterConversations', JSON.stringify(this.conversations));
    } catch (error) {
      console.error('Error saving conversations:', error);
    }
  }

  getCurrentMessages() {
    return this.conversations[this.currentMaster] || [];
  }

  addMessageToConversation(role, content) {
    if (!this.conversations[this.currentMaster]) {
      this.conversations[this.currentMaster] = [];
    }
    this.conversations[this.currentMaster].push({ role, content });
    this.saveConversations();
  }
  
  render() {
    const master = MASTERS[this.currentMaster];
    const messages = this.getCurrentMessages();
    
    const container = document.createElement('div');
    container.innerHTML = `
      <div class="chat-container">
        <div class="master-selector-wrapper">
          <label for="master-selector" style="font-weight: 600; color: var(--color-text-title); margin-right: 12px;">
            选择大师:
          </label>
          <select id="master-selector" class="master-selector">
            ${Object.values(MASTERS).map(m => `
              <option value="${m.id}" ${m.id === this.currentMaster ? 'selected' : ''}>
                ${m.avatar} ${m.name} (${m.nameEn})
              </option>
            `).join('')}
          </select>
          <span class="master-description" style="margin-left: 16px; color: var(--color-text-secondary); font-size: 14px;">
            ${master.description}
          </span>
        </div>
        <div class="conversation" id="conversation">
          ${messages.length === 0 ? `
            <div class="empty-state">
              <div class="empty-icon">${master.avatar}</div>
              <h3 class="empty-title">开始与${master.name}对话</h3>
              <p class="empty-description">例如："${this.getExampleQuestion(this.currentMaster)}"</p>
            </div>
          ` : ''}
        </div>
        <div class="composer">
          <div class="composer-wrapper">
            <textarea 
              id="message-input" 
              class="composer-textarea" 
              placeholder="选择一位大师，开始对话..."
              rows="1"
            ></textarea>
            <div class="composer-actions">
              <button class="icon-button" id="clear-btn" title="清空当前对话">🗑️</button>
              <button class="button button-primary button-m" id="send-btn">
                <span>发送</span>
              </button>
            </div>
          </div>
          <div class="composer-hint">Enter 发送 | Shift+Enter 换行</div>
        </div>
      </div>
    `;
    
    // Setup event listeners
    setTimeout(() => {
      this.setupListeners();
      this.restoreConversation();
    }, 0);
    
    return container;
  }

  getExampleQuestion(masterId) {
    const examples = {
      tocqueville: '托克维尔如何看待地方自治？',
      weber: '韦伯的理性化理论是什么？',
    };
    return examples[masterId] || '请介绍一下您的思想。';
  }

  restoreConversation() {
    const messages = this.getCurrentMessages();
    const conversation = document.getElementById('conversation');
    
    if (messages.length > 0) {
      // Clear empty state
      conversation.innerHTML = '';
      
      // Restore all messages
      messages.forEach(msg => {
        const messageEl = createMessage(msg.role, msg.content, { showTools: msg.role === 'assistant' });
        conversation.appendChild(messageEl);
      });
      
      this.scrollToBottom();
    }
  }

  switchMaster(masterId) {
    if (this.isStreaming) {
      Toast.warning('请等待当前消息完成');
      return;
    }

    this.currentMaster = masterId;
    
    // Re-render the page
    const appContainer = document.getElementById('app');
    appContainer.innerHTML = '';
    const pageElement = this.render();
    appContainer.appendChild(pageElement);
    
    Toast.success(`已切换至${MASTERS[masterId].name}`);
  }
  
  setupListeners() {
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const clearBtn = document.getElementById('clear-btn');
    const masterSelector = document.getElementById('master-selector');
    
    // Master selector change
    masterSelector.addEventListener('change', (e) => {
      this.switchMaster(e.target.value);
    });
    
    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    });
    
    // Send on Enter (but not Shift+Enter)
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
    
    sendBtn.addEventListener('click', () => this.sendMessage());
    clearBtn.addEventListener('click', () => this.clearConversation());
  }
  
  async sendMessage() {
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const content = input.value.trim();
    
    if (!content || this.isStreaming) return;
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Add user message
    this.addMessage('user', content);
    this.addMessageToConversation('user', content);
    
    // Show loading state
    sendBtn.disabled = true;
    sendBtn.classList.add('loading');
    this.isStreaming = true;
    
    // Add assistant placeholder with master avatar
    const master = MASTERS[this.currentMaster];
    const assistantMessage = this.addMessage('assistant', '', { 
      isStreaming: true,
      masterAvatar: master.avatar
    });
    const bubble = assistantMessage.querySelector('.message-bubble');
    
    let fullResponse = '';
    const messages = this.getCurrentMessages();
    
    try {
      // Stream the response
      await api.streamMessage(
        messages,
        this.currentMaster,
        0.5,
        (content) => {
          // Update message with chunk
          fullResponse += content;
          bubble.innerHTML = formatMessageContent(fullResponse) + `
            <span class="typing-indicator">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </span>
          `;
          this.scrollToBottom();
        },
        () => {
          // Complete
          bubble.innerHTML = formatMessageContent(fullResponse);
          this.addMessageToConversation('assistant', fullResponse);
          this.isStreaming = false;
          sendBtn.disabled = false;
          sendBtn.classList.remove('loading');
          
          // Add tools to message
          const contentWrapper = assistantMessage.querySelector('.message-content');
          const tools = document.createElement('div');
          tools.className = 'message-tools';
          tools.innerHTML = `
            <button class="tool-button" title="复制" onclick="copyToClipboard(this)">📋 复制</button>
            <button class="tool-button" title="反馈" onclick="app.showFeedback()">👍 反馈</button>
          `;
          contentWrapper.appendChild(tools);
          
          this.scrollToBottom();
        },
        (error) => {
          // Error
          bubble.innerHTML = `<span style="color: var(--color-error)">❌ 发生错误: ${error.message}</span>`;
          bubble.classList.add('message-error');
          this.isStreaming = false;
          sendBtn.disabled = false;
          sendBtn.classList.remove('loading');
          Toast.error('消息发送失败: ' + error.message);
        }
      );
    } catch (error) {
      bubble.innerHTML = `<span style="color: var(--color-error)">❌ 发生错误: ${error.message}</span>`;
      bubble.classList.add('message-error');
      this.isStreaming = false;
      sendBtn.disabled = false;
      sendBtn.classList.remove('loading');
      Toast.error('消息发送失败: ' + error.message);
    }
  }
  
  addMessage(role, content, options = {}) {
    const conversation = document.getElementById('conversation');
    
    // Remove empty state if exists
    const emptyState = conversation.querySelector('.empty-state');
    if (emptyState) {
      emptyState.remove();
    }
    
    const message = createMessage(role, content, options);
    conversation.appendChild(message);
    this.scrollToBottom();
    
    return message;
  }
  
  scrollToBottom() {
    const conversation = document.getElementById('conversation');
    if (conversation) {
      conversation.scrollTop = conversation.scrollHeight;
    }
  }
  
  clearConversation() {
    Modal.confirm(
      '清空对话',
      `确定要清空与${MASTERS[this.currentMaster].name}的当前对话吗？此操作无法撤销。`,
      () => {
        this.conversations[this.currentMaster] = [];
        this.saveConversations();
        const conversation = document.getElementById('conversation');
        const master = MASTERS[this.currentMaster];
        conversation.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">${master.avatar}</div>
            <h3 class="empty-title">开始与${master.name}对话</h3>
            <p class="empty-description">例如："${this.getExampleQuestion(this.currentMaster)}"</p>
          </div>
        `;
        Toast.success('对话已清空');
      }
    );
  }
}

// Remove HistoryPage class completely

// Stats Page
class StatsPage {
  constructor() {
    this.stats = null;
  }
  
  async render() {
    const container = document.createElement('div');
    container.innerHTML = `
      <h1 class="mb-4">统计数据</h1>
      <div class="stats-grid" id="stats-grid">
        ${this.renderSkeleton()}
      </div>
      <div class="chart-container" id="chart-container">
        <div class="skeleton" style="height: 300px;"></div>
      </div>
    `;
    
    setTimeout(() => {
      this.loadStats();
    }, 0);
    
    return container;
  }
  
  renderSkeleton() {
    return Array(3).fill(0).map(() => `
      <div class="skeleton" style="height: 120px;"></div>
    `).join('');
  }
  
  async loadStats() {
    try {
      this.stats = api.getStatsLocal();
      this.renderStats();
    } catch (error) {
      const grid = document.getElementById('stats-grid');
      grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📊</div>
          <h3 class="empty-title">暂无统计数据</h3>
          <p class="empty-description">收集到足够反馈后会在此展示</p>
        </div>
      `;
    }
  }
  
  renderStats() {
    const grid = document.getElementById('stats-grid');
    const chartContainer = document.getElementById('chart-container');
    
    if (!this.stats) {
      grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📊</div>
          <h3 class="empty-title">暂无统计数据</h3>
          <p class="empty-description">收集到足够反馈后会在此展示</p>
        </div>
      `;
      return;
    }
    
    grid.innerHTML = `
      <div class="card stat-card">
        <div class="stat-value">${this.stats.average_rating?.toFixed(1) || 'N/A'}</div>
        <div class="stat-label">平均评分</div>
      </div>
      <div class="card stat-card">
        <div class="stat-value">${this.stats.total_feedback || 0}</div>
        <div class="stat-label">总反馈数</div>
      </div>
      <div class="card stat-card">
        <div class="stat-value">${this.stats.total_conversations || 0}</div>
        <div class="stat-label">总对话数</div>
      </div>
    `;
    
    chartContainer.innerHTML = `
      <h3 class="mb-4">评分分布</h3>
      <div class="empty-state">
        <div class="empty-icon">📈</div>
        <p class="empty-description">图表功能开发中...</p>
      </div>
    `;
  }
}

// Settings Page
class SettingsPage {
  render() {
    const container = document.createElement('div');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    container.innerHTML = `
      <h1 class="mb-4">设置</h1>
      
      <div class="settings-section">
        <h2 class="settings-section-title">外观</h2>
        
        <div class="settings-item">
          <div class="settings-item-info">
            <div class="settings-item-title">深色模式</div>
            <div class="settings-item-description">切换浅色和深色主题</div>
          </div>
          <div id="theme-toggle-setting"></div>
        </div>
      </div>
      
      <div class="settings-section">
        <h2 class="settings-section-title">数据</h2>
        
        <div class="settings-item">
          <div class="settings-item-info">
            <div class="settings-item-title">清除所有对话</div>
            <div class="settings-item-description">删除所有已保存的对话记录</div>
          </div>
          <button class="button button-danger button-m" id="clear-all-conversations">
            清除
          </button>
        </div>
      </div>
    `;
    
    setTimeout(() => {
      const toggleContainer = container.querySelector('#theme-toggle-setting');
      const toggle = createToggle(currentTheme === 'dark', (isActive) => {
        app.setTheme(isActive ? 'dark' : 'light');
      });
      toggleContainer.appendChild(toggle);

      // Clear conversations
      container.querySelector('#clear-all-conversations').addEventListener('click', () => {
        Modal.confirm(
          '清除所有对话',
          '确定要删除所有对话记录吗？此操作无法撤销。',
          () => {
            localStorage.removeItem('masterConversations');
            Toast.success('所有对话已清除');
          }
        );
      });
    }, 0);
    
    return container;
  }
}

// About Page
class AboutPage {
  render() {
    const container = document.createElement('div');
    container.innerHTML = `
      <h1 class="mb-4">关于</h1>
      
      <div class="card mb-4">
        <h2 class="mb-4">社会学大师对话系统</h2>
        <p style="line-height: 1.8;">
          本应用是一个基于社会学大师著作的 AI 对话系统，旨在帮助用户更好地理解和探索经典社会学思想。
          目前支持与托克维尔对话，未来将陆续加入更多社会学大师。
        </p>
      </div>

      <div class="card mb-4">
        <h3 class="mb-4">当前支持的大师</h3>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          ${Object.values(MASTERS).map(m => `
            <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: var(--color-surface-bg-alt); border-radius: 8px;">
              <span style="font-size: 32px;">${m.avatar}</span>
              <div>
                <div style="font-weight: 600; color: var(--color-text-title);">${m.name} (${m.nameEn})</div>
                <div style="font-size: 14px; color: var(--color-text-secondary);">${m.description}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
    
    return container;
  }
}
