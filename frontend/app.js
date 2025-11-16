// Main Application

class App {
  constructor() {
    this.currentPage = 'chat';
    this.pages = {
      chat: new ChatPage(),
      stats: new StatsPage(),
      settings: new SettingsPage(),
      about: new AboutPage()
    };
    
    this.init();
  }
  
  init() {
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.setTheme(savedTheme, false);
    
    // Setup navigation
    this.setupNavigation();
    
    // Setup theme toggle
    this.setupThemeToggle();
    
    // Handle initial route
    this.handleRoute();
    
    // Listen to hash changes
    window.addEventListener('hashchange', () => this.handleRoute());
  }
  
  setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.dataset.page;
        window.location.hash = page;
      });
    });
  }
  
  setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      this.setTheme(newTheme);
    });
  }
  
  setTheme(theme, save = true) {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update icon
    const themeIcon = document.querySelector('.theme-icon');
    themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    
    // Save to localStorage
    if (save) {
      localStorage.setItem('theme', theme);
    }
  }
  
  handleRoute() {
    const hash = window.location.hash.slice(1) || 'chat';
    this.navigateTo(hash);
  }
  
  async navigateTo(page) {
    if (!this.pages[page]) {
      page = 'chat';
    }
    
    this.currentPage = page;
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.dataset.page === page);
    });
    
    // Render page
    const appContainer = document.getElementById('app');
    
    // For chat page, don't recreate if already exists (preserve conversation)
    if (page === 'chat' && appContainer.querySelector('.chat-container')) {
      // Just update nav, don't re-render
      return;
    }
    
    appContainer.innerHTML = '';
    
    const pageInstance = this.pages[page];
    const pageElement = await pageInstance.render();
    appContainer.appendChild(pageElement);
    
    // Add fade-in animation
    appContainer.style.animation = 'fadeIn 120ms ease-out';
  }
  
  showFeedback() {
    const chatPage = this.pages.chat;
    const messages = chatPage.getCurrentMessages();
    
    if (!messages || messages.length === 0) {
      Toast.error('没有可反馈的对话');
      return;
    }
    
    const feedbackModal = new FeedbackModal(messages, chatPage.userId);
    feedbackModal.show();
  }
  
  deleteConversation(id) {
    // This method is no longer needed as we removed history page
    // But keep it for backward compatibility
    Toast.warning('历史功能已移除');
  }
  
  continueConversation(id) {
    Toast.warning('历史功能已移除');
  }
}

// Global app instance
let app;

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    app = new App();
  });
} else {
  app = new App();
}

// Make some functions globally accessible for inline event handlers
window.copyToClipboard = copyToClipboard;
window.copyCode = copyCode;
window.app = app;
