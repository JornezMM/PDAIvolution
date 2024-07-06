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
import pickle
import pandas as pd
import xgboost  
import struct
COLUMNS_LENT = [2, 3, 4, 5, 6, 8, 10, 17, 24, 29, 34, 35, 43, 47, 49, 50, 54, 55,
           57, 58, 59, 78, 82, 96, 104, 105, 106, 107, 108, 112, 115, 117, 118, 119, 120, 122,
           123, 124, 126, 127, 129, 130, 131, 133, 134, 135, 137, 138, 139, 141, 152, 156, 162, 166,
           170, 182, 186, 190, 194, 206, 207, 209, 211, 212, 213, 216, 218, 225, 227, 229, 230, 231,
           233, 234, 235, 241, 243, 245, 246, 247, 249, 250, 251, 253, 255, 257, 259, 261, 263, 264,
           272, 273, 275, 277, 280, 281, 284, 285, 286, 288, 290, 294, 297, 308, 310, 312, 316, 318,
           319, 322, 325, 326, 327, 328, 329, 334, 337, 339, 342, 343, 345, 346, 348, 354, 356, 362,
           365, 366, 369, 370, 372, 373, 377, 378, 379, 380, 381, 382, 383, 384, 386, 387, 388, 390,
           392, 393, 394, 397, 398, 399, 402, 403, 407, 408, 409, 413, 414, 415, 416, 417, 420, 424,
           425, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 438, 440, 444, 445, 447, 448, 450,
           453, 454, 459, 460, 461, 467, 472, 473, 475, 477, 478, 481, 482, 484, 486, 487, 488, 491,
           493, 497, 499, 500, 501, 502, 506, 512, 514, 515, 517, 518, 525, 526, 527, 528, 529, 530,
           532, 534, 535, 539, 543, 544, 545, 546, 547, 550, 551, 553, 554, 570, 577, 580, 582, 585,
           586, 590, 591, 596, 597, 602, 606, 608, 610, 612, 613, 615, 621, 622, 625, 626, 629, 632,
           633, 634, 636, 640, 644, 645, 649, 650, 652, 654, 659, 665, 667, 670, 671, 675, 676, 677,
           678, 679, 686, 687, 688, 689, 690, 696, 697, 699, 701, 702, 703, 705, 706, 707, 709, 711,
           716, 725, 726, 727, 728, 729, 730, 731, 733, 735, 736, 747, 750, 751, 755, 756, 760, 761,
           763, 764, 765, 768, 775, 776, 778, 782, 784, 787, 788, 789, 790, 791]
COLUMNS_AMP = [1, 3, 10, 18, 24, 34, 35, 36, 37, 48, 59, 60, 78, 79, 81, 95, 96, 97,
               110, 111, 112, 121, 122, 123, 132, 134, 135, 136, 137, 139, 140, 143, 144, 146, 147,
               148, 150, 151, 152, 154, 155, 156, 158, 159, 160, 162, 163, 166, 167, 170, 174, 178, 179,
               180, 182, 183, 184, 186, 187, 188, 190, 191, 192, 195, 196, 199, 200, 204, 209, 210, 211,
               213, 216, 218, 219, 221, 222, 223, 231, 232, 235, 238, 239, 247, 277, 279, 282, 287, 289,
               290, 294, 295, 297, 298, 300, 301, 307, 308, 309, 310, 312, 314, 316, 318, 319, 321, 322,
               324, 327, 328, 329, 331, 332, 333, 335, 337, 339, 340, 341, 342, 343, 344, 347, 348, 349,
               353, 354, 355, 356, 357, 362, 363, 365, 366, 369, 371, 372, 373, 375, 378, 380, 381, 383,
               385, 387, 388, 394, 398, 400, 401, 402, 404, 405, 407, 409, 410, 411, 412, 414, 415, 416,
               417, 418, 419, 420, 422, 424, 425, 426, 427, 430, 437, 438, 439, 440, 441, 442, 443, 444,
               445, 446, 448, 449, 450, 451, 452, 453, 455, 459, 461, 462, 463, 465, 467, 468, 469, 471,
               472, 473, 475, 497, 498, 500, 501, 508, 509, 510, 512, 518, 519, 520, 521, 522, 525, 527,
               528, 529, 530, 532, 540, 541, 542, 544, 545, 546, 554, 555, 560, 563, 564, 565, 566, 571,
               572, 574, 577, 578, 581, 585, 586, 588, 589, 591, 593, 595, 597, 598, 599, 601, 602, 603,
               604, 605, 607, 608, 610, 611, 612, 613, 615, 616, 617, 620, 624, 625, 626, 627, 629, 630,
               633, 634, 636, 637, 639, 640, 642, 643, 646, 647, 648, 651, 652, 654, 655, 658, 659, 661,
               663, 665, 666, 667, 668, 670, 671, 678, 679, 689, 690, 696, 705, 707, 708, 709, 710, 712,
               716, 722, 728, 732, 734, 757, 758, 761, 763, 765, 766, 771, 775, 782, 786]

HOME = "home.html"
LOGIN = "login.html"
REDIRECTHOME = "home"
REGISTER = "register.html"
MODIFY = "modify.html"
SECRET_KEY="SECRET_KEY"

def create_app():
    app = Flask(__name__)
    load_dotenv()
    config = dotenv_values("./app/.env")
    csrf = CSRFProtect()
    csrf.init_app(app)
    FontAwesome(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
    app.config[SECRET_KEY] = config[SECRET_KEY]
    login_manager = LoginManager()
    login_manager.init_app(app)

    db.init_app(app)

    def create_default_admin():
        """
        Creates a default admin user and adds default medicines to the database if they don't already exist.
        """
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
        """
        Load the user based on the user_id and the user_type stored in the session.

        Args:
            user_id (int): The ID of the user to load.

        Returns:
            object or None: The user object corresponding to the user_id and user_type, or None if the user_type is not set or invalid.
        """
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
        """
        Renders the home.html template.

        Returns:
            The rendered home.html template.
        """
        return render_template("home.html")

    @app.route("/home/")
    def home():
        """
        Redirects the user to the appropriate page based on their authentication status.

        If the user is authenticated, it redirects them to the page specified by their usertype.
        If the user is not authenticated, it redirects them to the login page.

        Returns:
            A redirect response to the appropriate page.
        """
        if current_user.is_authenticated:
            return redirect(url_for(session.get("usertype")))
        return redirect(url_for("login_get"))

    @app.route("/login/", methods=["GET"])
    def login_get():
        """
        Handle GET request for login page.

        If the user is already authenticated, redirect to the home page.
        Otherwise, render the login template.

        Returns:
            If the user is authenticated, a redirect response to the home page.
            Otherwise, a rendered template for the login page.
        """
        if current_user.is_authenticated:
            return redirect(url_for(REDIRECTHOME))
        return render_template(LOGIN)

    @app.route("/login/", methods=["POST"])
    def login_post():
        """
        Handle the POST request for the login route.

        If the user is already authenticated, redirect to the home page.
        Otherwise, retrieve the username, password, and user type from the request form.
        Depending on the user type, query the corresponding table (Patient, Doctor, or Admin) to find the user.
        If the user exists and the password is correct, set the session variables and log in the user.
        Redirect to the home page if the login is successful, otherwise render the login template with an error.

        Returns:
            If the login is successful, redirects to the home page.
            If the login fails, renders the login template with an error.
        """
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
        """
        Logout the user and clear the session.

        Returns:
            A redirect response to the home page.
        """
        logout_user()
        session.clear()
        return redirect(url_for("index"))

    @app.route("/register/", methods=["GET"])
    def register_get():
        """
        Handle GET requests for the '/register/' route.

        If the current user is authenticated and has the 'admin' usertype,
        retrieve all doctors from the database and render the 'REGISTER' template
        with the list of doctor names. Otherwise, redirect to the 'REDIRECTHOME' route.

        Returns:
            If the current user is authenticated and has the 'admin' usertype,
            the 'REGISTER' template with the list of doctor names.
            Otherwise, a redirect to the 'REDIRECTHOME' route.
        """
        if current_user.is_authenticated and session.get("usertype") == "admin":
            doctors = Doctor.query.all()
            return render_template(REGISTER, doctorNames=doctors)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/register/", methods=["POST"])
    def register_post():
        """
        Handle the POST request for user registration.

        This function is responsible for handling the POST request when a user submits the registration form.
        It checks if the current user is authenticated and has the "admin" role in the session.
        If so, it retrieves the username and user type from the form data and performs the registration process
        based on the user type (patient, doctor, or admin).
        If the registration is successful, the user is redirected to the admin page.
        If the user is not authenticated or does not have the "admin" role, they are redirected to the home page.

        Returns:
            A redirect response to the admin page if the registration is successful and the user is an admin.
            A redirect response to the home page if the user is not authenticated or does not have the "admin" role.
        """
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
        """
        Renders the admin page if the current user is authenticated and has the usertype set to 'admin'.
        Otherwise, redirects to the home page.

        Returns:
            If the current user is authenticated and has the usertype set to 'admin', renders the admin.html template
            with the doctors, patients, admins, and admin_username variables.
            Otherwise, redirects to the home page.
        """
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
        """
        Render the modify template based on the user type.

        Args:
            user (str): The user to modify, in the format "<user_type>-<username>".

        Returns:
            If the current user is authenticated and has the usertype "admin", the function
            renders the modify template based on the user type. If the user type is "doctor",
            it retrieves the doctor object from the database and renders the template with the
            doctor object and user type "doctor". If the user type is "patient", it retrieves
            the patient object and associated doctor object from the database, as well as all
            doctors, and renders the template with the patient object, user type "patient",
            doctors, and doctor object. If the user type is "admin", it retrieves the admin
            object from the database and renders the template with the admin object and user
            type "admin". If the current user is not authenticated or does not have the
            usertype "admin", it redirects to the home page.

        """
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
        """
        Modify the user information based on the given user type.

        Args:
            user (str): The user identifier in the format 'user_type-username'.

        Returns:
            redirect: Redirects to the 'admin' route.
        """
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
        """
        Deletes a user from the system.

        Args:
            user (str): The user to be deleted.

        Returns:
            str: A redirect URL or JavaScript code based on the deletion result.
        """
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
        """
        Render the patient page if the user is authenticated as a patient.
        
        Returns:
            If the user is authenticated as a patient, the patient.html template is rendered with the following variables:
            - user: The patient user object.
            - age: The age of the patient calculated based on their birth date.
            - actual_medicine: The current medicine being taken by the patient (if any).
            - medicine_name: The name of the current medicine being taken by the patient (if any).
            - doctor: The doctor object associated with the patient.
            
            If the user is not authenticated as a patient, it redirects to the home page.
        """
        if current_user.is_authenticated and session.get("usertype") == "patient":
            user = Patient.query.filter_by(id=current_user.id).first()
            age = datetime.datetime.now().year - user.birth_date.year - 1
            videos = Video.query.filter_by(patient_id=user.id).all()
            actual_medicine = None
            actual_medicine = (
                    PatientMedicine.query.filter_by(patient_id=user.id)
                    .where(PatientMedicine.end_date == None).all()
                )
            
            if actual_medicine:
                for medicine in actual_medicine:
                    medicine.name = Medicine.query.filter_by(
                        id=medicine.medicine_id
                    ).first().name
            else:
                actual_medicine = None
            if (
                datetime.datetime.now().month > user.birth_date.month
                and datetime.datetime.now().day > user.birth_date.day
            ):
                age += 1
            doctor = Doctor.query.filter_by(id=user.doctor_id).first()
            dates= [video.date for video in videos]
            dates = [date.strftime("%Y-%m-%d") for date in dates]
            amplitude= [video.amplitude for video in videos]
            slowness= [video.slowness for video in videos]
            return render_template(
                "patient.html",
                user=user,
                age=age,
                actual_medicine=actual_medicine,
                doctor=doctor,
                slowness=slowness,
                amplitude=amplitude,
                dates=dates
            )
        return redirect(url_for(REDIRECTHOME))

    @app.route("/doctor/", methods=["GET"])
    def doctor():
        """
        Renders the doctor.html template if the current user is authenticated as a doctor.
        Otherwise, redirects to the home page.

        Returns:
            If the user is authenticated as a doctor, the doctor.html template is rendered with the patients data.
            Otherwise, redirects to the home page.
        """
        if current_user.is_authenticated and session.get("usertype") == "doctor":
            patients = get_doctor_patients(current_user.id)
            return render_template("doctor.html", patients=patients)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/view/<string:patient_username>", methods=["GET"])
    def view(patient_username):
        """
        View function to display patient information.

        Args:
            patient_username (str): The username of the patient.

        Returns:
            flask.Response: The rendered patient.html template with patient information.
        """
        if current_user.is_authenticated and session.get("usertype") == "doctor":
            patient_id = Patient.query.filter_by(username=patient_username).first().id
            if Patient.query.filter_by(id=patient_id).first().doctor_id == current_user.id:
                patient = Patient.query.filter_by(id=patient_id).first()
                age = datetime.datetime.now().year - patient.birth_date.year - 1
                actual_medicine = (
                    PatientMedicine.query.filter_by(patient_id=patient_id)
                    .where(PatientMedicine.end_date == None).all()
                )
                
                if actual_medicine:
                    for medicine in actual_medicine:
                        medicine.name = Medicine.query.filter_by(
                            id=medicine.medicine_id
                        ).first().name
                else:
                    actual_medicine = None
                if (
                    datetime.datetime.now().month > patient.birth_date.month
                    and datetime.datetime.now().day > patient.birth_date.day
                ):
                    age += 1
                videos = Video.query.filter_by(patient_id=patient_id).all()
                dates= [video.date for video in videos]
                dates = [date.strftime("%Y-%m-%d") for date in dates]
                amplitude= [video.amplitude for video in videos]
                slowness= [video.slowness for video in videos]
                print(slowness)
                doctor = Doctor.query.filter_by(id=patient.doctor_id).first()
                return render_template(
                    "patient.html",
                    user=patient,
                    age=age,
                    actual_medicine=actual_medicine,
                    doctor=doctor,
                    slowness=slowness,
                    amplitude=amplitude,
                    dates=dates
                )
        return redirect(url_for(REDIRECTHOME))

    @app.route("/medicines/<string:patient_username>", methods=["GET"])
    def medicines(patient_username):
        """
        Retrieves and displays the medicines for a specific patient.

        Args:
            patient_username (str): The username of the patient.

        Returns:
            A rendered HTML template displaying the patient's medicines.
        """
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
        """
        Delete a medicine for a patient.

        Args:
            patient_medicine_id (int): The ID of the patient's medicine to be deleted.

        Returns:
            redirect: Redirects to the "medicines" route for the patient.
        """
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
        """
        End the treatment for a specific patient medicine.

        Args:
            patient_medicine_id (int): The ID of the patient medicine.

        Returns:
            redirect: Redirects to the "medicines" route for the patient.
        """
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
        """
        Handle GET request for adding medicine to a patient.

        Args:
            patient_username (str): The username of the patient.

        Returns:
            If the current user is authenticated as a doctor and has the correct doctor-patient relationship,
            it returns the rendered template "add_medicine.html" with a list of all medicines.
            Otherwise, it redirects to the home page.
        """
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
        """
        Add a medicine for a specific patient.

        Args:
            patient_username (str): The username of the patient.

        Returns:
            redirect: Redirects to the "medicines" page for the specified patient.

        Raises:
            Redirect: Redirects to the home page if the user is not authenticated or does not have the required permissions.
        """
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
        """
        View function for managing videos of a patient.

        Args:
            patient_username (str): The username of the patient.

        Returns:
            If the request method is GET and the user is authenticated as a doctor and has the
            necessary permissions, it returns the rendered template for managing videos of the
            specified patient. Otherwise, it redirects to the home page.

        """
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
        """
        Render the add_video.html template with patient and video data.

        Args:
            patient_username (str): The username of the patient.

        Returns:
            If the current user is authenticated, has the usertype "doctor", and is the doctor of the specified patient,
            the function returns the rendered add_video.html template with the patient and video data.
            Otherwise, it redirects to the REDIRECTHOME page.

        """
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
        """
        Add a video for a specific patient.

        Args:
            patient_username (str): The username of the patient.

        Returns:
            redirect: Redirects to the "manage_video" page for the patient.
        """
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
            amplitude = 0
            slowness = 0
            video = Video(
                patient_id=patient.id,
                hand=hand,
                date=date,
                video_data=video_data,
                amplitude=amplitude,
                slowness=slowness,
            )
            with open("ampModel.pkl", "rb") as f:
                amp = pickle.load(f)
            with open("lentModel.pkl", "rb") as f:
                lent = pickle.load(f)
            file = NamedTemporaryFile(delete=False)
            file_path = file.name
            contents = video_data
            with open(file_path, "wb") as f:
                f.write(contents)
                (
                    classic_features,
                    fresh_features,
                    detection_time,
                )= extract_video_features(file_path)
                gender = 0 if patient.gender == "M" else 1
                hand = 0 if hand == "right" else 1
                handedness = 0 if patient.handedness == "right" else 1
                misc_features = pd.Series([hand, gender, datetime.datetime.now().year - patient.birth_date.year - 1, handedness], index=[ "hand","gender", "age", "handedness"])
                all_features = pd.concat([misc_features, classic_features, fresh_features])
                all_features = all_features.to_frame().T
                all_features = all_features.drop(columns=["angle__query_similarity_count__query_None__threshold_0.0"])
                all_features_lent= all_features.iloc[:, COLUMNS_LENT]
                all_features_amp= all_features.iloc[:, COLUMNS_AMP]
                print(all_features)
                video.amplitude = struct.unpack('<Q', amp.predict(all_features_amp))[0]
                video.slowness = struct.unpack('<Q', lent.predict(all_features_lent))[0]
            file.close()
            os.remove(file_path)
            db.session.add(video)
            
            db.session.commit()
            return redirect(url_for("manage_video", patient_username=patient_username))
        return redirect(url_for(REDIRECTHOME))

    @app.route("/delete_video/<int:video_id>", methods=["GET"])
    def delete_video(video_id):
        """
        Deletes a video from the database.

        Parameters:
        - video_id (int): The ID of the video to be deleted.

        Returns:
        - redirect: Redirects to the "manage_video" route for the corresponding patient.
        """
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
        """
        Render the video page for the specified video ID.

        Parameters:
        - video_id (int): The ID of the video to be rendered.

        Returns:
        - response: The rendered video page if the user is authenticated, otherwise redirects to the home page.
        """
        if current_user.is_authenticated:
            video = Video.query.filter_by(id=video_id).first()
            patient = Patient.query.filter_by(id=video.patient_id).first()
            return render_template("video.html", video=video, patient=patient)
        return redirect(url_for(REDIRECTHOME))

    @app.route("/videoView/<int:video_id>")
    def video_view(video_id):
        """
        View function for displaying a video.

        Args:
            video_id (int): The ID of the video to be displayed.

        Returns:
            Response: The video data as a response with the mimetype set to "video/mp4".
        """
        video = Video.query.get_or_404(video_id)
        return Response(video.video_data, mimetype="video/mp4")

    @app.route("/about/", methods=["GET"])
    def about():
        """
        Render the about page.

        Returns:
            The rendered about.html template with the first_name variable from the session.
        """
        return render_template("about.html", first_name=session.get("first_name"))

    @app.errorhandler(404)
    def page_not_found(e):
        """
        Handle the 404 error page.

        Args:
            e: The error object.

        Returns:
            A rendered template for the 404 error page with a 404 status code.
        """
        return render_template('404.html'), 404
    
    def get_doctor_patients(doctor_id):
        return Patient.query.filter_by(doctor_id=doctor_id).all()

    return app
