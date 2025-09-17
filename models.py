from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))  # can be empty initially
    password = db.Column(db.String(100), default='123456')  # initial password
    is_class_teacher = db.Column(db.Boolean, default=False)
    grade_assigned = db.Column(db.String(50))
    subjects = db.Column(db.String(200))
    syllabus_coverage = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)  # admin column

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), db.ForeignKey('staff.staff_id'))
    staff = db.relationship('Staff', backref='attendances', lazy=True)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime)
    logout_reason = db.Column(db.String(200))
