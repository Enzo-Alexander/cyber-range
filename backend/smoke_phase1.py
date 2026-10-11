"""Phase 1 后端冒烟测试：管理员出题 -> 做题 -> 提交Flag -> 计分排名 全流程。"""
import os
import tempfile

# 用独立临时库，避免影响正在运行的服务
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name.replace(os.sep, '/')}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import init_db  # noqa: E402

init_db()  # 显式建表 + 种子

OK = []


def check(name: str, cond: bool, extra: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    OK.append(cond)
    print(f"[{status}] {name} {extra}")


with TestClient(app) as c:
    # 管理员登录
    r = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    check("管理员登录", r.status_code == 200)
    admin_token = r.json()["access_token"]
    H_ADMIN = {"Authorization": f"Bearer {admin_token}"}

    # 种子题目已存在
    r = c.get("/api/challenges")
    check("题目列表返回种子题目", r.status_code == 200 and len(r.json()) >= 8)
    ch = r.json()[0]

    # 管理员创建题目
    r = c.post("/api/admin/challenges", json={
        "title": "冒烟测试题",
        "category": "Web安全",
        "difficulty": 1,
        "points": 500,
        "description": "测试题目",
        "flag": "flag{smoke_test}",
        "status": "published",
    }, headers=H_ADMIN)
    check("管理员创建题目", r.status_code == 201, f"->{r.json().get('title')}")
    new_id = r.json()["id"]

    # 普通用户注册 + 登录
    r = c.post("/api/auth/register", json={
        "username": "tester", "email": "tester@x.com", "password": "pass123456",
    })
    check("普通用户注册", r.status_code == 201)
    r = c.post("/api/auth/login", json={"username": "tester", "password": "pass123456"})
    user_token = r.json()["access_token"]
    H_USER = {"Authorization": f"Bearer {user_token}"}

    # 非管理员不能进管理接口
    r = c.get("/api/admin/challenges", headers=H_USER)
    check("普通用户访问管理接口被拒", r.status_code == 403)

    # 提交正确 flag
    r = c.post(f"/api/challenges/{new_id}/submit", json={"flag": "flag{smoke_test}"}, headers=H_USER)
    check("提交正确Flag判分", r.status_code == 200 and r.json()["success"], f"->{r.json()}")

    # 重复提交被拒
    r = c.post(f"/api/challenges/{new_id}/submit", json={"flag": "flag{smoke_test}"}, headers=H_USER)
    check("重复提交被拦截", r.json()["success"] is False)

    # 提交错误 flag
    r = c.post(f"/api/challenges/{ch['id']}/submit", json={"flag": "wrong"}, headers=H_USER)
    check("提交错误Flag", r.json()["success"] is False)

    # 排行榜出现 tester
    r = c.get("/api/challenges/leaderboard")
    lb = r.json()
    check("排行榜包含tester", any(x["username"] == "tester" and x["total_points"] == 500 for x in lb), f"->{lb[:1]}")

    # 个人资料
    r = c.get("/api/users/me/profile", headers=H_USER)
    prof = r.json()
    check("个人资料-总分", prof["total_points"] == 500)
    check("个人资料-解题数", prof["total_solved"] == 1)
    check("个人资料-排名>0", prof["rank"] >= 1)
    check("个人资料-掌握度", len(prof["progress"]) == 6)
    check("个人资料-最近解题记录", len(prof["solves"]) == 1 and prof["solves"][0]["title"] == "冒烟测试题")

    # 题目已解状态标记
    r = c.get("/api/challenges", headers=H_USER)
    card = next(x for x in r.json() if x["id"] == new_id)
    check("题目列表-已解标记", card["solved_by_me"] is True)

    # 管理员统计
    r = c.get("/api/admin/stats", headers=H_ADMIN)
    check("管理统计卡", r.status_code == 200 and r.json()["challenge_total"] >= 9)

print(f"\n结果: {sum(OK)}/{len(OK)} 通过")
if not all(OK):
    raise SystemExit(1)
