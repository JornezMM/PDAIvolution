from flask_login import UserMixin
from .base import db

class Patient(UserMixin, db.Model):
    def __repr__(self):
        return f"<Patient {self.username}>"

    def get_id(self):
        return self.id

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    handedness = db.Column(db.Enum("right", "left"), nullable=False)
    gender = db.Column(db.Enum("M", "F"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
