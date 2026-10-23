"""初始化：建表 + 创建默认管理员 + 种子题目。"""
from sqlalchemy import inspect, text

from .database import Base, SessionLocal, engine
from .models import Challenge, User
from .security import hash_password

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_EMAIL = "admin@cyberrange.local"

SEED_CHALLENGES: list[dict] = [
    {
        "title": "栈溢出入门",
        "category": "二进制漏洞",
        "difficulty": 2,
        "points": 300,
        "description": "一个经典的回调函数栈溢出。程序读取 64 字节输入到 16 字节缓冲区，未做长度检查。\n\n请利用栈溢出覆盖返回地址，跳到 win() 函数读取 flag。\n\n附件：stack0",
        "attachment": "stack0.zip",
        "flag": "flag{st4ck_0v3rfl0w_1ntro}",
    },
    {
        "title": "RSA 小指数攻击",
        "category": "密码学",
        "difficulty": 3,
        "points": 200,
        "description": "题目给了一组 RSA 公钥，其中 e = 3，并且明文 m 很小（小于 n 的 1/3）。\n\n请利用低加密指数攻击：密文 c = m^3，直接对 c 开三次方即可还原明文。\n\n附件：rsa_small_e.py",
        "attachment": "rsa_small_e.zip",
        "flag": "flag{sm4ll_e_a7tack}",
    },
    {
        "title": "Base64 隐写",
        "category": "数字取证",
        "difficulty": 1,
        "points": 100,
        "description": "一段 Base64 字符串里隐藏了额外信息。Base64 编码时末尾通常有 0-2 位冗余比特，隐写利用这些比特传递消息。\n\n请提取出隐藏的 flag。",
        "attachment": "b64_stego.txt",
        "flag": "flag{b64_st3g0}",
    },
    {
        "title": "HTTP 报文分析",
        "category": "流量分析",
        "difficulty": 2,
        "points": 250,
        "description": "给定一份 HTTP 抓包文件（pcap），其中某次 GET 请求的 URL 参数里藏着 flag。\n\n请用流量分析工具定位可疑请求，还原出 flag。",
        "attachment": "http_capture.pcap",
        "flag": "flag{http_p4r4m_l34k}",
    },
    {
        "title": "SQL 注入入门",
        "category": "Web安全",
        "difficulty": 2,
        "points": 200,
        "description": "登录接口对 username 字段存在 SQL 注入。\n\n使用万能密码绕过登录即可拿到管理员会话与 flag。",
        "attachment": "sqli_app.zip",
        "flag": "flag{sqli_0r_1_1_1}",
    },
    {
        "title": "UPX 脱壳",
        "category": "逆向工程",
        "difficulty": 2,
        "points": 150,
        "description": "目标程序用 UPX 加壳。请先脱壳，再用 IDA/Ghidra 定位关键比较函数，得到 flag。\n\n附件：packed_elf",
        "attachment": "packed_elf.zip",
        "flag": "flag{upx_1s_3asy}",
    },
    {
        "title": "凯撒移位",
        "category": "密码学",
        "difficulty": 1,
        "points": 100,
        "description": "一段被凯撒密码加密的字符串。偏移量未知，请暴力枚举 25 个偏移，找到语义通顺的明文。",
        "attachment": "",
        "flag": "flag{ca3s4r_brut3f0rc3}",
    },
    {
        "title": "格式化字符串漏洞",
        "category": "二进制漏洞",
        "difficulty": 3,
        "points": 400,
        "description": "程序存在格式化字符串漏洞，可将任意地址写入。\n\n请利用 %n 覆写 GOT 表项劫持控制流，读取 flag。",
        "attachment": "fmt_str.zip",
        "flag": "flag{f0rm4t_str1ng_wr1te}",
    },
    {
        "title": "堆溢出 Use-After-Free",
        "category": "二进制漏洞",
        "difficulty": 3,
        "points": 300,
        "description": "程序在释放堆块后仍保留悬挂指针，随后对该悬空指针进行读写（Use-After-Free）。\n\n请通过堆重叠构造任意地址读写，进而泄露并覆写目标内存获取 flag。",
        "attachment": "heap_uaf.zip",
        "flag": "flag{heap_uaf_0v3r1ap}",
    },
    {
        "title": "AES 差分分析",
        "category": "密码学",
        "difficulty": 4,
        "points": 350,
        "description": "一段被简化 AES 加密的密文。密钥空间被刻意缩小，可通过差分/蛮力方式还原密钥。\n\n请还原密钥后解出明文 flag。",
        "attachment": "aes_diff.zip",
        "flag": "flag{a3s_diff_crypt}",
    },
    {
        "title": "DNS 隧道检测",
        "category": "流量分析",
        "difficulty": 2,
        "points": 250,
        "description": "给定一份 DNS 抓包文件，其中部分子域名字段携带编码后的数据（DNS 隧道）。\n\n请提取被编码的子域名字段，还原出 flag。",
        "attachment": "dns_tunnel.pcap",
        "flag": "flag{dns_tunn3l_4113rt}",
    },
]


def _ensure_columns() -> None:
    """轻量迁移：给已存在的表补上后加的列（本项目没有引入 Alembic）。"""
    wanted: dict[str, dict[str, str]] = {
        "competition_challenges": {
            "points": "INTEGER NOT NULL DEFAULT 100",
            "solved_count": "INTEGER NOT NULL DEFAULT 0",
        },
        "notifications": {
            "related_article_id": "INTEGER",
        },
    }
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in wanted.items():
            if table not in tables:
                continue
            existing = {col["name"] for col in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_columns()

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == ADMIN_USERNAME).first():
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()

        existing_titles = {c.title for c in db.query(Challenge).all()}
        for data in SEED_CHALLENGES:
            if data["title"] not in existing_titles:
                db.add(Challenge(author=ADMIN_USERNAME, status="published", **data))
        db.commit()
    finally:
        db.close()
