# Conversation

## Contribution guide

- Upload Dockerfile along with your code

## 启动指南（前后端）

下面是使用 Windows PowerShell 在本地启动后端和前端的简明步骤。默认后端监听 `8000` 端口，前端静态服务使用 `3000` 端口。

注意：如果使用 Docker 或 Docker Compose，也提供了相应命令（见后文）。

### 1) 启动后端（开发模式）

```powershell
# 进入后端目录
cd backend

# （可选）创建并激活虚拟环境（如尚未创建）
python -m venv venv
# 激活虚拟环境（PowerShell）
.\venv\Scripts\Activate.ps1

# 复制环境变量模板并编辑 .env（在编辑器中填写 API Key 等）
Copy-Item .env.example .env
# 编辑 .env 文件以填入 PINECONE_API_KEY、GEMINI_API_KEY 等

# 安装依赖（仅首次）
pip install -r requirements.txt

# 启动后端（开发：带热重载）
uvicorn app.main:app --reload --port 8000
```

访问验证：
- Swagger UI: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 2) 启动前端（静态文件）

前端为纯静态文件，推荐使用简单的 HTTP 静态服务器。以下命令均在项目根或 `frontend` 目录下执行。

```powershell
# 切换到前端目录
cd frontend

# 使用 Python 内置服务器（需已安装 Python）
python -m http.server 3000

# 或者使用 Node.js 的 http-server（如已安装 Node.js）
npx http-server -p 3000

# 或者在 VS Code 中使用 Live Server 扩展，右键打开 `index.html` -> Open with Live Server
```

访问前端：

- 在浏览器打开 http://localhost:3000
- 确保后端已启动并可访问 http://localhost:8000

### 常见问题与排查

- 若前端请求后端失败，请检查后端是否运行并确认 `ALLOWED_ORIGINS` 包含 `http://localhost:3000`。
- 可使用 `curl http://localhost:8000/health` 检查后端健康状态。
- 前端有测试页面：`http://localhost:3000/test.html`，用于诊断 API 可达性与 CORS。

### 3) 简短说明

- 后端：FastAPI 应用，默认端口 `8000`，主要端点 `POST /api/v1/chat` 与 `POST /api/v1/telemetry`。
- 前端：纯静态 JS/CSS/HTML，建议使用端口 `3000` 提供静态资源。

### 4) 跨平台示例 — Linux / macOS

下面给出在 Linux 或 macOS 上常用的等效命令，供在非 Windows 环境下使用。默认端口与前述相同（后端 `8000`，前端 `3000`）。

后端（开发模式）：

```bash
# 进入后端目录
cd backend

# 创建并激活虚拟环境（仅首次）
python3 -m venv venv
source venv/bin/activate

# 复制环境变量模板并编辑 .env
cp .env.example .env
# 编辑 .env 文件以填入 PINECONE_API_KEY、GEMINI_API_KEY 等

# 安装依赖（仅首次）
pip install -r requirements.txt

# 启动后端（带热重载）
uvicorn app.main:app --reload --port 8000
```

前端（静态文件，Linux / macOS）：

```bash
# 切换到前端目录
cd frontend

# 使用 Python 内置服务器
python3 -m http.server 3000

# 或者使用 Node.js 的 http-server
npx http-server -p 3000
```

访问与排查同 Windows 部分所述。

