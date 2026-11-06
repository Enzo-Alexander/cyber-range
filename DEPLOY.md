# CyberRange 单机部署

以下步骤适用于阿里云 ECS Linux 服务器，并假设使用 IP `101.201.253.37`。

## 1. 放行安全组

在阿里云 ECS 控制台的入方向安全组中放行：

| 端口 | 协议 | 来源 |
| --- | --- | --- |
| 22 | TCP | 你的公网 IP |
| 80 | TCP | 0.0.0.0/0 |

不要对公网开放后端 `8000`、数据库端口等内部服务端口。

## 2. 本地打包

在项目根目录执行：

```powershell
tar --exclude=frontend/node_modules --exclude=frontend/dist --exclude=backend/.venv --exclude=.git -czf cyberrange-deploy.tar.gz .
scp .\cyberrange-deploy.tar.gz root@101.201.253.37:/tmp/
```

当前打包命令会包含 `backend/cyberrange.db` 和 `backend/uploads`。

- 如果要保留现有数据，请先停止本地后端，再执行打包。
- 如果要全新部署，请在 `tar` 命令中再加 `--exclude=backend/cyberrange.db`，服务器首次启动会自动生成空数据库。

## 3. 服务器解压

```bash
ssh root@101.201.253.37
mkdir -p /opt/cyberrange
tar -xzf /tmp/cyberrange-deploy.tar.gz -C /opt/cyberrange
cd /opt/cyberrange
```

如果要把本地数据库带到服务器：

```bash
mkdir -p data
cp backend/cyberrange.db data/cyberrange.db
```

不复制数据库时，后端首次启动会自动建立数据库、管理员账号并写入种子数据。

## 4. 安装 Docker

Ubuntu、Debian、Alibaba Cloud Linux、CentOS 可以使用 Docker 官方安装脚本：

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker compose version
```

如果当前不是 root 用户，请给命令加 `sudo`。

## 5. 配置生产环境变量

```bash
cp .env.example .env
openssl rand -hex 32
nano .env
```

将生成的随机字符串填入 `SECRET_KEY`。如果没有域名，`CORS_ORIGINS` 保持：

```dotenv
CORS_ORIGINS=http://101.201.253.37
```

不要提交服务器上的 `.env`。

## 6. 启动

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
curl http://127.0.0.1/health
```

浏览器访问：

```text
http://101.201.253.37
```

默认管理员账号为 `admin`，密码为 `admin123`。首次登录后应立即修改密码。

## 7. 日常维护

查看日志：

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### 更新网站

更新时只上传代码，不要覆盖服务器上的 `.env`、`data/` 和 `backend/uploads/`。

先在本地项目根目录测试并打包：

```powershell
cd E:\项目设计方案\CyberRange
npm --prefix frontend run build

tar `
  --exclude=frontend/node_modules `
  --exclude=frontend/dist `
  --exclude=backend/.venv `
  --exclude=backend/cyberrange.db `
  --exclude=backend/uploads `
  --exclude=data `
  --exclude=.env `
  --exclude=.git `
  -czf cyberrange-update.tar.gz .

scp .\cyberrange-update.tar.gz root@101.201.253.37:/tmp/
```

然后在服务器上备份数据库、解压代码并重新构建：

```bash
ssh root@101.201.253.37
cd /opt/cyberrange

docker compose -f docker-compose.prod.yml stop backend
cp data/cyberrange.db "data/cyberrange-$(date +%F-%H%M).db"
tar -xzf /tmp/cyberrange-update.tar.gz -C /opt/cyberrange
docker compose -f docker-compose.prod.yml up -d --build
```

检查结果：

```bash
docker compose -f docker-compose.prod.yml ps
curl http://127.0.0.1/health
```

容器正常后访问 `http://101.201.253.37` 检查页面。

注意：

- `data/cyberrange.db` 保存线上用户、题目和解题记录，绝不能用本地旧数据库覆盖。
- `backend/uploads/` 保存线上附件，更新包中不应包含该目录。
- `.env` 保存服务器密钥，更新包中也不应包含它。
- 如果以后修改了数据库模型字段，仅重新构建不够，需要单独做数据库迁移。

### 备份

```bash
cd /opt/cyberrange
docker compose -f docker-compose.prod.yml stop backend
cp data/cyberrange.db "data/cyberrange-$(date +%F-%H%M).db"
tar -czf "backend/uploads-$(date +%F-%H%M).tar.gz" -C backend uploads
docker compose -f docker-compose.prod.yml start backend
```

数据库和上传文件分别保存在宿主机 `data/` 与 `backend/uploads/`，重建容器不会丢失。
