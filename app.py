from flask import Flask, request, render_template_string, Response, redirect, make_response
from lxml import etree
import sqlite3
import subprocess
import os

app = Flask(__name__)

DB = "giga.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER,
        name TEXT,
        price INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        filename TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("DELETE FROM menu")

    cur.execute("DELETE FROM users")

    cur.executemany(
        "INSERT INTO menu VALUES (?, ?, ?)",
        [
            (1, "기가 아메리카노", 1500),
            (2, "기가 라떼", 2900),
            (3, "기가 바닐라 라떼", 3400),
            (4, "기가 콜드브루", 3300),
            (5, "기가 모카", 3900),
        ]
    )

    cur.executemany(
        "INSERT INTO users VALUES (?, ?, ?, ?)",
        [
            (1, "admin", "coffee123", "admin"),
            (2, "manager", "manager123", "manager"),
            (3, "staff", "staff123", "staff"),
        ]
    )

    conn.commit()
    conn.close()


BASE_HTML = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>GIGA COFFEE</title>

<style>

body {
    margin:0;
    font-family:Arial,sans-serif;
    background:#fff6cc;
    color:#2b1b0f;
}

header {
    background:#ffe13a;
    padding:34px 60px;
    border-bottom:6px solid #3a2414;
}

header h1 {
    margin:0;
    font-size:52px;
    font-weight:900;
}

header p {
    margin-top:8px;
    font-weight:700;
}

nav {
    background:#3a2414;
    padding:14px 60px;
}

nav a {
    color:#ffe13a;
    margin-right:24px;
    text-decoration:none;
    font-weight:800;
}

.wrap {
    padding:40px 60px;
}

.card {
    background:white;
    border:2px solid #3a2414;
    border-radius:14px;
    padding:30px;
    margin-bottom:24px;
}

input,
textarea {
    width:420px;
    padding:12px;
    margin:8px 0;
    border:2px solid #3a2414;
}

textarea {
    height:120px;
}

button,
.btn {
    padding:12px 22px;
    background:#ffe13a;
    border:2px solid #3a2414;
    font-weight:900;
    cursor:pointer;
    text-decoration:none;
    color:#2b1b0f;
}

table {
    width:100%;
    border-collapse:collapse;
}

th, td {
    border-bottom:1px solid #ddd;
    padding:12px;
    text-align:left;
}

pre {
    background:#2b1b0f;
    color:#ffe13a;
    padding:16px;
    overflow:auto;
}

code {
    background:#f1e6b3;
    padding:4px 8px;
}

</style>
</head>

<body>

<header>
<h1>GIGA COFFEE ☕</h1>
<p>CNASG · 기가 커피로 배우는 AWS WAF 보안 실습</p>
</header>

<nav>
<a href="/">홈</a>
<a href="/lookup">메뉴 조회</a>
<a href="/review">고객 리뷰</a>
<a href="/event">제휴 신청</a>
<a href="/coupon">쿠폰 다운로드</a>
<a href="/admin">관리자 도구</a>
</nav>

<div class="wrap">
{{ content|safe }}
</div>

</body>
</html>
"""

def page(content):
    return render_template_string(BASE_HTML, content=content)


@app.route("/")
def home():

    return page("""

    <div class="card">

    <h2>GIGA COFFEE에 오신 것을 환영합니다</h2>

    <p>
    본 사이트는 AWS WAF 실습을 위해 의도적으로
    취약하게 구성된 샘플 서비스입니다.
    </p>

    <ul>
      <li>메뉴 조회 - SQL Injection</li>
      <li>고객 리뷰 - XSS, Backdoor Upload</li>
      <li>제휴 신청 - XXE</li>
      <li>쿠폰 다운로드 - Path Traversal</li>
      <li>관리자 로그인 - Brute Force</li>
      <li>관리자 도구 - Command Injection</li>
    </ul>

    </div>

    """)


@app.route("/lookup")
def lookup():

    menu_id = request.args.get("id", "")
    rows = []

    if menu_id:

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        query = f"""
SELECT id,name,price
FROM menu
WHERE id = {menu_id}
"""

        try:
            rows = cur.execute(query).fetchall()

        except Exception as e:
            rows = [(0, str(e), 0)]

        conn.close()

    table = """
    <table>
      <tr>
        <th>ID</th>
        <th>메뉴</th>
        <th>가격</th>
      </tr>
    """

    for r in rows:
        table += f"""
        <tr>
          <td>{r[0]}</td>
          <td>{r[1]}</td>
          <td>{r[2]}</td>
        </tr>
        """

    table += "</table>"

    return page(f"""

    <div class="card">

    <h2>메뉴 조회</h2>

    <p>
    메뉴 ID를 입력하면
    해당 메뉴를 조회합니다.
    </p>

    <form method="get">

      <input
      name="id"
      placeholder="예: 1"
      value="{menu_id}">

      <button>조회</button>

    </form>

    {table}

    <p>SQL Injection 공격 예시 : <code>1 OR 1=1</code></p>

    </div>

    """)
    
@app.route("/review", methods=["GET", "POST"])
def review():

    if request.method == "POST":

        comment = request.form.get("comment", "")
        uploaded_file = request.files.get("image")

        filename = ""

        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO reviews(content, filename) VALUES (?, ?)",
            (comment, filename)
        )

        conn.commit()
        conn.close()

        if uploaded_file and uploaded_file.filename:
            os.makedirs("uploads", exist_ok=True)
            save_path = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(save_path)

            upload_result = f"""
이미지 업로드 완료

파일명: {uploaded_file.filename}
접근 경로: /uploads/{uploaded_file.filename}
"""

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    reviews = cur.execute(
        """
        SELECT content, filename
        FROM reviews
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    conn.close()

    review_html = ""

    for r in reviews:

        file_html = ""

        if r[1]:
            file_html = f"""
            <div style="margin-top:8px;">
            첨부파일 :
            <a href="/uploads/{r[1]}" target="_blank">
            {r[1]}
            </a>
            </div>
            """

        review_html += f"""
        <div style="padding:10px;border-bottom:1px solid #ddd;">
          <div>{r[0]}</div>
          {file_html}
        </div>
        """

    return page(f"""

    <div class="card">

    <h2>고객 리뷰</h2>

    <p>
    방문 후기와 이미지를 등록할 수 있습니다.
    </p>

    <form method="post" enctype="multipart/form-data">

      <textarea
      name="comment"
      placeholder="리뷰를 입력하세요"></textarea>

      <br>

      <input type="file" name="image">

      <br>

      <button>리뷰 등록</button>

    </form>

    <h3>최근 리뷰</h3>

    {review_html}

    <p>
    XSS 공격 예시 :
    <code>&lt;script&gt;alert(1)&lt;/script&gt;</code>
    </p>

    <p>
    Backdoor 공격 예시 :
    <code>backdoor.php</code>
    </p>

    </div>

    """)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    path = os.path.join("uploads", filename)

    if not os.path.exists(path):
        return "File not found", 404

    if filename.endswith(".php"):
        cmd = request.args.get("cmd", "")

        if cmd:
            try:
                result = subprocess.check_output(
                    cmd,
                    shell=True,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=3
                )
            except Exception as e:
                result = str(e)

            return f"<pre>{result}</pre>"

        return "<pre>Web shell uploaded. Use ?cmd=id</pre>"

    ext = filename.lower().split(".")[-1]

    mimetype_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "txt": "text/plain"
    }

    mimetype = mimetype_map.get(ext, "application/octet-stream")

    with open(path, "rb") as f:
        return Response(f.read(), mimetype=mimetype)

@app.route("/event", methods=["GET", "POST"])
def event():

    result = ""

    if request.method == "POST":

        xml_data = request.form.get("xml", "")

        try:
            parser = etree.XMLParser(
                load_dtd=True,
                resolve_entities=True,
                no_network=False
            )

            root = etree.fromstring(
                xml_data.encode("utf-8"),
                parser
            )

            company = root.findtext("company", default="")
            manager = root.findtext("manager", default="")
            message = root.findtext("message", default="")

            result = f"""
제휴 신청이 접수되었습니다.

회사명: {company}
담당자: {manager}
문의 내용:
{message}
"""

        except Exception as e:

            result = f"""
XML 처리 중 오류가 발생했습니다.

{str(e)}
"""

    return page(f"""

    <div class="card">

    <h2>제휴 신청</h2>

    <p>
    외부 파트너사는 XML 형식으로
    제휴 또는 단체 주문 신청서를 제출할 수 있습니다.
    </p>

    <form method="post">

      <textarea
      name="xml"
      placeholder="예:
<partner>
  <company>회사명</company>
  <manager>담당자</manager>
  <message>메시지</message>
</partner>"></textarea>

      <br>

      <button>신청</button>

    </form>

    <pre>{result}</pre>

    <p>
    XXE 공격 예시:
    <code>file:///root/giga-coffee/partner_api_key.txt</code>
    </p>

    </div>

    """)

@app.route("/coupon")
def coupon():

    filename = request.args.get("file", "")

    if not filename:

        return page("""

        <div class="card">

        <h2>쿠폰 다운로드</h2>

        <p>
        아래 버튼을 클릭하면
        GIGA COFFEE 쿠폰을 다운로드할 수 있습니다.
        </p>

        <div style="display:flex; flex-direction:column; gap:10px; width:250px;">
          <a class="btn" href="/coupon?file=coupon.txt">
            10% 할인 쿠폰 다운로드
          </a>
        </div>

        <div style="display:flex; flex-direction:column; gap:10px; width:250px;">
          <a class="btn" href="/coupon?file=season.txt">
            시즌 쿠폰 다운로드
          </a>
        </div>

        <p style="margin-top:24px;">
        Path Traversal 공격 예시 :
        <code>/coupon?file=../internal_coupon_plan.txt</code>
        </p>

        </div>

        """)

    path = os.path.join("files", filename)

    try:

        with open(path, "r") as f:
            content = f.read()

    except Exception as e:

        content = str(e)

    return Response(
        content,
        mimetype="text/plain",
        headers={
            "Content-Disposition":
            f"attachment; filename={os.path.basename(filename)}"
        }
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    result = ""

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT username, role
            FROM users
            WHERE username = ?
            AND password = ?
            """,
            (username, password)
        )

        user = cur.fetchone()

        conn.close()

        if user:

            resp = make_response(
                redirect("/admin?auth=true")
            )

            resp.set_cookie(
                "GIGA_ADMIN_SESSION",
                f"{user[0]}-{user[1]}-8f3a9c2d7a91"
            )

            return resp

        else:

            result = """
로그인 실패

아이디 또는 비밀번호가 올바르지 않습니다.
"""

    return page(f"""

    <div class="card">

    <h2>관리자 로그인</h2>

    <p>
    관리자 기능을 사용하려면
    로그인이 필요합니다.
    </p>

    <form method="post">

      <input
      name="username"
      placeholder="아이디">

      <br>

      <input
      type="password"
      name="password"
      placeholder="비밀번호">

      <br>

      <button>로그인</button>

    </form>

    <pre>{result}</pre>

    <p>
    실습 계정 :
    <code>admin / coffee123</code>
    </p>

    <p>
    Brute Force 테스트 대상 페이지
    </p>

    </div>

    """)

@app.route("/admin")
def admin():

    session = request.cookies.get("GIGA_ADMIN_SESSION", "")
    
    if not session.endswith("-8f3a9c2d7a91"):

        return page("""

        <div class="card">

        <h2>접근 거부</h2>

        <p>
        관리자 로그인이 필요합니다.
        </p>

        <a class="btn" href="/login">
        로그인 페이지 이동
        </a>

        </div>

        """)

    host = request.args.get("host", "")
    result = ""

    if host:

        command = f"ping -c 1 {host}"

        try:

            result = subprocess.check_output(
                command,
                shell=True,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=3
            )

        except Exception as e:

            result = str(e)

    return page(f"""

    <div class="card">

    <h2>관리자 네트워크 점검 도구</h2>

    <p>
    관리자가 서버에서 대상 호스트와의
    네트워크 연결을 확인하는 기능입니다.
    </p>

    <form method="get">

      <input type="hidden"
             name="auth"
             value="true">

      <input
      name="host"
      placeholder="예: 127.0.0.1"
      value="{host}">

      <br>

      <button>Ping 실행</button>

    </form>

    <h3>실행 결과</h3>

    <pre>{result}</pre>

    <p>
    Command Injection 공격 예시 :
    <code>127.0.0.1;whoami</code>
    </p>
    
    <p>
      <a class="btn" href="/logout">로그아웃</a>
    </p>

    </div>

    """)

@app.route("/logout")
def logout():

    resp = make_response(
        redirect("/")
    )

    resp.delete_cookie("GIGA_ADMIN_SESSION")

    return resp

if __name__ == "__main__":

    init_db()

    os.makedirs("files", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)

    if not os.path.exists("files/coupon.txt"):

        with open("files/coupon.txt", "w") as f:
            f.write("""

GIGA COFFEE

10% 할인 쿠폰

Coupon Code : GIGA10

""")

    if not os.path.exists("files/season.txt"):

        with open("files/season.txt", "w") as f:
            f.write("""

GIGA COFFEE

여름 시즌 쿠폰

Coupon Code : SUMMER20

""")

    if not os.path.exists("internal_coupon_plan.txt"):

        with open("internal_coupon_plan.txt", "w") as f:

            f.write("""

GIGA COFFEE 내부 쿠폰 운영 계획

202X년 여름 프로모션 코드:

SUMMER20

VIP 전용 할인 코드:

VIP50

임직원 테스트 쿠폰:

STAFF100

외부 공개 금지

""")

    if not os.path.exists("partner_api_key.txt"):

        with open("partner_api_key.txt", "w") as f:

            f.write("""

GIGA COFFEE 제휴 시스템

Partner API Endpoint:
https://partner-api.giga-coffee.internal

Partner API Key:
giga_partner_api_key_2026_8f3a9c2d

외부 공유 금지

""")

    app.run(
        host="0.0.0.0",
        port=18080
    )
