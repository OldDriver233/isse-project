// UI Components Library

// Toast Notification
class Toast {
  static show(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };
    
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    container.appendChild(toast);
    
    if (duration > 0) {
      setTimeout(() => {
        toast.remove();
      }, duration);
    }
    
    return toast;
  }
  
  static success(message, duration) {
    return Toast.show(message, 'success', duration || 2500);
  }
  
  static error(message, duration) {
    return Toast.show(message, 'error', duration || 4000);
  }
  
  static warning(message, duration) {
    return Toast.show(message, 'warning', duration || 3000);
  }
}

// Modal Dialog
class Modal {
  constructor(title, content, options = {}) {
    this.title = title;
    this.content = content;
    this.options = {
      showClose: true,
      footer: null,
      onClose: null,
      ...options
    };
    this.element = null;
  }
  
  show() {
    const container = document.getElementById('modal-container');
    
    this.element = document.createElement('div');
    this.element.className = 'modal-overlay';
    this.element.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h2 class="modal-title">${this.title}</h2>
          ${this.options.showClose ? '<button class="icon-button modal-close">✕</button>' : ''}
        </div>
        <div class="modal-body">
          ${this.content}
        </div>
        ${this.options.footer ? `<div class="modal-footer">${this.options.footer}</div>` : ''}
      </div>
    `;
    
    container.appendChild(this.element);
    
    // Close handlers
    const closeBtn = this.element.querySelector('.modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }
    
    this.element.addEventListener('click', (e) => {
      if (e.target === this.element) {
        this.close();
      }
    });
    
    // ESC key handler
    this.escHandler = (e) => {
      if (e.key === 'Escape') {
        this.close();
      }
    };
    document.addEventListener('keydown', this.escHandler);
    
    return this;
  }
  
  close() {
    if (this.element) {
      this.element.remove();
      document.removeEventListener('keydown', this.escHandler);
      if (this.options.onClose) {
        this.options.onClose();
      }
    }
  }
  
  static confirm(title, message, onConfirm, onCancel) {
    const footer = `
      <button class="button button-secondary button-m" id="modal-cancel">取消</button>
      <button class="button button-primary button-m" id="modal-confirm">确认</button>
    `;
    
    const modal = new Modal(title, `<p>${message}</p>`, { footer });
    modal.show();
    
    const confirmBtn = modal.element.querySelector('#modal-confirm');
    const cancelBtn = modal.element.querySelector('#modal-cancel');
    
    confirmBtn.addEventListener('click', () => {
      if (onConfirm) onConfirm();
      modal.close();
    });
    
    cancelBtn.addEventListener('click', () => {
      if (onCancel) onCancel();
      modal.close();
    });
    
    return modal;
  }
}

// Feedback Modal
class FeedbackModal {
  constructor(messages, userId) {
    this.messages = messages;
    this.userId = userId;
    this.rating = 5;
  }
  
  show() {
    const content = `
      <div class="feedback-form">
        <div class="mb-4">
          <label class="settings-item-title">整体评分 (1-10)</label>
          <div class="rating-scale" style="display: flex; gap: 8px; margin-top: 12px;">
            ${Array.from({length: 10}, (_, i) => i + 1).map(num => `
              <button class="rating-btn button button-secondary button-m" data-rating="${num}">${num}</button>
            `).join('')}
          </div>
          <div class="rating-display" style="margin-top: 8px; font-size: 14px; color: var(--color-text-secondary);">
            当前评分: <span id="current-rating">5</span>
          </div>
        </div>
        <div class="mb-4">
          <label class="settings-item-title">评语（可选）</label>
          <textarea id="feedback-comment" class="textarea" style="margin-top: 8px;" placeholder="请分享您的想法..."></textarea>
        </div>
      </div>
    `;
    
    const footer = `
      <button class="button button-secondary button-m" id="feedback-cancel">取消</button>
      <button class="button button-primary button-m" id="feedback-submit">提交</button>
    `;
    
    const modal = new Modal('对最新回答评分', content, { footer });
    modal.show();
    
    // Rating buttons
    const ratingBtns = modal.element.querySelectorAll('.rating-btn');
    const currentRatingSpan = modal.element.querySelector('#current-rating');
    
    // Set initial selected rating
    ratingBtns[4].classList.add('button-primary');
    ratingBtns[4].classList.remove('button-secondary');
    
    ratingBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        ratingBtns.forEach(b => {
          b.classList.remove('button-primary');
          b.classList.add('button-secondary');
        });
        btn.classList.add('button-primary');
        btn.classList.remove('button-secondary');
        this.rating = parseInt(btn.dataset.rating);
        currentRatingSpan.textContent = this.rating;
      });
    });
    
    // Submit handler
    const submitBtn = modal.element.querySelector('#feedback-submit');
    const cancelBtn = modal.element.querySelector('#feedback-cancel');
    const commentArea = modal.element.querySelector('#feedback-comment');
    
    submitBtn.addEventListener('click', async () => {
      submitBtn.classList.add('loading');
      submitBtn.disabled = true;
      
      try {
        await api.submitFeedback(
          this.userId,
          this.rating,
          commentArea.value,
          this.messages
        );
        
        // Save feedback locally
        api.saveFeedback({
          rating: this.rating,
          comment: commentArea.value,
          timestamp: new Date().toISOString(),
        });
        
        Toast.success('感谢您的反馈！');
        modal.close();
      } catch (error) {
        Toast.error('提交反馈失败: ' + error.message);
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
      }
    });
    
    cancelBtn.addEventListener('click', () => {
      modal.close();
    });
    
    return modal;
  }
}

// Button Component
function createButton(text, options = {}) {
  const {
    variant = 'primary',
    size = 'm',
    icon = null,
    onClick = null,
    disabled = false,
    className = ''
  } = options;
  
  const button = document.createElement('button');
  button.className = `button button-${variant} button-${size} ${className}`;
  button.disabled = disabled;
  
  if (icon) {
    button.innerHTML = `<span class="icon">${icon}</span><span>${text}</span>`;
  } else {
    button.textContent = text;
  }
  
  if (onClick) {
    button.addEventListener('click', onClick);
  }
  
  return button;
}

// Input Component
function createInput(options = {}) {
  const {
    type = 'text',
    placeholder = '',
    value = '',
    className = '',
    onChange = null
  } = options;
  
  const input = document.createElement('input');
  input.className = `input ${className}`;
  input.type = type;
  input.placeholder = placeholder;
  input.value = value;
  
  if (onChange) {
    input.addEventListener('input', onChange);
  }
  
  return input;
}

// Textarea Component
function createTextarea(options = {}) {
  const {
    placeholder = '',
    value = '',
    className = '',
    rows = 3,
    onChange = null
  } = options;
  
  const textarea = document.createElement('textarea');
  textarea.className = `textarea ${className}`;
  textarea.placeholder = placeholder;
  textarea.value = value;
  textarea.rows = rows;
  
  if (onChange) {
    textarea.addEventListener('input', onChange);
  }
  
  return textarea;
}

// Card Component
function createCard(content, options = {}) {
  const { className = '', onClick = null } = options;
  
  const card = document.createElement('div');
  card.className = `card ${className}`;
  
  if (typeof content === 'string') {
    card.innerHTML = content;
  } else if (content instanceof HTMLElement) {
    card.appendChild(content);
  }
  
  if (onClick) {
    card.style.cursor = 'pointer';
    card.addEventListener('click', onClick);
  }
  
  return card;
}

// Empty State Component
function createEmptyState(icon, title, description, action = null) {
  const container = document.createElement('div');
  container.className = 'empty-state';
  
  container.innerHTML = `
    <div class="empty-icon">${icon}</div>
    <h3 class="empty-title">${title}</h3>
    <p class="empty-description">${description}</p>
  `;
  
  if (action) {
    container.appendChild(action);
  }
  
  return container;
}

// Skeleton Component
function createSkeleton(width = '100%', height = '20px') {
  const skeleton = document.createElement('div');
  skeleton.className = 'skeleton';
  skeleton.style.width = width;
  skeleton.style.height = height;
  return skeleton;
}

// Message Bubble Component
function createMessage(role, content, options = {}) {
  const { showTools = true, isStreaming = false, isError = false, masterAvatar = '🎓' } = options;
  
  const message = document.createElement('div');
  message.className = `message ${role}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  
  if (role === 'user') {
    avatar.textContent = 'U';
  } else {
    // Use master avatar for assistant
    avatar.textContent = masterAvatar;
  }
  
  const contentWrapper = document.createElement('div');
  contentWrapper.className = 'message-content';
  
  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${isError ? 'message-error' : ''}`;
  
  if (isStreaming) {
    bubble.innerHTML = `
      ${content}
      <span class="typing-indicator">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </span>
    `;
  } else {
    bubble.innerHTML = formatMessageContent(content);
  }
  
  contentWrapper.appendChild(bubble);
  
  if (showTools && role === 'assistant' && !isStreaming) {
    const tools = document.createElement('div');
    tools.className = 'message-tools';
    tools.innerHTML = `
      <button class="tool-button" title="复制" onclick="copyToClipboard(this)">📋 复制</button>
      <button class="tool-button" title="反馈" onclick="app.showFeedback()">👍 反馈</button>
    `;
    contentWrapper.appendChild(tools);
  }
  
  message.appendChild(avatar);
  message.appendChild(contentWrapper);
  
  return message;
}

// Format message content with code blocks, etc.
function formatMessageContent(content) {
  // Simple markdown-like formatting
  let formatted = content;
  
  // Code blocks with triple backticks
  formatted = formatted.replace(/```(\w+)?\n([\s\S]+?)```/g, (match, lang, code) => {
    return `
      <div class="code-block">
        <div class="code-header">
          <span>${lang || 'code'}</span>
          <button class="tool-button" onclick="copyCode(this)">📋 复制</button>
        </div>
        <div class="code-content"><code>${escapeHtml(code.trim())}</code></div>
      </div>
    `;
  });
  
  // Inline code
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // Bold
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // Italic
  formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  
  // Line breaks
  formatted = formatted.replace(/\n/g, '<br>');
  
  return formatted;
}

// Utility: Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Utility: Copy to clipboard
function copyToClipboard(button) {
  const bubble = button.closest('.message-content').querySelector('.message-bubble');
  const text = bubble.textContent;
  
  navigator.clipboard.writeText(text).then(() => {
    Toast.success('已复制到剪贴板');
  }).catch(() => {
    Toast.error('复制失败');
  });
}

// Utility: Copy code block
function copyCode(button) {
  const codeBlock = button.closest('.code-block').querySelector('code');
  const text = codeBlock.textContent;
  
  navigator.clipboard.writeText(text).then(() => {
    Toast.success('已复制代码');
  }).catch(() => {
    Toast.error('复制失败');
  });
}

// Toggle Component
function createToggle(isActive = false, onChange = null) {
  const toggle = document.createElement('div');
  toggle.className = `toggle ${isActive ? 'active' : ''}`;
  
  const thumb = document.createElement('div');
  thumb.className = 'toggle-thumb';
  toggle.appendChild(thumb);
  
  toggle.addEventListener('click', () => {
    toggle.classList.toggle('active');
    if (onChange) {
      onChange(toggle.classList.contains('active'));
    }
  });
  
  return toggle;
}

// Format date/time
function formatDateTime(date) {
  const d = new Date(date);
  const now = new Date();
  const diff = now - d;
  
  // Less than 1 minute
  if (diff < 60000) {
    return '刚刚';
  }
  
  // Less than 1 hour
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000);
    return `${minutes}分钟前`;
  }
  
  // Less than 1 day
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000);
    return `${hours}小时前`;
  }
  
  // Less than 7 days
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000);
    return `${days}天前`;
  }
  
  // Format as date
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
