import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
DB_PATH = Path("/tmp/quicksum.db")


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


init_db()


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok"})


@app.post("/api/summarize")
def summarize():
    payload = request.get_json(silent=True) or {}
    content = (payload.get("content") or "").strip()
    input_type = payload.get("input_type") or "text"
    topics = payload.get("topics") or []

    if not content:
        return jsonify({"error": "Content is required."}), 400

    topic_text = ", ".join(topics) if topics else "Tổng quát"
    intro = (
        f"Bạn đã gửi {'một đường dẫn' if input_type == 'url' else 'một đoạn văn bản'} "
        f"với chủ đề: {topic_text}."
    )

    key_points = [
        "Hệ thống nhận diện nội dung đầu vào và chuẩn hóa dữ liệu.",
        "Các chủ đề ưu tiên được dùng để gợi ý trọng tâm tóm tắt.",
        "Kết quả trả về gồm ý chính và bản tóm tắt ngắn gọn.",
        "API sẵn sàng tích hợp với mô hình AI trong các bước tiếp theo.",
    ]

    summary = (
        f"{intro} Hiện tại bản demo tạo ra nội dung tóm tắt mẫu để phục vụ việc "
        "triển khai giao diện. Bạn có thể thay thế phần này bằng mô hình AI hoặc dịch vụ "
        "tóm tắt thực tế khi triển khai trên Vercel."
    )

    stats = "⚡ Bạn vừa tiết kiệm được 4 phút đọc. Tỉ lệ tóm tắt: 20% so với gốc."

    return jsonify({"stats": stats, "key_points": key_points, "summary": summary})


@app.post("/api/register")
def register():
    payload = request.get_json(silent=True) or {}
    full_name = (payload.get("full_name") or "").strip()
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not full_name or not username or not password:
        return jsonify({"error": "Vui lòng nhập đầy đủ họ tên, tên đăng nhập và mật khẩu."}), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as connection:
            connection.execute(
                "INSERT INTO users (full_name, username, password_hash) VALUES (?, ?, ?)",
                (full_name, username, password_hash),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác."}), 409

    return jsonify({"message": "Đăng ký thành công."}), 201


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Vui lòng nhập tên đăng nhập và mật khẩu."}), 400

    with get_db_connection() as connection:
        user = connection.execute(
            "SELECT full_name, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không đúng."}), 401

    return jsonify({"message": "Đăng nhập thành công.", "full_name": user["full_name"]})


if __name__ == "__main__":
    app.run(debug=True)
