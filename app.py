from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request

from models import db, Visit, build_db_url

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = build_db_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Создание таблицы visits при старте приложения
with app.app_context():
    db.create_all()


@app.route("/hello", methods=["GET"])
def hello():
    # 1. Текущее время
    now = datetime.utcnow()

    # 2. IP-адрес клиента
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.remote_addr or "unknown"

    # 3. Сохраняем запись в таблицу Visit
    visit = Visit(timestamp=now, ip_address=client_ip)
    db.session.add(visit)
    db.session.commit()

    # 4. Возвращаем 200 OK с телом «Hello»
    return "Hello", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)