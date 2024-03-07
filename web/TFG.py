from flask import Flask, render_template, request, redirect, url_for
from flask_font_awesome import FontAwesome
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

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
    age = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name1 = db.Column(db.String(100), nullable=False)
    last_name2 = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=False)
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
    # if request.method == 'POST':
    #     username = request.form['username']
    #     password = request.form['password']
        
    #     # Check if user already exists in the database
    #     for user in users:
    #         if user['username'] == username:
    #             return 'Username already taken'
        
    #     # Add new user to the database
    #     users.append({'username': username, 'password': password})
    #     return redirect(url_for('login'))
    
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
    