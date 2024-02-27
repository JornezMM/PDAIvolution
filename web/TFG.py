from flask import Flask, render_template, request, redirect, url_for
from flask_font_awesome import FontAwesome

app = Flask(__name__)
font_awesome = FontAwesome(app)

# Dummy user database
users = []

@app.route('/')
def home():
   return render_template('home.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists in the database
        for user in users:
            if user['username'] == username and user['password'] == password:
                return redirect(url_for('home'))
        
        return 'Invalid username or password'
    
    return render_template('login.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user already exists in the database
        for user in users:
            if user['username'] == username:
                return 'Username already taken'
        
        # Add new user to the database
        users.append({'username': username, 'password': password})
        return redirect(url_for('login'))
    
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
    