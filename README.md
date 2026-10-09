# CyberRange · 网络安全实战靶场与流量分析平台

集「CTF 靶场练习」与「Wireshark 式流量分析教学」于一体的安全学习平台。

> 当前为 **Phase 0 · 基础框架**：前后端脚手架 + 认证体系 + 暗黑终端主题 + 基础页面。
> 流量分析双模式、题库计分等后续阶段见《设计方案》。

## 技术栈
- **前端**：Vue 3 + TypeScript + Vite + Pinia + Vue Router（暗黑终端主题）
- **后端**：Python FastAPI + SQLAlchemy + SQLite(本地) / PostgreSQL(生产)
- **部署**：本地直接运行；后续可切 Docker Compose

## 目录结构
```
CyberRange/
├── backend/            # FastAPI 后端
│   └── app/
│       ├── main.py          # 入口
│       ├── config.py        # 配置(可用环境变量覆盖)
│       ├── database.py      # SQLAlchemy
│       ├── models.py        # User 模型
│       ├── schemas.py       # Pydantic 校验
│       ├── security.py      # bcrypt 密码 + JWT
│       ├── dependencies.py  # 依赖(当前用户/角色)
│       ├── seed.py          # 初始化(创建 admin)
│       └── routers/         # auth, users
├── frontend/           # Vue3 前端
│   └── src/
│       ├── api/             # API 客户端
│       ├── stores/          # Pinia
│       ├── router/          # 路由
│       ├── layouts/         # 主布局(顶部导航)
│       ├── views/           # 页面
│       └── styles/theme.css # 暗色主题
└── docker-compose.yml   # 供 Docker 环境使用(可先忽略)
```

## 本地运行（推荐，Docker 未安装时用这个）

### 1. 后端（终端 1）
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API 地址：http://127.0.0.1:8000
- 交互式文档：http://127.0.0.1:8000/docs
- 首次启动自动建库，并创建管理员账号：`admin / admin123`

### 2. 前端（终端 2）
```bash
cd frontend
npm install
npm run dev
```
- 页面地址：http://localhost:5173
- 前端已配置代理，`/api/*` 会自动转发到后端 `:8000`

### 3. 打开
浏览器访问 http://localhost:5173，用 `admin / admin123` 登录。

## 切换到 PostgreSQL / Docker（装了 Docker 之后）
在项目根目录：
```bash
docker compose up --build
```
- 后端：http://localhost:8000
- 前端：http://localhost:80
- 数据库：PostgreSQL(`cyberrange`)、缓存 Redis

## 默认管理员
- 用户名：`admin`，密码：`admin123`（仅本地开发，生产请改强密码）

## 后续阶段
- Phase 1：题库与计分闭环
- Phase 2：流量分析双模式 + Wireshark 视图
- Phase 3：教学化（班级/统计/教师权限）
- Phase 4：公网化（合规/防滥用）
