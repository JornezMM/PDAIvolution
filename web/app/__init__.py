from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_font_awesome import FontAwesome
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.base import db
from models.admin import Admin
from models.doctor import Doctor
from models.patient import Patient
from models.medicine import Medicine
from models.patient_medicine import PatientMedicine
from models.video import Video
from flask_wtf.csrf import CSRFProtect
import datetime
from dotenv import load_dotenv, dotenv_values
from paddel.preprocessing.input.features import extract_video_features
from tempfile import NamedTemporaryFile
import os
from controllers.admin_controllers import (
    register_patient,
    register_doctor,
    register_admin,
)


HOME = "home.html"
LOGIN = "login.html"
REDIRECTHOME = "home"
REGISTER = "register.html"
MODIFY = "modify.html"
SECRET_KEY="SECRET_KEY"

def create_app():
    app = Flask(__name__)
    load_dotenv()
    config = dotenv_values(".env")
    csrf = CSRFProtect()
    csrf.init_app(app)
    FontAwesome(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
    app.config[SECRET_KEY] = config[SECRET_KEY]
    login_manager = LoginManager()
    login_manager.init_app(app)

    db.init_app(app)

    def create_default_admin():
        if not Admin.query.first():
            default_admin = Admin(
                username="admin",
                password=config["DEFAULT_PASSWORD"],
                first_name="Default",
                last_name="Admin",
            )
            db.session.add(default_admin)
        if not Medicine.query.first():
            medicine1 = Medicine(name="Medicine 1")
            medicine2 = Medicine(name="Medicine 2")
            medicine3 = Medicine(name="Medicine 3")
            db.session.add(medicine1)
            db.session.add(medicine2)
            db.session.add(medicine3)
        db.session.commit()

    with app.app_context():
        db.create_all()
        create_default_admin()

    @login_manager.user_loader
    def loader_user(user_id):
        """Carga el usuario desde la base de datos"""
        if session.get("usertype") is None:
            return None
        user_type = session.get("usertype")
        if user_type == "patient":
            return Patient.query.filter_by(id=user_id).first()
        elif user_type == "doctor":
            return Doctor.query.filter_by(id=user_id).first()
        elif user_type == "admin":
            return Admin.query.filter_by(id=user_id).first()
        else:
            return None

    @app.route("/")
    def index():
        return render_template("home.html")

    @app.route("/home/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for(session.get("usertype")))
        return redirect(url_for("login_get"))

    @app.route("/login/", methods=["GET"])
    def login_get():
        if current_user.is_authenticated:
            return redirect(url_for(REDIRECTHOME))
        return render_template(LOGIN)

    @app.route("/login/", methods=["POST"])
    def login_post():
        if current_user.is_authenticated:
            return redirect(url_for(REDIRECTHOME))
        username = request.form["username"]
        password = request.form["password"]
        user_type = request.form["role"]
        if user_type == "patient":
            user = Patient.query.filter_by(username=username).first()
        elif user_type == "doctor":
            user = Doctor.query.filter_by(username=username).first()
        elif user_type == "admin":
            user = Admin.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["usertype"] = user_type
            session["first_name"] = user.first_name
            login_user(user)
            return redirect(url_for(REDIRECTHOME))
        else:
            return render_template(LOGIN, error=True)

    @app.route("/logout/")
    def logout():
        logout_user()
        session.clear()
        return redirect(url_for(REDIRECTHOME))

    @app.route("/register/", methods=["GET"])
    def register_get():
        if current_user.is_authenticated and session.get("usertype") == "admin":
            doctors = Doctor.query.all()
            return render_template(REGISTER, doctorNames=doctors)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/register/", methods=["POST"])
    def register_post():
        if current_user.is_authenticated and session.get("usertype") == "admin":
            username = request.form["username"]
            user_type = request.form["user_type"]
            if (
                user_type == "patient"
                and not Patient.query.filter_by(username=username).first()
            ):
                db.session.add(register_patient(request.form))
                db.session.commit()
            elif (
                user_type == "doctor"
                and not Doctor.query.filter_by(username=username).first()
            ):
                db.session.add(register_doctor(request.form))
                db.session.commit()
            elif (
                user_type == "admin"
                and not Admin.query.filter_by(username=username).first()
            ):
                db.session.add(register_admin(request.form))
                db.session.commit()
            else:
                return render_template(REGISTER, error=True)
            return redirect(url_for("admin"))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/admin/", methods=["GET"])
    def admin():
        if current_user.is_authenticated and session.get("usertype") == "admin":
            doctors = Doctor.query.all()
            patients = Patient.query.all()
            admins = Admin.query.all()
            return render_template(
                "admin.html",
                doctors=doctors,
                patients=patients,
                admins=admins,
                admin_username=current_user.username,
            )
        return redirect(url_for(REDIRECTHOME))

    @app.route("/modify/<string:user>", methods=["GET"])
    def modify_get(user):
        if current_user.is_authenticated and session.get("usertype") == "admin":
            splited_user = user.split("-")
            username = splited_user[1]
            match splited_user[0].lower():
                case "doctor":
                    doctor = Doctor.query.filter_by(username=username).first()
                    return render_template(MODIFY, user=doctor, user_type="doctor")
                case "patient":
                    patient = Patient.query.filter_by(username=username).first()
                    doctor = Doctor.query.filter_by(id=patient.doctor_id).first()
                    doctors = Doctor.query.all()
                    return render_template(
                        MODIFY,
                        user=patient,
                        user_type="patient",
                        doctors=doctors,
                        doctor=doctor,
                    )
                case "admin":
                    admin = Admin.query.filter_by(username=username).first()
                    return render_template(MODIFY, user=admin, user_type="admin")
        return redirect(url_for(REDIRECTHOME))

    @app.route("/modify/<string:user>", methods=["POST"])
    def modify_post(user):
        old_username = user.split("-")[1]
        user_type = user.split("-")[0]
        username = request.form["username"]
        password = request.form["password"]
        first_name = request.form["name"]
        last_name = request.form["last_name"]
        if user_type == "patient":
            birth_date = datetime.datetime.strptime(
                request.form["birth_date"], "%Y-%m-%d"
            ).date()
            doctor_id = request.form["doctor_id"]
            patient = Patient.query.filter_by(username=old_username).first()
            patient.username = username
            patient.first_name = first_name
            patient.last_name = last_name
            patient.birth_date = birth_date
            patient.doctor_id = doctor_id
            if password:
                patient.password = generate_password_hash(password)
            db.session.commit()
        elif user_type == "doctor":
            doctor = Doctor.query.filter_by(username=old_username).first()
            doctor.username = username
            doctor.first_name = first_name
            doctor.last_name = last_name
            if password:
                doctor.password = generate_password_hash(password)
            db.session.commit()
        elif user_type == "admin":
            admin = Admin.query.filter_by(username=old_username).first()
            admin.username = username
            admin.first_name = first_name
            admin.last_name = last_name
            if password:
                admin.password = generate_password_hash(password)
            db.session.commit()
        return redirect(url_for("admin"))

    @app.route("/delete/<string:user>", methods=["GET"])
    def delete(user):
        if current_user.is_authenticated and session.get("usertype") == "admin":
            user_type = user.split("-")[0]
            username = user.split("-")[1]
            if user_type == "patient":
                patient = Patient.query.filter_by(username=username).first()
                medicines = PatientMedicine.query.filter_by(patient_id=patient.id).all()
                for medicine in medicines:
                    db.session.delete(medicine)
                videos = Video.query.filter_by(patient_id=patient.id).all()
                for video in videos:
                    db.session.delete(video)
                db.session.delete(patient)
                db.session.commit()
            elif user_type == "doctor":
                doctor = Doctor.query.filter_by(username=username).first()
                if get_doctor_patients(doctor.id):
                    return "<script>window.location.href='/admin/';alert('No se puede eliminar un doctor con pacientes asignados.');</script>"
                db.session.delete(doctor)
                db.session.commit()
            elif user_type == "admin":
                if username == current_user.username:
                    return "<script>window.location.href='/admin/';alert('No se puede eliminar el usuario actual.');</script>"
                admin = Admin.query.filter_by(username=username).first()
                db.session.delete(admin)
                db.session.commit()
            return redirect(url_for("admin"))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/patient/", methods=["GET"])
    def patient():
        if current_user.is_authenticated and session.get("usertype") == "patient":
            user = Patient.query.filter_by(id=current_user.id).first()
            age = datetime.datetime.now().year - user.birth_date.year - 1
            medicine_name = None
            actual_medicine = None
            actual_medicine = (
                PatientMedicine.query.filter_by(patient_id=user.id)
                .where(PatientMedicine.end_date is None)
                .first()
            )
            if actual_medicine:
                medicine_name = (
                    Medicine.query.filter_by(id=actual_medicine.medicine_id)
                    .firts()
                    .name
                )
            if (
                datetime.datetime.now().month > user.birth_date.month
                and datetime.datetime.now().day > user.birth_date.day
            ):
                age += 1
            doctor = Doctor.query.filter_by(id=user.doctor_id).first()
            return render_template(
                "patient.html",
                user=user,
                age=age,
                actual_medicine=actual_medicine,
                medicine_name=medicine_name,
                doctor=doctor,
            )
        return redirect(url_for(REDIRECTHOME))

    @app.route("/doctor/", methods=["GET"])
    def doctor():
        if current_user.is_authenticated and session.get("usertype") == "doctor":
            patients = get_doctor_patients(current_user.id)
            return render_template("doctor.html", patients=patients)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/view/<string:patient_username>", methods=["GET"])
    def view(patient_username):
        if current_user.is_authenticated and session.get("usertype") == "doctor":
            patient_id = Patient.query.filter_by(username=patient_username).first().id
            print(patient_id)
            if (
                Patient.query.filter_by(id=patient_id).first().doctor_id
                == current_user.id
            ):
                patient = Patient.query.filter_by(id=patient_id).first()
                print(patient_id)
                age = datetime.datetime.now().year - patient.birth_date.year - 1
                actual_medicine = (
                    PatientMedicine.query.filter_by(patient_id=patient_id)
                    .where(PatientMedicine.end_date == None)
                    .first()
                )
                if actual_medicine:
                    medicine_name = (
                        Medicine.query.filter_by(id=actual_medicine.medicine_id)
                        .first()
                        .name
                    )
                else:
                    medicine_name = None
                    actual_medicine = None
                if (
                    datetime.datetime.now().month > patient.birth_date.month
                    and datetime.datetime.now().day > patient.birth_date.day
                ):
                    age += 1
                doctor = Doctor.query.filter_by(id=patient.doctor_id).first()
                return render_template(
                    "patient.html",
                    user=patient,
                    age=age,
                    actual_medicine=actual_medicine,
                    medicine_name=medicine_name,
                    doctor=doctor,
                )
        return redirect(url_for(REDIRECTHOME))

    @app.route("/medicines/<string:patient_username>", methods=["GET"])
    def medicines(patient_username):
        if request.method == "GET":
            if current_user.is_authenticated:
                if (
                    session.get("usertype") == "doctor"
                    and Patient.query.filter_by(username=patient_username)
                    .first()
                    .doctor_id
                    == current_user.id
                ):
                    patient = Patient.query.filter_by(username=patient_username).first()
                    patient_medicines = PatientMedicine.query.filter_by(
                        patient_id=patient.id
                    ).all()
                    medicines = Medicine.query.all()
                    for patient_medicine in patient_medicines:
                        medicine = Medicine.query.filter_by(
                            id=patient_medicine.medicine_id
                        ).first()
                        patient_medicine.medicine_name = medicine.name
                    return render_template(
                        "medicines.html",
                        patient=patient,
                        patient_medicines=patient_medicines,
                        medicines=medicines,
                    )
                else:
                    return redirect(url_for(REDIRECTHOME))
            else:
                return redirect(url_for(REDIRECTHOME))

    @app.route("/delete_medicine/<int:patient_medicine_id>", methods=["GET"])
    def delete_medicine(patient_medicine_id):
        if current_user.is_authenticated and session.get("usertype") == "doctor":
            patient_medicine = PatientMedicine.query.filter_by(
                id=patient_medicine_id
            ).first()
            patient = Patient.query.filter_by(id=patient_medicine.patient_id).first()
            if patient.doctor_id == current_user.id:
                db.session.delete(patient_medicine)
                db.session.commit()
            return redirect(url_for("medicines", patient_username=patient.username))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/end_treatment/<int:patient_medicine_id>", methods=["GET"])
    def end_treatment(patient_medicine_id):
        if current_user.is_authenticated and session.get("usertype") == "doctor":
            patient_medicine = PatientMedicine.query.filter_by(
                id=patient_medicine_id
            ).first()
            patient = Patient.query.filter_by(id=patient_medicine.patient_id).first()
            if patient.doctor_id == current_user.id:
                patient_medicine.end_date = datetime.datetime.now().date()
                db.session.commit()
            return redirect(url_for("medicines", patient_username=patient.username))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/add_medicine/<string:patient_username>", methods=["GET"])
    def add_medicine_get(patient_username):
        if (
            current_user.is_authenticated
            and session.get("usertype") == "doctor"
            and Patient.query.filter_by(username=patient_username).first().doctor_id
            == current_user.id
        ):
            medicines = Medicine.query.all()
            return render_template("add_medicine.html", medicines=medicines)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/add_medicine/<string:patient_username>", methods=["POST"])
    def add_medicine_post(patient_username):
        if (
            current_user.is_authenticated
            and session.get("usertype") == "doctor"
            and Patient.query.filter_by(username=patient_username).first().doctor_id
            == current_user.id
        ):
            patient = Patient.query.filter_by(username=patient_username).first()
            medicine_id = request.form["medicine"]
            dosage = request.form["dosage"]
            start_date = datetime.datetime.strptime(
                request.form["start_date"], "%Y-%m-%d"
            ).date()
            end_date = request.form["end_date"]
            if end_date == "":
                end_date = None
            else:
                end_date = datetime.datetime.strptime(
                    request.form["end_date"], "%Y-%m-%d"
                ).date()
            patient_medicine = PatientMedicine(
                patient_id=patient.id,
                medicine_id=medicine_id,
                dosage=dosage,
                start_date=start_date,
                end_date=end_date,
            )
            db.session.add(patient_medicine)
            db.session.commit()
            return redirect(url_for("medicines", patient_username=patient_username))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/manage_video/<string:patient_username>", methods=["GET"])
    def manage_video(patient_username):
        if request.method == "GET":
            if (
                current_user.is_authenticated
                and session.get("usertype") == "doctor"
                and Patient.query.filter_by(username=patient_username).first().doctor_id
                == current_user.id
            ):
                patient = Patient.query.filter_by(username=patient_username).first()
                videos = Video.query.filter_by(patient_id=patient.id).all()
                for video in videos:
                    file = NamedTemporaryFile(delete=False)
                    file_path = file.name
                    contents = video.video_data
                    with open(file_path, "wb") as f:
                        f.write(contents)
                    file.close()
                    os.remove(file_path)
                return render_template(
                    "manage_video.html", patient=patient, videos=videos
                )
            return redirect(url_for(REDIRECTHOME))

    @app.route("/add_video/<string:patient_username>", methods=["GET"])
    def add_video_get(patient_username):
        if (
            current_user.is_authenticated
            and session.get("usertype") == "doctor"
            and Patient.query.filter_by(username=patient_username).first().doctor_id
            == current_user.id
        ):
            patient = Patient.query.filter_by(username=patient_username).first()
            videos = Video.query.filter_by(patient_id=patient.id).all()
            return render_template("add_video.html", patient=patient, videos=videos)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/add_video/<string:patient_username>", methods=["POST"])
    def add_video_post(patient_username):
        if (
            current_user.is_authenticated
            and session.get("usertype") == "doctor"
            and Patient.query.filter_by(username=patient_username).first().doctor_id
            == current_user.id
        ):
            patient = Patient.query.filter_by(username=patient_username).first()
            hand = request.form["hand"]
            date = datetime.datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            video_data = request.files["videoFile"].read()
            amplitude = 1
            slowness = 2
            video = Video(
                patient_id=patient.id,
                hand=hand,
                date=date,
                video_data=video_data,
                amplitude=amplitude,
                slowness=slowness,
            )
            db.session.add(video)
            db.session.commit()
            return redirect(url_for("manage_video", patient_username=patient_username))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/delete_video/<int:video_id>", methods=["GET"])
    def delete_video(video_id):
        if current_user.is_authenticated and session.get("usertype") == "doctor":
            video = Video.query.filter_by(id=video_id).first()
            patient = Patient.query.filter_by(id=video.patient_id).first()
            if patient.doctor_id == current_user.id:
                db.session.delete(video)
                db.session.commit()
            return redirect(url_for("manage_video", patient_username=patient.username))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/video/<int:video_id>", methods=["GET"])
    def video(video_id):
        if current_user.is_authenticated:
            video = Video.query.filter_by(id=video_id).first()
            patient = Patient.query.filter_by(id=video.patient_id).first()
            return render_template("video.html", video=video, patient=patient)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/videoView/<int:video_id>")
    def video_view(video_id):
        video = Video.query.get_or_404(video_id)
        return Response(video.video_data, mimetype="video/mp4")

    def get_doctor_patients(doctor_id):
        return Patient.query.filter_by(doctor_id=doctor_id).all()

    return app
