from flask import Flask, render_template, request, redirect, url_for, session,Response
from flask_font_awesome import FontAwesome
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
font_awesome = FontAwesome(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "abc"
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.init_app(app)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    hand = db.Column(db.Enum('left', 'right'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    video_data = db.Column(db.LargeBinary, nullable=False)
    amplitude = db.Column(db.Integer, nullable=False)
    slowness = db.Column(db.Integer, nullable=False)

class Patient(UserMixin, db.Model):
    def _repr_(self):
        return f'<Patient {self.username}>'
    def get_id(self):
        return self.id
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    handedness = db.Column(db.Enum('right', 'left'), nullable=False)
    gender = db.Column(db.Enum('M', 'F'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

class Admin(UserMixin, db.Model):
    def _repr_(self):
        return f'<Admin {self.username}>'
    def get_id(self):
        return self.id
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

class Doctor(UserMixin,db.Model):
    def _repr_(self):
        return f'<Doctor {self.username}>'
    def get_id(self):
        return self.id
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class PatientMedicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)

# Initialize the database
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

    # medicine1 = Medicine.query.filter_by(name='Medicine 1').first()
    # medicine2 = Medicine.query.filter_by(name='Medicine 2').first()
    # jupe = Patient.query.filter_by(username='jupe').first()
    # if medicine1 and medicine2:
    #     patient_medicine1 = PatientMedicine(
    #         patient_id=jupe.id,
    #         medicine_id=medicine1.id,
    #         dosage='2 pills',
    #         start_date=datetime.date(2022, 1, 1),
    #         end_date=datetime.date(2022, 1, 31)
    #     )
    #     patient_medicine2 = PatientMedicine(
    #         patient_id=jupe.id,
    #         medicine_id=medicine2.id,
    #         dosage='1 pill',
    #         start_date=datetime.date(2022, 2, 1),
    #         end_date=datetime.date(2022, 2, 28)
    #     )
    # db.session.add(patient_medicine1)
    # db.session.add(patient_medicine2)
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
        if session.get("usertype") == 'doctor':
            return redirect(url_for('doctor'))
        elif session.get("usertype") == 'admin':
            return redirect(url_for('admin'))
        elif session.get("usertype") == 'patient':
            return redirect(url_for('patient'))
    else:
        return redirect(url_for('login'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    if request.method == 'POST':
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
            login_user(user)
            if user_type == 'patient':
                return redirect(url_for('patient'))
            elif user_type == 'doctor':
                return redirect(url_for('home'))
            elif user_type == 'admin':
                return redirect(url_for('home'))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html')

@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'admin':
                doctors= Doctor.query.all()
                return render_template('register.html', doctorNames=doctors,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        first_name = request.form['name']
        last_name = request.form['last_name']
        if user_type == 'patient':
            existing_patient = Patient.query.filter_by(username=username).first()
            if existing_patient:
                return render_template('register.html', error=True,username=current_user.first_name)
            birth_date = datetime.datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            gender = request.form['gender']
            doctor_id = request.form['doctor_id']
            handedness = request.form['handedness']
            hashed_password = generate_password_hash(password)
            patient = Patient(username=username, password=hashed_password, first_name=first_name, last_name=last_name, birth_date=birth_date, gender=gender, doctor_id=doctor_id, handedness=handedness)
            db.session.add(patient)
            db.session.commit()
        elif user_type == 'doctor':
            existing_doctor = Doctor.query.filter_by(username=username).first()
            if existing_doctor:
                return render_template('register.html',username=current_user.first_name, error=True)
            hashed_password = generate_password_hash(password)
            doctor = Doctor(username=username, password=hashed_password, first_name=first_name, last_name=last_name)
            db.session.add(doctor)
            db.session.commit()
        elif user_type == 'admin':
            existing_admin = Admin.query.filter_by(username=username).first()
            if existing_admin:
                return render_template('register.html',username=current_user.first_name, error=True)
            hashed_password = generate_password_hash(password)
            admin = Admin(username=username, password=hashed_password, first_name=first_name, last_name=last_name)
            db.session.add(admin)
            db.session.commit()
        return redirect(url_for('admin'))    

@app.route('/admin/', methods=['GET'])
def admin():
    if request.method == 'GET':
        doctors = Doctor.query.all()
        patients = Patient.query.all()
        admins = Admin.query.all()
        if current_user.is_authenticated:
            if session.get("usertype") == 'admin':
                return render_template('admin.html', doctors=doctors, patients=patients, admins=admins, admin_username=current_user.first_name,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))

@app.route('/modify/<string:user>', methods=['GET', 'POST'])
def modify(user):
    if request.method == 'GET':
        rowData = user.split('-')
        if current_user.is_authenticated:
            if session.get("usertype") == 'admin':
                username = rowData[1]
                match rowData[0].lower():
                    case 'doctor':
                        doctor = Doctor.query.filter_by(username=rowData[1]).first()
                        return render_template('modify.html', user=doctor, user_type='doctor',username=current_user.first_name)
                    case 'patient':
                        patient = Patient.query.filter_by(username=rowData[1]).first()
                        doctor= Doctor.query.get(patient.doctor_id)
                        doctors = Doctor.query.all()
                        return render_template('modify.html', user=patient, user_type='patient', doctors=doctors, doctor=doctor,username=current_user.first_name)
                    case 'admin':
                        admin = Admin.query.filter_by(username=rowData[1]).first()
                        return render_template('modify.html', user=admin, user_type='admin',username=current_user.first_name)

            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    if request.method == 'POST':
        old_username = user.split('-')[1]
        print(old_username)
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
                hashed_password = generate_password_hash(password)
                patient.password = hashed_password
            db.session.commit()
        elif user_type == 'doctor':
            doctor = Doctor.query.filter_by(username=old_username).first()
            doctor.username = username
            doctor.first_name = first_name
            doctor.last_name = last_name
            if password:
                hashed_password = generate_password_hash(password)
                doctor.password = hashed_password
            db.session.commit()
        elif user_type == 'admin':
            admins = Admin.query.all()
            admin = Admin.query.filter_by(username=old_username).first()
            admin.username = username
            admin.first_name = first_name
            admin.last_name = last_name
            if password:
                hashed_password = generate_password_hash(password)
                admin.password = hashed_password
            db.session.commit()
        return redirect(url_for('admin'))
            
@app.route('/delete/<string:user>', methods=['GET'])
def delete(user):
    if current_user.is_authenticated:
        if session.get("usertype") == 'admin':
            user_type = user.split('-')[0]
            username = user.split('-')[1]
            if user_type == 'patient':
                patient = Patient.query.filter_by(username=username).first()
                db.session.delete(patient)
                db.session.commit()
            elif user_type == 'doctor':
                doctor = Doctor.query.filter_by(username=username).first()
                if get_doctor_patients(doctor.id):
                    return "<script>alert('No se puede eliminar un doctor con pacientes asignados.'); window.location.href='/admin/';</script>"
                else:
                    db.session.delete(doctor)
                    db.session.commit()
            elif user_type == 'admin':
                admin = Admin.query.filter_by(username=username).first()
                db.session.delete(admin)
                db.session.commit()
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/patient/', methods=['GET'])
def patient():
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'patient':
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
                                       doctor=doctor,username=current_user.first_name)
            else:
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))

@app.route('/doctor/', methods=['GET'])
def doctor():
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'doctor':
                patients = get_doctor_patients(current_user.id)
                return render_template('doctor.html', patients=patients,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
@app.route('/view/<string:patient_username>', methods=['GET'])
def view(patient_username):
    if request.method == 'GET':
        if current_user.is_authenticated:
            print(patient_username)
            patient_id = Patient.query.filter_by(username=patient_username).first().id
            print(patient_id)
            if session.get("usertype") == 'doctor' and Patient.query.get(patient_id).doctor_id == current_user.id:
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
                return render_template('patient.html',user=user, age=age, actual_medicine=actual_medicine, medicine_name=medicine_name,doctor=doctor,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
@app.route('/medicines/<string:patient_username>', methods=['GET', 'POST'])
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
                return render_template('medicines.html', patient=patient, patient_medicines=patient_medicines, medicines=medicines,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
@app.route('/add_medicine/<string:patient_username>', methods=['GET','POST'])
def add_medicine(patient_username):
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
                medicines = Medicine.query.all()
                return render_template('add_medicine.html', medicines=medicines,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    if request.method == 'POST':
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
@app.route('/manage_video/<string:patient_username>', methods=['GET'])
def manage_video(patient_username):
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
                patient = Patient.query.filter_by(username=patient_username).first()
                videos = Video.query.filter_by(patient_id=patient.id).all()
                return render_template('manage_video.html', patient=patient, videos=videos,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
@app.route('/add_video/<string:patient_username>', methods=['GET','POST'])
def add_video(patient_username):
    if request.method == 'GET':
        if current_user.is_authenticated:
            if session.get("usertype") == 'doctor' and Patient.query.filter_by(username=patient_username).first().doctor_id == current_user.id:
                patient = Patient.query.filter_by(username=patient_username).first()
                videos = Video.query.filter_by(patient_id=patient.id).all()
                return render_template('add_video.html', patient=patient, videos=videos,username=current_user.first_name)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    elif request.method == 'POST':
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
    
@app.route('/video/<int:video_id>', methods=['GET'])
def video(video_id):
    if request.method == 'GET':
        if current_user.is_authenticated:
            video = Video.query.get(video_id)
            patient = Patient.query.get(video.patient_id)
            return render_template('video.html', video=video, patient=patient,username=current_user.first_name)
    else:
        return redirect(url_for('home'))

@app.route('/videoView/<int:video_id>')
def videoView(video_id):
    video = Video.query.get_or_404(video_id)
    return Response(video.video_data, mimetype='video/mp4')
def get_doctor_patients(doctor_id):
    return Patient.query.filter_by(doctor_id=doctor_id).all()


if __name__ == '__main__':
    app.run(debug=True)
    