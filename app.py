from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database Setup
def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY, 
                            username TEXT UNIQUE, 
                            password TEXT)''')
        conn.commit()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            
            if user:
                cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
                user_valid = cursor.fetchone()
                if user_valid:
                    session['user'] = username
                    return redirect(url_for('upload'))
                else:
                    flash('Incorrect password!', 'danger')
            else:
                flash('Account does not exist! Please register.', 'warning')
                return redirect(url_for('register'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            
            if user:
                flash('Username already exists! Please login.', 'warning')
                return redirect(url_for('login'))
            else:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            flash('No file selected! Please choose an image.', 'danger')
            return redirect(request.url)
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        disease, treatment = diagnose_disease(filename)
        session['last_uploaded'] = filename
        session['disease'] = disease
        session['treatment'] = treatment
        
        return render_template('upload_more.html', disease=disease, treatment=treatment, image=filename)
    
    return render_template('upload.html')

@app.route('/upload_more', methods=['POST'])
def upload_more():
    if request.form.get('upload_more') == 'yes':
        return redirect(url_for('upload'))
    return redirect(url_for('result'))

def diagnose_disease(image_filename):
    disease_dict = {
        "image1.jpg": ("Early Blight", "Use copper-based fungicides and remove infected leaves."),
        "image2.jpg": ("Late Blight", "Remove infected plants and use copper-based fungicides."),
        "image3.jpg": ("Septoria Leaf Spot", "Use copper-based fungicides and ensure good air circulation."),
        "image4.jpg": ("Fusarium Wilt", "Remove infected plants; avoid planting in same soil."),
        "image5.jpg": ("Verticillium Wilt", "Remove infected plants; avoid planting in same soil."),
        "image6.jpg": ("Anthracnose", "Remove infected fruit; use fungicides if necessary."),
        "image7.jpg": ("Buckeye Rot", "Remove infected fruit and use fungicides."),
        "image8.jpg": ("Bacterial Wilt", "Remove infected plants; no cure available."),
        "image9.jpg": ("Bacterial Canker", "Remove infected plant parts; use copper-based sprays."),
        "image10.jpg": ("Bacterial Spot", "Remove infected plant parts; use copper-based sprays.")
    }

    for key, (disease, treatment) in disease_dict.items():
        if key in image_filename.lower():
            return disease, treatment

    return "Unknown Disease", "Consult an expert."

@app.route('/result')
def result():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('result.html', disease=session.get('disease'), treatment=session.get('treatment'), image=session.get('last_uploaded'))

@app.route('/report')
def report():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('report.html', disease=session.get('disease'), treatment=session.get('treatment'), image=session.get('last_uploaded'))

@app.route('/print_report')
def print_report():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('print_report.html', disease=session.get('disease'), treatment=session.get('treatment'), image=session.get('last_uploaded'))

if __name__ == '__main__':
    app.run(debug=True)
