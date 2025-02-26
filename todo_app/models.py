from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow().replace(tzinfo=pytz.UTC))
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    user = db.relationship('User', back_populates='tasks')

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    tasks = db.relationship('Task', back_populates='user')

def convert_to_ist(utc_time):
    if utc_time.tzinfo is None:
        utc_time = pytz.utc.localize(utc_time)
    ist = pytz.timezone('Asia/Kolkata')
    return utc_time.astimezone(ist)
