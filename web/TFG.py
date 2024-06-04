from flask import Flask, render_template, request, redirect, url_for, session,Response
from flask_font_awesome import FontAwesome
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import Admin, Doctor, Patient, Medicine, PatientMedicine, Video, db
import datetime

HOME = 'home.html'
LOGIN = 'login.html'
REDIRECTHOME = 'home'

app = Flask(__name__)
font_awesome = FontAwesome(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "abc"

login_manager = LoginManager()
login_manager.init_app(app)

def create_default_admin():
    if not Admin.query.first():
        default_admin = Admin(
            username='admin',
            password="scrypt:32768:8:1$qIEAmGScjaI4Sokx$33074b5fb76cf77744d751e832250dbcd090080cdd93f23adb5d555ccd324e2021cb04076c0e3a9fc8ba62239452db8851791d8d0fc93ef9558aeeb4e6a5953d",
            first_name='Default',
            last_name='Admin'
        )
        db.session.add(default_admin)
    if not Medicine.query.first():
        medicine1 = Medicine(name='Medicine 1')
        medicine2 = Medicine(name='Medicine 2')
        medicine3 = Medicine(name='Medicine 3')
        db.session.add(medicine1)
        db.session.add(medicine2)
        db.session.add(medicine3)
    db.session.commit()
db.init_app(app)
with app.app_context():
    db.create_all()
    create_default_admin()
    
@login_manager.user_loader
def loader_user(user_id):
    """Carga el usuario desde la base de datos"""
    if session.get('usertype') == None:
        return None
    user_type = session.get('usertype')
    if user_type == 'patient':
        return Patient.query.get(user_id)
    elif user_type == 'doctor':
        return Doctor.query.get(user_id)
    elif user_type == 'admin':
        return Admin.query.get(user_id)
    else:
        return None

@app.route('/')
def index():
   return render_template('home.html')

@app.route('/home/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for(session.get("usertype")))
    return redirect(url_for('login_get'))

@app.route('/login/', methods=['GET'])
def login_get():
    if current_user.is_authenticated:
        return redirect(url_for(REDIRECTHOME))
    return render_template(LOGIN)

@app.route('/login/',methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['role']
    if user_type == 'patient':
        user = Patient.query.filter_by(username=username).first()
    elif user_type == 'doctor':
        user = Doctor.query.filter_by(username=username).first()
    elif user_type == 'admin':
        user = Admin.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['usertype'] = user_type
        session['first_name'] = user.first_name
        login_user(user)
        return redirect(url_for(REDIRECTHOME))
    else:
        return render_template(LOGIN, error=True)

@app.route('/logout/')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for(REDIRECTHOME))

@app.route('/register/', methods=['GET'])
def register_get():
    if current_user.is_authenticated and session.get("usertype") == 'admin':
        doctors= Doctor.query.all()
        return render_template('register.html', doctorNames=doctors)
    return redirect(url_for(REDIRECTHOME))
                    
@app.route('/register/', methods=['POST'])
def register_post():
    if current_user.is_authenticated and session.get("usertype") == 'admin':
        username = request.form['username']
        user_type = request.form['user_type']
        if user_type == 'patient' and not Patient.query.filter_by(username=username).first():
            db.session.add(register_patient(request.form))
            db.session.commit()
        elif user_type == 'doctor' and not Doctor.query.filter_by(username=username).first():
            db.session.add(register_doctor(request.form))
            db.session.commit()
        elif user_type == 'admin' and not Admin.query.filter_by(username=username).first():
            db.session.add(register_admin(request.form))
            db.session.commit()
        else:
            return render_template('register.html', error=True)
        return redirect(url_for('admin'))
    return redirect(url_for(REDIRECTHOME))    
    
def register_patient(form):
    username = form['username']
    password = form['password']
    first_name = form['name']
    last_name = form['last_name']
    birth_date = datetime.datetime.strptime(form['birth_date'], '%Y-%m-%d').date()
    gender = form['gender']
    doctor_id = form['doctor_id']
    handedness = form['handedness']
    hashed_password = generate_password_hash(password)
    return Patient(username=username, password=hashed_password, first_name=first_name,
                   last_name=last_name, birth_date=birth_date, gender=gender, doctor_id=doctor_id, handedness=handedness)

def register_doctor(form):
    username = form['username']
    if Doctor.query.filter_by(username=username).first():
        return render_template('register.html', error=True)
    password = form['password']
    first_name = form['name']
    last_name = form['last_name']
    hashed_password = generate_password_hash(password)
    return Doctor(username=username, password=hashed_password, first_name=first_name, last_name=last_name)

def register_admin(form):
    username = form['username']
    if Admin.query.filter_by(username=username).first():
        return render_template('register.html', error=True)
    password = form['password']
    first_name = form['name']
    last_name = form['last_name']
    hashed_password = generate_password_hash(password)
    return Admin(username=username, password=hashed_password, first_name=first_name, last_name=last_name)

@app.route('/admin/', methods=['GET'])
def admin():
    if current_user.is_authenticated and session.get("usertype") == 'admin':
        doctors = Doctor.query.all()
        patients = Patient.query.all()
        admins = Admin.query.all()
        return render_template('admin.html', doctors=doctors, patients=patients, admins=admins, admin_username=current_user.username)
    return redirect(url_for(REDIRECTHOME))

@app.route('/modify/<string:user>', methods=['GET'])
def modify_get(user):
    if current_user.is_authenticated and session.get("usertype") == 'admin':
        splited_user = user.split('-')
        username = splited_user[1]
        match splited_user[0].lower():
            case 'doctor':
                doctor = Doctor.query.filter_by(username=username).first()
                return render_template('modify.html', user=doctor, user_type='doctor')
            case 'patient':
                patient = Patient.query.filter_by(username=username).first()
                doctor= Doctor.query.get(patient.doctor_id)
                doctors = Doctor.query.all()
                return render_template('modify.html', user=patient, user_type='patient', doctors=doctors, doctor=doctor)
            case 'admin':
                admin = Admin.query.filter_by(username=username).first()
                return render_template('modify.html', user=admin, user_type='admin')
    return redirect(url_for(REDIRECTHOME))

@app.route('/modify/<string:user>', methods=['POST'])
def modify_post(user):
    old_username = user.split('-')[1]
    user_type = user.split('-')[0]
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['name']
    last_name = request.form['last_name']
    if user_type == 'patient':
        birth_date = datetime.datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
        doctor_id = request.form['doctor_id']
        patient = Patient.query.filter_by(username=old_username).first()
        patient.username = username
        patient.first_name = first_name
        patient.last_name = last_name
        patient.birth_date = birth_date
        patient.doctor_id = doctor_id
        if password:
            patient.password = generate_password_hash(password)
        db.session.commit()
    elif user_type == 'doctor':
        doctor = Doctor.query.filter_by(username=old_username).first()
        doctor.username = username
        doctor.first_name = first_name
        doctor.last_name = last_name
        if password:
            doctor.password = generate_password_hash(password)
        db.session.commit()
    elif user_type == 'admin':
        admins = Admin.query.all()
        admin = Admin.query.filter_by(username=old_username).first()
        admin.username = username
        admin.first_name = first_name
        admin.last_name = last_name
        if password:
            admin.password = generate_password_hash(password)
        db.session.commit()
    return redirect(url_for('admin'))
            
@app.route('/delete/<string:user>', methods=['GET'])
def delete(user):
    if current_user.is_authenticated and session.get("usertype") == 'admin':
        user_type = user.split('-')[0]
        username = user.split('-')[1]
        if user_type == 'patient':
            patient = Patient.query.filter_by(username=username).first()
            db.session.delete(patient)
            db.session.commit()
        elif user_type == 'doctor':
            doctor = Doctor.query.filter_by(username=username).first()
            if get_doctor_patients(doctor.id):
                return "<script>window.location.href='/admin/';alert('No se puede eliminar un doctor con pacientes asignados.');</script>"
            db.session.delete(doctor)
            db.session.commit()
        elif user_type == 'admin':
            if username == current_user.username:
                return "<script>window.location.href='/admin/';alert('No se puede eliminar el usuario actual.');</script>"
            admin = Admin.query.filter_by(username=username).first()
            db.session.delete(admin)
            db.session.commit()
        return redirect(url_for('admin'))
    return redirect(url_for(REDIRECTHOME))

@app.route('/patient/', methods=['GET'])
def patient():
    if current_user.is_authenticated and session.get("usertype") == 'patient':
        user= Patient.query.filter_by(id=current_user.id).first()
        age= datetime.datetime.now().year - user.birth_date.year-1
        actual_medicine = PatientMedicine.query.filter_by(patient_id=user.id).where(PatientMedicine.end_date == None).first()
        if actual_medicine:
            medicine_name = Medicine.query.get(actual_medicine.medicine_id).name
        else:
            medicine_name = None
            actual_medicine = None                
        if datetime.datetime.now().month > user.birth_date.month and datetime.datetime.now().day > user.birth_date.day:
            age += 1
        doctor= Doctor.query.get(user.doctor_id)
        return render_template('patient.html',user=user, age=age, actual_medicine=actual_medicine, medicine_name=medicine_name,
                                doctor=doctor)
    return redirect(url_for(REDIRECTHOME))

@app.route('/doctor/', methods=['GET'])
def doctor():
    if current_user.is_authenticated and session.get("usertype") == 'doctor':
        patients = get_doctor_patients(current_user.id)
        return render_template('doctor.html', patients=patients)
    return redirect(url_for(REDIRECTHOME))
        
@app.route('/view/<string:patient_username>', methods=['GET'])
def view(patient_username):
    if current_user.is_authenticated and session.get("usertype") == 'doctor':
        patient_id = Patient.query.filter_by(username=patient_username).first().id
        if  Patient.query.get(patient_id).doctor_id == current_user.id:
            user= Patient.query.filter_by(id=patient_id).first()
            age= datetime.datetime.now().year - user.birth_date.year-1
            actual_medicine = PatientMedicine.query.filter_by(patient_id=user.id).where(PatientMedicine.end_date == None).first()
            if actual_medicine:
                medicine_name = Medicine.query.get(actual_medicine.medicine_id).name
            else:
                medicine_name = None
                actual_medicine = None                
            if datetime.datetime.now().month > user.birth_date.month and datetime.datetime.now().day > user.birth_date.day:
                age += 1
            doctor= Doctor.query.get(user.doctor_id)
            return render_template('patient.html',user=user, age=age, actual_medicine=actual_medicine, medicine_name=medicine_name,doctor=doctor)
    return redirect(url_for(REDIRECTHOME))
    
@app.route('/medicines/<string:patient_username>', methods=['GET'])
def medicines(patient_username):
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
                patient = Patient.query.filter_by(username=patient_username).first()
                patient_medicines = PatientMedicine.query.filter_by(patient_id=patient.id).all()
                medicines = Medicine.query.all()
                for patient_medicine in patient_medicines:
                    medicine = Medicine.query.get(patient_medicine.medicine_id)
                    patient_medicine.medicine_name = medicine.name
                return render_template('medicines.html', patient=patient, patient_medicines=patient_medicines, medicines=medicines)
            else:
                return redirect(url_for(REDIRECTHOME))
        else:
            return redirect(url_for(REDIRECTHOME))
        
@app.route('/add_medicine/<string:patient_username>', methods=['GET'])
def add_medicine_get(patient_username):
    if current_user.is_authenticated and session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
        medicines = Medicine.query.all()
        return render_template('add_medicine.html', medicines=medicines)
    return redirect(url_for(REDIRECTHOME))
    
@app.route('/add_medicine/<string:patient_username>', methods=['POST'])
def add_medicine_post(patient_username):
    if current_user.is_authenticated and session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
        patient = Patient.query.filter_by(username=patient_username).first()
        medicine_id = request.form['medicine']
        dosage = request.form['dosage']
        start_date = datetime.datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = request.form['end_date']
        if end_date == '':
            end_date = None
        else:
            end_date = datetime.datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        patient_medicine = PatientMedicine(patient_id=patient.id, medicine_id=medicine_id, dosage=dosage, start_date=start_date, end_date=end_date)
        db.session.add(patient_medicine)
        db.session.commit()
        return redirect(url_for('medicines', patient_username=patient_username))
    return redirect(url_for(REDIRECTHOME))
    
@app.route('/manage_video/<string:patient_username>', methods=['GET'])
def manage_video(patient_username):
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
                patient = Patient.query.filter_by(username=patient_username).first()
                videos = Video.query.filter_by(patient_id=patient.id).all()
                return render_template('manage_video.html', patient=patient, videos=videos)
        return redirect(url_for(REDIRECTHOME))
    
@app.route('/add_video/<string:patient_username>', methods=['GET'])
def add_video_get(patient_username):
    if current_user.is_authenticated and session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
        patient = Patient.query.filter_by(username=patient_username).first()
        videos = Video.query.filter_by(patient_id=patient.id).all()
        return render_template('add_video.html', patient=patient, videos=videos)
    return redirect(url_for(REDIRECTHOME))

@app.route('/add_video/<string:patient_username>', methods=['POST'])
def add_video_post(patient_username):
    if current_user.is_authenticated and session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
        patient = Patient.query.filter_by(username=patient_username).first()
        hand = request.form['hand']
        date = datetime.datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        video_data = request.files['videoFile'].read()
        amplitude = 1
        slowness = 2
        video = Video(patient_id=patient.id, hand=hand, date=date, video_data=video_data, amplitude=amplitude, slowness=slowness)
        db.session.add(video)
        db.session.commit()
        return redirect(url_for('manage_video', patient_username=patient_username))
    return redirect(url_for(REDIRECTHOME))
    
@app.route('/video/<int:video_id>', methods=['GET'])
def video(video_id):
    if current_user.is_authenticated:
        video = Video.query.get(video_id)
        patient = Patient.query.get(video.patient_id)
        return render_template('video.html', video=video, patient=patient)
    return redirect(url_for(REDIRECTHOME))

@app.route('/videoView/<int:video_id>')
def videoView(video_id):
    video = Video.query.get_or_404(video_id)
    return Response(video.video_data, mimetype='video/mp4')

def get_doctor_patients(doctor_id):
    return Patient.query.filter_by(doctor_id=doctor_id).all()


if __name__ == '__main__':
    app.run(debug=True)
    