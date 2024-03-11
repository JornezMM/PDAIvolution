from flask import Flask, render_template, request, redirect, url_for
from flask_font_awesome import FontAwesome
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash

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


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name1 = db.Column(db.String(100), nullable=False)
    last_name2 = db.Column(db.String(100), nullable=True)
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum('M', 'F','O'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name1 = db.Column(db.String(100), nullable=False)
    last_name2 = db.Column(db.String(100), nullable=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
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

    return Users.query.get(user_id)

@app.route('/')
def home():
   return render_template('home.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    # if request.method == 'POST':
    #     username = request.form['username']
    #     password = request.form['password']
        
    #     # Check if user exists in the database
    #     for user in users:
    #         if user['username'] == username and user['password'] == password:
    #             return redirect(url_for('home'))
        
    #     return 'Invalid username or password'
    
    return render_template('login.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        first_name = request.form['name']
        last_name1 = request.form['last_name1']
        last_name2 = request.form['last_name2']

        if user_type == 'patient':
            # Check if the patient already exists in the database
            existing_patient = Patient.query.filter_by(username=username).first()
            if existing_patient:
                return 'Patient already exists'
            
            # Create a new patient
            birth_date = request.form['birth_date']
            gender = request.form['gender']
            doctor_id = request.form['doctor_id']
            hashed_password = generate_password_hash(password)  # Hash the password
            patient = Patient(username=username, password=hashed_password, first_name=first_name, last_name1=last_name1, last_name2=last_name2, birth_date=birth_date, gender=gender, doctor_id=doctor_id)
            db.session.add(patient)
            print(patient)
            db.session.commit()
        elif user_type == 'doctor':
            # Check if the doctor already exists in the database
            existing_doctor = Doctor.query.filter_by(username=username).first()
            if existing_doctor:
                return 'Doctor already exists'
            
            # Create a new doctor
            hashed_password = generate_password_hash(password)  # Hash the password
            doctor = Doctor(username=username, password=hashed_password, first_name=first_name, last_name1=last_name1, last_name2=last_name2)
            db.session.add(doctor)
            print(doctor)
            db.session.commit()
        elif user_type == 'admin':
            # Check if the admin already exists in the database
            existing_admin = Admin.query.filter_by(username=username).first()
            if existing_admin:

                return 'Admin already exists'
            
            # Create a new admin
            hashed_password = generate_password_hash(password)  # Hash the password
            admin = Admin(username=username, password=hashed_password, first_name=first_name, last_name1=last_name1, last_name2=last_name2)
            db.session.add(admin)
            db.session.commit()
            return "aaaaaaaaaaaaaaaaaaaaaaaaaa"

    return redirect(url_for('home'))
    
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
    