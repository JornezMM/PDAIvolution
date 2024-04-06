from flask import Flask, render_template, request, redirect, url_for, session
from flask_font_awesome import FontAwesome
from flask_sqlalchemy import SQLAlchemy
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
    user_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    hand = db.Column(db.Enum('left', 'right'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    video_data = db.Column(db.LargeBinary, nullable=False)
    classification = db.Column(db.String(100), nullable=True)


class Patient(UserMixin, db.Model):
    def _repr_(self):
        return f'<Patient {self.username}>'
    def get_id(self):
        return self.id
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name1 = db.Column(db.String(100), nullable=False)
    last_name2 = db.Column(db.String(100), nullable=True)
    birth_date = db.Column(db.Date, nullable=False)
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
    last_name1 = db.Column(db.String(100), nullable=False)
    last_name2 = db.Column(db.String(100), nullable=True)

class Doctor(UserMixin,db.Model):
    def _repr_(self):
        return f'<Doctor {self.username}>'
    def get_id(self):
        return self.id
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name1 = db.Column(db.String(100), nullable=False)
    last_name2 = db.Column(db.String(100), nullable=True)
# Initialize the database
db.init_app(app)
with app.app_context():
    db.create_all()
    
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
   return render_template('home.html')

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
                return redirect(url_for('home'))
            elif user_type == 'doctor':
                return redirect(url_for('home'))
            elif user_type == 'admin':
                return redirect(url_for('home'))
        else:
            return "<script>alert('Usuario o contraseña incorrectos.'); window.location.href='/login/';</script>"
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
                return render_template('register.html')
            else:
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        first_name = request.form['name']
        last_name1 = request.form['last_name1']
        last_name2 = request.form['last_name2']

        if user_type == 'patient':
            existing_patient = Patient.query.filter_by(username=username).first()
            if existing_patient:
                return "<script>alert('Ese nombre de usuario ya existe.'); window.location.href='/register/';</script>"
            birth_date = datetime.datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            gender = request.form['gender']
            doctor_id = request.form['doctor_id']
            hashed_password = generate_password_hash(password)
            patient = Patient(username=username, password=hashed_password, first_name=first_name, last_name1=last_name1, last_name2=last_name2, birth_date=birth_date, gender=gender, doctor_id=doctor_id)
            db.session.add(patient)
            print(patient)
            db.session.commit()
        elif user_type == 'doctor':
            existing_doctor = Doctor.query.filter_by(username=username).first()
            if existing_doctor:
                return "<script>alert('Ese nombre de usuario ya existe.'); window.location.href='/register/';</script>"
            hashed_password = generate_password_hash(password)
            doctor = Doctor(username=username, password=hashed_password, first_name=first_name, last_name1=last_name1, last_name2=last_name2)
            db.session.add(doctor)
            print(doctor)
            db.session.commit()
        elif user_type == 'admin':
            existing_admin = Admin.query.filter_by(username=username).first()
            if existing_admin:
                return "<script>alert('Ese nombre de usuario ya existe.'); window.location.href='/register/';</script>"
            hashed_password = generate_password_hash(password)
            admin = Admin(username=username, password=hashed_password, first_name=first_name, last_name1=last_name1, last_name2=last_name2)
            db.session.add(admin)
            db.session.commit()
            return redirect(url_for('home'))
        return redirect(url_for('register'))
    return render_template('register.html')
if __name__ == '__main__':
    app.run(debug=True)
    