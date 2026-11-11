import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def build_db_url() -> str:
    user = os.getenv("DB_USER", "app")
    password = os.getenv("DB_PASSWORD", "changeme")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "visits_db")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"


class Visit(db.Model):
    __tablename__ = "visits"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=False)