# CyberRange · 网络安全实战靶场

一个用于网络安全学习与训练的实战平台，包含 CTF 类题目（逆向、二进制漏洞、密码学、Web 安全、流量分析、数字取证）、Flag 提交判分、排行榜、用户中心与管理员出题后台。

暗黑终端风界面（荧光绿 + 红色点缀）。

> 当前进度：**Phase 1 已基本完成** —— 登录注册、题目大厅、题目详情、Flag 提交判分、排行榜、个人中心、管理后台（出题 + 附件上传）已可用。
> 流量分析器（Wireshark 式）等后续模块见《设计方案》。

---

## 技术栈

| 端 | 技术 |
|---|---|
| 前端 | Vue 3 · Vite · TypeScript · Pinia · Vue Router |
| 后端 | Python FastAPI · SQLAlchemy · SQLite |
| 包管理 | 前端 pnpm · 后端 pip / venv |

---

## 目录结构

```
CyberRange/
├── frontend/            # 前端（Vue3 + Vite）
│   ├── src/             # 源码（views / router / stores / api / styles / layouts）
│   ├── .env.development # 开发环境后端地址（VITE_API_BASE）
│   ├── package.json
│   └── pnpm-workspace.yaml
├── backend/             # 后端（FastAPI）
│   ├── app/             # 应用（main / models / routers / schemas / seed ...）
│   ├── requirements.txt # Python 依赖清单
│   ├── cyberrange.db    # SQLite 数据库（首次启动自动生成）
│   ├── uploads/         # 管理员上传的题目附件
│   └── .venv/           # Python 虚拟环境（不随项目分发）
└── README.md
```

---

## 环境要求

- Node.js 18+ 与 pnpm 12（前端）
- Python 3.10+（后端）

---

## 快速开始

### 1. 启动后端（在 `backend` 目录）

Windows 终端（PowerShell）：

```bash
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\activate          # 激活虚拟环境
pip install -r requirements.txt   # 安装依赖
uvicorn app.main:app --reload --port 8000
```

> 注意：建虚拟环境时务必用系统安装的 Python（`py -3.12` 即 Python Launcher），不要直接用 `python`——如果 PATH 里第一个 `python` 是临时/沙箱环境，建出来的 venv 会因解释器路径失效而无法使用。

macOS / Linux 终端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

后端默认运行在 `http://127.0.0.1:8000`，所有接口带 `/api` 前缀；交互式文档见 `http://127.0.0.1:8000/docs`。

### 2. 启动前端（在 `frontend` 目录）

```bash
cd frontend
pnpm install   # 首次或依赖更新后执行
pnpm run dev   # 开发模式
```

前端默认运行在 `http://localhost:5173`，浏览器打开即可使用。

> 前端开发模式通过 `frontend/.env.development` 直连后端，默认地址为 `http://127.0.0.1:8000/api`。若你的后端端口不同，请同步修改该文件。

---

## 默认管理员账号

- 用户名：`admin`
- 密码：`admin123`

首次启动后端会自动创建管理员并写入种子题目。普通用户可在登录页自行注册。

---

## 主要功能

- **题目大厅**：按类型（逆向/二进制漏洞/密码学/Web安全/流量分析/数字取证）浏览题目，支持分页；已解出的题目卡片带绿色标记。
- **题目详情**：查看描述、下载附件、提交 Flag 判分；显示最近解题者。
- **排行榜**：按解题积分排名。
- **个人中心**：查看自己的解题记录与积分。
- **管理后台**（仅管理员）：新建/编辑题目、设置 Flag、上传附件。
- **注册 / 登录**：暗黑终端风格双栏页面。

---

## 打包分发给别人

**打包时应排除**（体积大，且复制到别的电脑往往无法直接运行）：
- `backend/.venv`
- `frontend/node_modules`

接收方拿到文件夹后，按上面的「快速开始」执行：后端重建虚拟环境并装依赖，前端 `pnpm install` 后 `pnpm run dev`，即可运行。

**关于数据库**：
- 带上 `backend/cyberrange.db`：对方一打开就有你现有的题目、用户、解题记录（含 admin 账号）。
- 想给对方干净环境：删除 `backend/cyberrange.db`，首次启动后端会自动重建数据库并补种子题。

**关于前端直连地址**：`.env.development` 中的 `http://127.0.0.1:8000/api` 指向「运行者自己电脑上的 8000 端口」，对方本地跑后端时正好对上，一般无需修改。

---

## 常见问题

**Q：题目卡片显示 0 题或请求失败？**
A：确认后端已启动（`uvicorn ... --port 8000`），且 `frontend/.env.development` 中的 `VITE_API_BASE` 指向你的后端地址。

**Q：为什么是直连后端而不是走 Vite 代理？**
A：本地开发经 Vite 代理请求后端时，登录身份在某些环境下无法被正确识别（表现为「已解题卡片不显示标记」）。改为开发模式直连后端后该问题已解决；生产部署仍走同域 `/api`，不受影响。

---

## 后续阶段（详见《设计方案》）

- Phase 2：流量分析双模式 + Wireshark 式报文视图
- Phase 3：教学化（班级/统计/教师权限）
- Phase 4：公网化（合规/防滥用）

---

## 说明

本项目用于网络安全教学与合法训练环境，请勿用于任何非法用途。
