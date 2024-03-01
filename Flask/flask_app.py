# Import necessary modules
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired
from flask_wtf.csrf import CSRFProtect
from markupsafe import Markup
from docx import Document  # Added import for docx library
import configparser
import logging
from logging.handlers import RotatingFileHandler
import secrets

# Create Flask app instance
app = Flask(__name__)

logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler('events.log', maxBytes=10000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Read configuration from config.ini
config = configparser.ConfigParser()
config.optionxform = str
config.read('config.ini')

# Set Flask app configurations
app.secret_key = secrets.token_hex(16)
app.config['SESSION_PERMANENT'] = False 

# Get configuration values
DOCX_DIR = config['Paths']['DocxDirectory']  
credentials = dict(config['Credentials'])

# Enable CSRF protection
csrf = CSRFProtect(app)

# Define a form for login using Flask-WTF
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

# Define a form for access request using Flask-WTF
class AccessRequestForm(FlaskForm):
    full_name = StringField('Full Name', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired()])

# Function to retrieve data from the specified directory
def get_data_from_directory():
    data = {}

    for root, dirs, files in os.walk(DOCX_DIR):
        for docx_file in files:
            if docx_file.endswith(".docx"):
                doc_path = os.path.join(root, docx_file)
                doc = Document(doc_path)

                paragraphs = [paragraph.text for paragraph in doc.paragraphs]
                file_content = '\n\n'.join(paragraphs)

                relative_path = os.path.relpath(doc_path, DOCX_DIR)
                file_name_without_extension = os.path.splitext(relative_path)[0]

                directory_name = os.path.dirname(relative_path)

                if directory_name not in data:
                    data[directory_name] = []

                data[file_name_without_extension] = [{'name': file_name_without_extension, 'content': file_content}]

    return data

# Function to execute before each request
@app.before_request
def before_request():
    session.modified = True
    if request.endpoint not in ['login', 'static', 'request_access'] and 'username' not in session:
        return redirect(url_for('login'))

# Route to display a list of datasets
@app.route('/')
def list_datasets():
    data = get_data_from_directory()
    return render_template('index.html', data=data)

# Route for login with both GET and POST methods
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        # Invalidate the existing session if trying to access the login page
        session.pop('username', None)
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        if credentials.get(username) == password:
            # Set a unique session identifier for the browser tab
            session['session_token'] = os.urandom(24).hex()
            session['username'] = username
            flash('Successfully logged in', 'success')
            return redirect(url_for('list_datasets'))
        else:
            flash('Invalid credentials', 'danger')
            
    return render_template('login.html', form=form)

# Route to logout the user
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Route to read content from a specified sheet and file
@app.route('/read_content/<string:sheet>/<string:file_name>')
def read_content(sheet, file_name):
    data = get_data_from_directory()

    file_content = next((item['content'] for item in data.get(sheet, []) if item['name'] == file_name), None)

    if file_content is None:
        return "Content not found."

    paragraphs = file_content.split('\n\n')
    file_content_html = Markup(''.join(f'<p>{line}</p>' for line in paragraphs))
    
    return render_template('content.html', file_name=file_name, content=file_content_html)

# Route for requesting access
@app.route('/request-access', methods=['GET', 'POST'])
def request_access():
    form = AccessRequestForm()
    if form.validate_on_submit():
        full_name = form.full_name.data
        email = form.email.data

        # Write the details to a text file
        with open('access_requests.txt', 'a') as file:
            file.write(f'Full Name: {full_name}\nEmail: {email}\n\n')

        flash('Your access request has been submitted. Please await further instructions.', 'success')
        return redirect(url_for('login'))
    
    return render_template('request_access.html', form=form)

if __name__ == '__main__':
    app.logger.addHandler(file_handler)
    port = int(config['Paths'].get('Port', 5000))
    debug_setting = config['Paths'].getboolean('Debug', False)
    app.run(host='0.0.0.0', port=port, debug=debug_setting)
