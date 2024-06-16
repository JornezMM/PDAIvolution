from models.patient import Patient
from models.doctor import Doctor
from models.admin import Admin

from flask import render_template
from werkzeug.security import generate_password_hash
import datetime
REGISTER="register.html"
def register_patient(form):
    username = form["username"]
    password = form["password"]
    first_name = form["name"]
    last_name = form["last_name"]
    birth_date = datetime.datetime.strptime(form["birth_date"], "%Y-%m-%d").date()
    gender = form["gender"]
    doctor_id = form["doctor_id"]
    handedness = form["handedness"]
    hashed_password = generate_password_hash(password)
    return Patient(
        username=username,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        gender=gender,
        doctor_id=doctor_id,
        handedness=handedness,
    )


def register_doctor(form):
    username = form["username"]
    if Doctor.query.filter_by(username=username).first():
        return render_template(REGISTER, error=True)
    password = form["password"]
    first_name = form["name"]
    last_name = form["last_name"]
    hashed_password = generate_password_hash(password)
    return Doctor(
        username=username,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
    )


def register_admin(form):
    username = form["username"]
    if Admin.query.filter_by(username=username).first():
        return render_template(REGISTER, error=True)
    password = form["password"]
    first_name = form["name"]
    last_name = form["last_name"]
    hashed_password = generate_password_hash(password)
    return Admin(
        username=username,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
    )