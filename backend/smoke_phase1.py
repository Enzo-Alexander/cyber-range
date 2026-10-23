"""Phase 1 后端冒烟测试：管理员出题 -> 做题 -> 提交Flag -> 计分排名 全流程。"""
import os
import tempfile
from datetime import datetime

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
    check(
        "个人资料-等级",
        prof["level"] >= 1
        and prof["level_required"] == 5
        and 0 <= prof["level_progress"] < 5,
    )
    check("个人资料-掌握度", len(prof["progress"]) == 6)
    check("个人资料-最近解题记录", len(prof["solves"]) == 1 and prof["solves"][0]["title"] == "冒烟测试题")

    # 题目已解状态标记
    r = c.get("/api/challenges", headers=H_USER)
    card = next(x for x in r.json() if x["id"] == new_id)
    check("题目列表-已解标记", card["solved_by_me"] is True)

    # 管理员统计
    r = c.get("/api/admin/stats", headers=H_ADMIN)
    check("管理统计卡", r.status_code == 200 and r.json()["challenge_total"] >= 9)

    # 公告 / 文章按类型拆分
    r = c.post("/api/admin/articles", json={
        "title": "冒烟测试公告",
        "content": "公告内容",
        "type": "announcement",
    }, headers=H_ADMIN)
    check("管理员发布公告", r.status_code == 200)
    announcement_id = r.json()["id"]
    r = c.post("/api/admin/articles", json={
        "title": "冒烟测试文章",
        "content": "文章内容",
        "type": "article",
    }, headers=H_ADMIN)
    check("管理员发布文章", r.status_code == 200)

    r = c.get("/api/articles?type=announcement")
    announcements = r.json()
    check(
        "只返回公告",
        r.status_code == 200
        and len(announcements) == 1
        and announcements[0]["title"] == "冒烟测试公告",
    )
    r = c.get("/api/articles?type=article")
    articles = r.json()
    check(
        "只返回文章",
        r.status_code == 200
        and len(articles) == 1
        and articles[0]["title"] == "冒烟测试文章",
    )

    r = c.get("/api/notifications", headers=H_USER)
    check(
        "普通用户收到公告通知",
        r.status_code == 200
        and any(
            item["type"] == "announcement_published"
            and item["related_article_id"] == announcement_id
            for item in r.json()
        ),
    )

    r = c.delete(f"/api/admin/articles/{announcement_id}", headers=H_ADMIN)
    check("管理员删除公告", r.status_code == 200 and r.json()["success"] is True)
    r = c.get("/api/articles?type=announcement")
    check("删除后公告不再返回", r.status_code == 200 and len(r.json()) == 0)

    # 用户提交题目 -> 管理员通知/审核 -> 用户反馈通知
    r = c.post("/api/challenges/submit", json={
        "title": "用户投稿题",
        "category": "Web安全",
        "difficulty": 2,
        "points": 120,
        "description": "投稿流程测试",
        "flag": "flag{user_submission}",
    }, headers=H_USER)
    check(
        "用户提交题目进入待审核",
        r.status_code == 201 and r.json()["status"] == "pending",
    )
    submitted_id = r.json()["id"]

    r = c.get("/api/notifications", headers=H_ADMIN)
    check(
        "管理员收到投稿通知",
        r.status_code == 200
        and any(
            item["type"] == "challenge_submitted"
            and item["related_challenge_id"] == submitted_id
            for item in r.json()
        ),
    )

    r = c.get("/api/admin/challenges?status=pending", headers=H_ADMIN)
    check(
        "审核列表包含投稿",
        r.status_code == 200 and any(item["id"] == submitted_id for item in r.json()),
    )

    r = c.put(
        f"/api/admin/challenges/{submitted_id}",
        json={"status": "published"},
        headers=H_ADMIN,
    )
    check("管理员通过投稿", r.status_code == 200 and r.json()["status"] == "published")

    r = c.get("/api/notifications", headers=H_USER)
    check(
        "用户收到审核通过通知",
        r.status_code == 200
        and any(
            item["type"] == "challenge_approved"
            and item["related_challenge_id"] == submitted_id
            for item in r.json()
        ),
    )

    # 收藏题目
    r = c.post(f"/api/users/me/favorites/{new_id}/toggle", headers=H_USER)
    check("用户收藏题目", r.status_code == 200 and r.json()["favorited"] is True)
    r = c.get(f"/api/challenges/{new_id}", headers=H_USER)
    check("题目详情显示已收藏", r.json().get("favorited_by_me") is True)
    r = c.get("/api/users/me/favorites", headers=H_USER)
    check(
        "收藏列表包含题目",
        r.status_code == 200 and any(item["id"] == new_id for item in r.json()),
    )
    r = c.post(f"/api/users/me/favorites/{new_id}/toggle", headers=H_USER)
    check("用户取消收藏", r.status_code == 200 and r.json()["favorited"] is False)

    now = datetime.now()
    r = c.get(
        f"/api/users/me/activity/monthly?year={now.year}&month={now.month}",
        headers=H_USER,
    )
    activity = r.json()
    check(
        "月度做题活跃度",
        r.status_code == 200
        and activity["days"] >= 28
        and activity["total"] >= 1
        and len(activity["daily"]) == activity["days"],
    )

    r = c.get(
        f"/api/users/me/activity/yearly?year={now.year}",
        headers=H_USER,
    )
    yearly = r.json()
    check(
        "年度做题活跃度",
        r.status_code == 200
        and len(yearly["months"]) == 12
        and yearly["total"] >= 1
        and sum(len(month["daily"]) for month in yearly["months"]) >= 365,
    )

print(f"\n结果: {sum(OK)}/{len(OK)} 通过")
if not all(OK):
    raise SystemExit(1)
