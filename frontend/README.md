# 社会学大师对话系统 - 前端

这是社会学大师对话系统的前端应用，使用纯 JavaScript 开发，支持与多位社会学大师进行AI对话。

## 功能特性

- 💬 **多大师对话** - 支持选择不同的社会学大师进行对话（当前支持托克维尔）
- 🔄 **对话保留** - 页面切换后对话内容保留，每位大师的对话独立存储
- 📊 **统计数据** - 查看使用统计和反馈分析
- ⚙️ **个性化设置** - 主题切换、数据管理
- 🎨 **优雅设计** - 遵循现代 UI/UX 设计规范

## 技术栈

- **纯 JavaScript** - 无框架依赖
- **CSS Variables** - 支持主题切换
- **Responsive Design** - 完全响应式布局
- **Accessibility** - 符合 WCAG 无障碍标准

## 项目结构

```
frontend/
├── index.html          # 主 HTML 文件
├── styles.css          # 全局样式和组件样式
├── app.js              # 主应用逻辑和路由
├── components.js       # UI 组件库
├── pages.js            # 页面模块
├── api.js              # API 服务
└── README.md           # 项目说明
```

## 快速开始

### 1. 启动后端服务

确保后端服务已在 `http://localhost:8000` 运行。

在 `backend` 目录下：

```bash
# Windows PowerShell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

或者：

```bash
# 使用已有的 uvicorn 终端
# 确保后端服务已启动
```

验证后端运行：访问 http://localhost:8000/docs 查看API文档

### 2. 启动前端

由于是纯静态文件，可以使用任何 HTTP 服务器：

**使用 Python:**
```bash
cd frontend
python -m http.server 3000
```

**使用 Node.js (http-server):**
```bash
cd frontend
npx http-server -p 3000
```

**使用 VS Code Live Server:**
1. 安装 Live Server 扩展
2. 右键 `index.html`
3. 选择 "Open with Live Server"

### 3. 访问应用

在浏览器中打开 `http://localhost:3000`

### 4. 测试 API 连接

如果遇到问题，可以打开 `test.html` 测试后端API连接：
```
http://localhost:3000/test.html
```

这个页面可以帮助诊断：
- 后端服务是否正常运行
- API 端点是否可访问
- CORS 配置是否正确

## 页面说明

### Chat（聊天）
- 主对话界面
- 大师选择器：切换不同社会学大师
- 支持流式响应
- 消息工具栏（复制、反馈）
- Enter 发送，Shift+Enter 换行
- 对话按大师分别保存，页面切换后保留

### Stats（统计）
- 平均评分
- 总反馈数
- 评分分布

### Settings（设置）
- 深色/浅色主题切换
- 清除所有对话记录
- 清除反馈数据

### About（关于）
- 应用介绍
- 支持的大师列表
- 使用指南
- 快捷键说明

## UI 设计规范

本应用严格遵循 `UI_DESIGN.md` 中的设计规范：

- **颜色系统** - 使用 CSS Variables 实现主题切换
- **排版** - 系统字体栈，标准字号和行高
- **间距** - 4px 基准的间距系统
- **组件** - 统一的按钮、输入框、卡片等组件
- **动效** - 克制的微交互和过渡动画
- **响应式** - 支持移动端和桌面端

## API 集成

前端通过 `api.js` 与后端通信，主要接口：

### 后端 API
- `POST /api/v1/chat` - 聊天接口（支持流式和非流式）
- `POST /api/v1/telemetry` - 提交反馈

### 本地存储
由于后端当前只提供聊天接口，以下功能使用浏览器 localStorage 实现：
- 对话历史（按大师分组存储）
- 反馈统计
- 用户设置

## 新特性

### 多大师支持
- 在聊天页面顶部选择不同的社会学大师
- 每位大师的对话独立保存
- 切换大师不会丢失对话历史

### 对话保留
- 页面切换后对话内容保留
- 刷新浏览器后对话恢复
- 可随时清空特定大师的对话

### 未来计划
- 添加更多社会学大师（韦伯、涂尔干等）
- 增强对话导出功能
- 支持对话分享

## 故障排查

### 消息发送失败

1. **检查后端服务**
   ```bash
   # 访问健康检查端点
   curl http://localhost:8000/health
   ```

2. **检查 API 文档**
   - 访问 http://localhost:8000/docs
   - 确认 `/api/v1/chat` 端点存在

3. **检查环境变量**
   - 确保 `.env` 文件包含 `PINECONE_API_KEY` 和 `GEMINI_API_KEY`

4. **查看浏览器控制台**
   - 按 F12 打开开发者工具
   - 查看 Network 标签中的请求详情
   - 查看 Console 中的错误信息

5. **使用测试页面**
   - 打开 `test.html` 进行 API 测试

### CORS 错误

如果看到 CORS 相关错误，检查后端 `app/config.py` 中的 `ALLOWED_ORIGINS` 配置：

```python
ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]
```

## 浏览器支持

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 开发说明

### 修改主题颜色

在 `styles.css` 中修改 CSS Variables：

```css
:root {
  --color-primary-500: #3B82F6;
  --color-primary-600: #2563EB;
  /* ... */
}
```

### 添加新页面

1. 在 `pages.js` 中创建新页面类
2. 在 `app.js` 中注册页面
3. 在导航栏添加链接

### 自定义组件

所有 UI 组件在 `components.js` 中定义，可以复用和扩展。

## 性能优化

- 最小化 DOM 操作
- 使用事件委托
- 懒加载和按需渲染
- CSS 动画优先于 JS 动画

## 无障碍支持

- 键盘导航
- ARIA 属性
- 焦点管理
- 屏幕阅读器支持

## 许可证

MIT License
