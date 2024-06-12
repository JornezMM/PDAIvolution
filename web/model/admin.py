from flask_login import UserMixin
from .base import db

class Admin(UserMixin, db.Model):
    def __repr__(self):
        return f"<Admin {self.username}>"

    def get_id(self):
        return self.id

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
