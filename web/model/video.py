from .base import db

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    hand = db.Column(db.Enum("left", "right"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    video_data = db.Column(db.LargeBinary, nullable=False)
    amplitude = db.Column(db.Integer, nullable=False)
    slowness = db.Column(db.Integer, nullable=False)
