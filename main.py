import io
import json
import os
from datetime import datetime, timedelta, timezone
import uuid
import time
import sys

import requests
# import pywhatkit as kit
from dotenv import load_dotenv
import sqlite3
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import (
    DateField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# Production configuration
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
else:
    app.config['DEBUG'] = True

# Add custom filter for JSON parsing in templates
@app.template_filter('from_json')
def from_json_filter(s):
    try:
        return json.loads(s)
    except:
        return []

# Email Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', True) == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', False) == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Infobip SMS Configuration
INFOBIP_API_KEY = os.environ.get('INFOBIP_API_KEY')
INFOBIP_BASE_URL = os.environ.get('INFOBIP_BASE_URL', 'https://api.infobip.com')
INFOBIP_SENDER = os.environ.get('INFOBIP_SENDER', 'SCHOOL')

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple in-memory cache
cache = {}
cache_timeout = 60  # 60 seconds

def get_cache_key(collection, data_id=None):
    return f"cache_{collection}_{data_id or 'all'}"

def is_cache_valid(cache_key):
    if cache_key not in cache:
        return False
    return (datetime.now(timezone.utc) - cache[cache_key]['timestamp']).seconds < cache_timeout

def set_cache(cache_key, data):
    cache[cache_key] = {
        'data': data,
        'timestamp': datetime.now(timezone.utc)
    }

def get_cache(cache_key):
    if is_cache_valid(cache_key):
        return cache[cache_key]['data']
    return None

def clear_cache(collection=None):
    if collection:
        keys_to_remove = [k for k in cache.keys() if k.startswith(f"cache_{collection}")]
        for key in keys_to_remove:
            del cache[key]
    else:
        cache.clear()

# Helper functions for ReplDB

# ==================== Database Setup (SQLite3 + PostgreSQL Support) ====================
# Determine which database to use
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL and DATABASE_URL.startswith('postgresql')

if USE_POSTGRES:
    print("[INIT] Using PostgreSQL database")
    DATABASE = None
else:
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'school_management.db')
    print(f"[INIT] Using SQLite database: {DATABASE}")

def get_db_connection():
    """Get database connection (SQLite or PostgreSQL)"""
    if USE_POSTGRES:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize database with appropriate schema"""
    try:
        print(f"[INIT] Initializing database...")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_data (
                        collection TEXT,
                        id TEXT,
                        data TEXT,
                        PRIMARY KEY (collection, id)
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_data (
                        collection TEXT,
                        id TEXT,
                        data TEXT,
                        PRIMARY KEY (collection, id)
                    )
                ''')
            conn.commit()
        print(f"[INIT] Database initialized successfully")
        
        # Verify admin exists
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM app_data WHERE collection=%s', ('admin',)) if USE_POSTGRES else cursor.execute('SELECT COUNT(*) as count FROM app_data WHERE collection="admin"')
            admin_count = cursor.fetchone()
            admin_users = admin_count[0] if USE_POSTGRES else admin_count['count']
            print(f"[INIT] Admin users in database: {admin_users}")
    except Exception as e:
        print(f"Error initializing DB: {e}")
        sys.exit(1)

# Initialize DB on startup
init_db()
# Clear cache on startup
clear_cache()
print("[INIT] Cache cleared on startup")

# ==================== Database Helpers ====================
def save_to_db(collection, data):
    """Save data to database with auto-generated ID"""
    try:
        data_id = str(uuid.uuid4())
        data['id'] = data_id
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute(
                    "INSERT INTO app_data (collection, id, data) VALUES (%s, %s, %s)",
                    (collection, data_id, json.dumps(data))
                )
            else:
                cursor.execute(
                    "INSERT INTO app_data (collection, id, data) VALUES (?, ?, ?)",
                    (collection, data_id, json.dumps(data))
                )
            conn.commit()
            
        clear_cache(collection)
        return data_id
    except Exception as e:
        print(f"Error saving to DB: {e}")
        return None

def get_from_db(collection, data_id=None):
    """Get data from database with caching"""
    try:
        cache_key = get_cache_key(collection, data_id)
        cached_data = get_cache(cache_key)
        if cached_data is not None:
            return cached_data

        data = None
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if data_id:
                if USE_POSTGRES:
                    cursor.execute(
                        "SELECT data FROM app_data WHERE collection = %s AND id = %s",
                        (collection, data_id)
                    )
                else:
                    cursor.execute(
                        "SELECT data FROM app_data WHERE collection = ? AND id = ?",
                        (collection, data_id)
                    )
                row = cursor.fetchone()
                if row:
                    if USE_POSTGRES:
                        data = json.loads(row[0])
                    else:
                        data = json.loads(row['data'])
            else:
                if USE_POSTGRES:
                    cursor.execute(
                        "SELECT data FROM app_data WHERE collection = %s",
                        (collection,)
                    )
                else:
                    cursor.execute(
                        "SELECT data FROM app_data WHERE collection = ?",
                        (collection,)
                    )
                rows = cursor.fetchall()
                if USE_POSTGRES:
                    data = [json.loads(row[0]) for row in rows]
                else:
                    data = [json.loads(row['data']) for row in rows]

        if data is not None:
            set_cache(cache_key, data)
        return data if data_id else (data or [])
    except Exception as e:
        print(f"Error getting from DB: {e}")
        return None if data_id else []

def update_in_db(collection, data_id, data):
    """Update data in database"""
    try:
        data['id'] = data_id
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute(
                    "UPDATE app_data SET data = %s WHERE collection = %s AND id = %s",
                    (json.dumps(data), collection, data_id)
                )
            else:
                cursor.execute(
                    "UPDATE app_data SET data = ? WHERE collection = ? AND id = ?",
                    (json.dumps(data), collection, data_id)
                )
            conn.commit()
            
        clear_cache(collection)
        return True
    except Exception as e:
        print(f"Error updating in DB: {e}")
        return False

def delete_from_db(collection, data_id):
    """Delete data from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute(
                    "DELETE FROM app_data WHERE collection = %s AND id = %s",
                    (collection, data_id)
                )
            else:
                cursor.execute(
                    "DELETE FROM app_data WHERE collection = ? AND id = ?",
                    (collection, data_id)
                )
            conn.commit()
            if cursor.rowcount > 0:
                clear_cache(collection)
                return True
        return False
    except Exception as e:
        print(f"Error deleting from DB: {e}")
        return False

def query_db(collection, **filters):
    """Query data with filters (currently client-side to maintain logic)"""
    try:
        # Note: In a larger app, we would use SQL for filtering.
        # Keeping current logic to ensure existing filters work as expected.
        items = get_from_db(collection)
        if not items:
            return []

        filtered_items = []
        for item in items:
            if not item: continue
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered_items.append(item)
        return filtered_items
    except Exception as e:
        print(f"Error querying DB: {e}")
        return []


# Data Models using ReplDB
class Admin(UserMixin):
    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.username = data.get('username')
            self.email = data.get('email') 
            self.password_hash = data.get('password_hash')
            self.created_at = data.get('created_at', datetime.now(timezone.utc).isoformat())
        else:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def save(self):
        data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at
        }
        if hasattr(self, 'id') and self.id:
            update_in_db('admin', self.id, data)
        else:
            self.id = save_to_db('admin', data)
        return self.id

    @staticmethod
    def find_by_username(username):
        print(f"[ADMIN_LOOKUP] Finding admin with username: '{username}' (type: {type(username).__name__})")
        
        # Method 1: Try query_db with filter
        admins = query_db('admin', username=username)
        print(f"[ADMIN_LOOKUP] query_db returned: {len(admins) if isinstance(admins, list) else 'not a list'} results")
        
        if admins and len(admins) > 0:
            print(f"[ADMIN_LOOKUP] Found via query_db: {admins[0].get('username')}")
            return Admin(admins[0])
        
        # Method 2: Fallback - get all admins and search manually
        print(f"[ADMIN_LOOKUP] Fallback: getting all admins from database")
        all_admins = get_from_db('admin')
        print(f"[ADMIN_LOOKUP] All admins count: {len(all_admins) if isinstance(all_admins, list) else 0}")
        
        if isinstance(all_admins, list) and len(all_admins) > 0:
            for admin_data in all_admins:
                if admin_data and admin_data.get('username') == username:
                    print(f"[ADMIN_LOOKUP] Found via fallback search: {admin_data.get('username')}")
                    return Admin(admin_data)
                elif admin_data:
                    print(f"[ADMIN_LOOKUP] Checking admin: '{admin_data.get('username')}' vs '{username}' - Match: {admin_data.get('username') == username}")
        
        print(f"[ADMIN_LOOKUP] Admin with username '{username}' not found")
        return None

    @staticmethod
    def find_by_id(admin_id):
        data = get_from_db('admin', admin_id)
        return Admin(data) if data else None

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    roll_number = StringField('Roll Number', validators=[DataRequired(), Length(max=20)])
    class_id = SelectField('Class', coerce=str, validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)])
    email = StringField('Email', validators=[Email(message='Please enter a valid email address')])
    guardian_phone = StringField('Guardian Phone', validators=[DataRequired(), Length(max=15)])
    guardian_name = StringField('Guardian Name', validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    address = TextAreaField('Address')

class SMSTemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    template_type = SelectField('Type', choices=[
        ('fee_due', 'Fee Due Reminder'),
        ('exam_reminder', 'Exam Reminder'),
        ('result_publish', 'Result Publication'),
        ('general', 'General Message')
    ], validators=[DataRequired()])
    message = TextAreaField('Message Template', validators=[DataRequired()])

class ClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired(), Length(max=50)])
    section = StringField('Section', validators=[DataRequired(), Length(max=10)])
    teacher_id = SelectField('Class Teacher', coerce=str, validators=[])
    capacity = IntegerField('Capacity', validators=[DataRequired()], default=40)

class TeacherForm(FlaskForm):
    name = StringField('Teacher Name', validators=[DataRequired(), Length(max=100)])
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=20)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)])
    email = StringField('Email', validators=[Email(message='Please enter a valid email address')])
    subject = StringField('Subject', validators=[Length(max=100)])
    salary = FloatField('Salary')
    joining_date = DateField('Joining Date', validators=[DataRequired()])

@login_manager.user_loader
def load_user(user_id):
    return Admin.find_by_id(user_id)

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        # Clear cache before checking admin
        clear_cache()
        
        admin = Admin.find_by_username(form.username.data)
        print(f"[DEBUG] Login attempt - Username: {form.username.data}, Found: {admin is not None}")
        
        if admin:
            is_valid = check_password_hash(admin.password_hash, form.password.data)
            print(f"[DEBUG] Password check result: {is_valid}")
            
            if is_valid:
                login_user(admin)
                print(f"[DEBUG] User logged in successfully")
                return redirect(url_for('dashboard'))
        
        print(f"[DEBUG] Login failed for user: {form.username.data}")
        flash('Invalid username or password', 'error')
    else:
        print(f"[DEBUG] Form validation failed: {form.errors}")

    return render_template('login_modern.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Dashboard statistics with optimized queries
        students = query_db('student', is_active=True) or []
        total_students = len(students)

        teachers = query_db('teacher', is_active=True) or []
        total_teachers = len(teachers)

        classes = get_from_db('class') or []
        total_classes = len(classes)

        # Today's attendance
        today = datetime.now().date().isoformat()
        today_attendance_records = query_db('attendance', date=today) or []
        today_attendance = len(today_attendance_records)
        attendance_percentage = 0
        if total_students > 0:
            attendance_percentage = round((today_attendance / total_students) * 100, 2)

        # Teacher attendance today
        today_teacher_attendance = query_db('teacher_attendance', date=today) or []
        teacher_present = len([a for a in today_teacher_attendance if a.get('status') == 'Present'])
        teacher_attendance_percentage = 0
        if total_teachers > 0:
            teacher_attendance_percentage = round((teacher_present / total_teachers) * 100, 2)

        # Fee collection summary
        unpaid_fees = query_db('fee', is_paid=False) or []
        total_fees = sum(fee.get('amount', 0) for fee in unpaid_fees if fee)

        paid_fees = query_db('fee', is_paid=True) or []
        collected_fees = sum(fee.get('amount', 0) for fee in paid_fees if fee)

        # Recent SMS logs
        all_sms = get_from_db('sms_log') or []
        recent_sms = sorted([sms for sms in all_sms if sms], key=lambda x: x.get('sent_at', ''), reverse=True)[:5]
        
        # SMS sent today
        sms_sent_today = len([sms for sms in all_sms if sms and sms.get('sent_at', '').startswith(today)])

        # Check if mobile view is requested
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
        
        # Use mobile template if mobile device or mobile parameter is set
        if is_mobile or request.args.get('view') == 'mobile':
            return render_template('dashboard_mobile.html', 
                                 total_students=total_students,
                                 total_teachers=total_teachers,
                                 total_classes=total_classes,
                                 today_attendance=today_attendance,
                                 attendance_percentage=attendance_percentage,
                                 teacher_attendance_percentage=teacher_attendance_percentage,
                                 teacher_present=teacher_present,
                                 total_fees=total_fees,
                                 collected_fees=collected_fees,
                                 recent_sms=recent_sms,
                                 sms_sent_today=sms_sent_today,
                                 datetime=datetime)
        
        return render_template('dashboard_modern.html', 
                             total_students=total_students,
                             total_teachers=total_teachers,
                             total_classes=total_classes,
                             today_attendance=today_attendance,
                             attendance_percentage=attendance_percentage,
                             teacher_attendance_percentage=teacher_attendance_percentage,
                             teacher_present=teacher_present,
                             total_fees=total_fees,
                             collected_fees=collected_fees,
                             recent_sms=recent_sms,
                             sms_sent_today=sms_sent_today,
                             datetime=datetime)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('dashboard.html', 
                             total_students=0,
                             total_teachers=0,
                             total_classes=0,
                             attendance_percentage=0,
                             total_fees=0,
                             collected_fees=0,
                             recent_sms=[],
                             sms_sent_today=0,
                             datetime=datetime)

@app.route('/students')
@login_required
def students():
    search = request.args.get('search', '')
    class_filter = request.args.get('class_filter', '')
    status_filter = request.args.get('status_filter', 'all')

    # Get all students
    all_students = get_from_db('student')

    # Filter students
    filtered_students = []
    for student in all_students:
        # Apply filters
        if search and search.lower() not in student.get('name', '').lower() and search not in student.get('roll_number', ''):
            continue
        if class_filter and student.get('class_id') != class_filter:
            continue
        if status_filter == 'active' and not student.get('is_active', True):
            continue
        elif status_filter == 'inactive' and student.get('is_active', True):
            continue

        # Create a copy to avoid modifying original database object
        student_copy = dict(student)

        # Convert date strings to datetime objects for template
        if student_copy.get('date_of_birth'):
            try:
                if isinstance(student_copy['date_of_birth'], str):
                    student_copy['date_of_birth'] = datetime.fromisoformat(student_copy['date_of_birth']).date()
            except:
                student_copy['date_of_birth'] = None

        # Add class information
        class_data = get_from_db('class', student.get('class_id'))
        if class_data:
            student_copy['class_name'] = f"{class_data.get('name')} - {class_data.get('section')}"

        filtered_students.append(student_copy)

    classes = get_from_db('class')
    return render_template('students.html', students=filtered_students, classes=classes)

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    form = StudentForm()

    # Get all classes and add a default empty option
    classes = get_from_db('class')
    form.class_id.choices = [('', 'Select a Class')] + [(c.get('id'), f"{c.get('name')} - {c.get('section')}") for c in classes]

    if form.validate_on_submit():
        # Check if class_id is valid
        if not form.class_id.data:
            flash('Please select a valid class', 'error')
            return render_template('add_student.html', form=form)

        # Check if roll number already exists
        existing_students = query_db('student', roll_number=form.roll_number.data)
        if existing_students:
            flash('Roll number already exists. Please use a different roll number.', 'error')
            return render_template('add_student.html', form=form)

        try:
            student_data = {
                'name': form.name.data,
                'roll_number': form.roll_number.data,
                'class_id': form.class_id.data,
                'phone': form.phone.data,
                'email': form.email.data,
                'guardian_phone': form.guardian_phone.data,
                'guardian_name': form.guardian_name.data,
                'date_of_birth': form.date_of_birth.data.isoformat(),
                'address': form.address.data,
                'is_active': True,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            save_to_db('student', student_data)
            flash('Student added successfully!', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            flash('Error adding student. Please try again.', 'error')

    return render_template('add_student.html', form=form, classes=classes)

@app.route('/classes')
@login_required
def classes():
    classes = get_from_db('class')
    teachers = query_db('teacher', is_active=True)

    # Add teacher information and student count to classes
    for class_item in classes:
        if class_item.get('teacher_id'):
            teacher_data = get_from_db('teacher', class_item.get('teacher_id'))
            if teacher_data:
                class_item['teacher_name'] = teacher_data.get('name')

        # Count students in this class
        students_in_class = query_db('student', class_id=class_item.get('id'), is_active=True)
        class_item['student_count'] = len(students_in_class)
        class_item['students'] = students_in_class  # For template compatibility

    return render_template('classes.html', classes=classes, teachers=teachers)

@app.route('/add_class', methods=['GET', 'POST'])
@login_required
def add_class():
    form = ClassForm()
    teachers = query_db('teacher', is_active=True)
    form.teacher_id.choices = [('', 'Select Teacher')] + [(t.get('id'), t.get('name')) for t in teachers]

    if form.validate_on_submit():
        class_data = {
            'name': form.name.data,
            'section': form.section.data,
            'teacher_id': form.teacher_id.data if form.teacher_id.data else None,
            'capacity': form.capacity.data,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        save_to_db('class', class_data)
        flash('Class created successfully!', 'success')
        return redirect(url_for('classes'))

    return render_template('add_class.html', form=form)

@app.route('/delete_class/<class_id>', methods=['POST'])
@login_required
def delete_class(class_id):
    try:
        # Get class data first
        class_data = get_from_db('class', class_id)
        if not class_data:
            flash('Class not found.', 'error')
            return redirect(url_for('classes'))

        class_name = f"{class_data.get('name', '')} - {class_data.get('section', '')}"

        # Use helper function to check if class can be deleted
        can_delete, message = can_delete_class(class_id)
        
        if not can_delete:
            if "active student" in message or "exam record" in message or "fee record" in message:
                flash(f'Cannot delete class "{class_name}": {message}', 'error')
            else:
                flash(f'Cannot delete class "{class_name}": {message}', 'warning')
            return redirect(url_for('classes'))

        # If all checks pass, delete the class
        if delete_from_db('class', class_id):
            flash(f'Class "{class_name}" deleted successfully!', 'success')
        else:
            flash(f'Error deleting class "{class_name}" from database.', 'error')

    except Exception as e:
        print(f"Delete class error: {e}")
        flash('Error deleting class. Please try again.', 'error')

    return redirect(url_for('classes'))

@app.route('/transfer_students/<class_id>')
@login_required
def transfer_students_page(class_id):
    source_class = get_from_db('class', class_id)
    if not source_class:
        flash('Class not found.', 'error')
        return redirect(url_for('classes'))

    # Get all other classes
    all_classes = get_from_db('class')
    target_classes = [c for c in all_classes if c.get('id') != class_id]

    students = query_db('student', class_id=class_id, is_active=True)

    return render_template('transfer_students.html', 
                         source_class=source_class, 
                         target_classes=target_classes, 
                         students=students)

@app.route('/transfer_students/<class_id>', methods=['POST'])
@login_required
def transfer_students(class_id):
    target_class_id = request.form.get('target_class_id')
    student_ids = request.form.getlist('student_ids')

    if not target_class_id or not student_ids:
        flash('Please select target class and students to transfer.', 'error')
        return redirect(url_for('transfer_students_page', class_id=class_id))

    try:
        # Update students' class
        for student_id in student_ids:
            student_data = get_from_db('student', student_id)
            if student_data:
                student_data['class_id'] = target_class_id
                update_in_db('student', student_id, student_data)

        flash(f'Successfully transferred {len(student_ids)} students!', 'success')
        return redirect(url_for('classes'))
    except Exception:
        flash('Error transferring students.', 'error')
        return redirect(url_for('transfer_students_page', class_id=class_id))

@app.route('/teachers')
@login_required
def teachers():
    teachers = query_db('teacher', is_active=True)

    # Create a copy of teachers data and convert date strings to datetime objects for template
    teachers_display = []
    for teacher in teachers:
        teacher_copy = dict(teacher)
        if teacher_copy.get('joining_date'):
            try:
                if isinstance(teacher_copy['joining_date'], str):
                    teacher_copy['joining_date'] = datetime.fromisoformat(teacher_copy['joining_date']).date()
            except:
                teacher_copy['joining_date'] = None
        teachers_display.append(teacher_copy)

    return render_template('teachers.html', teachers=teachers_display)

@app.route('/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    form = TeacherForm()

    if form.validate_on_submit():
        teacher_data = {
            'name': form.name.data,
            'employee_id': form.employee_id.data,
            'phone': form.phone.data,
            'email': form.email.data,
            'subject': form.subject.data,
            'salary': form.salary.data,
            'joining_date': form.joining_date.data.isoformat(),
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        save_to_db('teacher', teacher_data)
        flash('Teacher added successfully!', 'success')
        return redirect(url_for('teachers'))

    return render_template('add_teacher.html', form=form)

@app.route('/delete_teacher/<teacher_id>', methods=['POST'])
@login_required
def delete_teacher(teacher_id):
    try:
        teacher_data = get_from_db('teacher', teacher_id)
        if teacher_data:
            teacher_data['is_active'] = False
            update_in_db('teacher', teacher_id, teacher_data)
            flash('Teacher deactivated successfully!', 'success')
        else:
            flash('Teacher not found.', 'error')
    except Exception:
        flash('Error deactivating teacher.', 'error')

    return redirect(url_for('teachers'))

@app.route('/delete_student/<student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    try:
        student_data = get_from_db('student', student_id)
        if student_data:
            student_data['is_active'] = False
            update_in_db('student', student_id, student_data)
            flash('Student deactivated successfully!', 'success')
        else:
            flash('Student not found.', 'error')
    except Exception:
        flash('Error deactivating student.', 'error')

    return redirect(url_for('students'))

@app.route('/sms_management')
@login_required
def sms_management():
    templates = query_db('sms_template', is_active=True)
    all_logs = get_from_db('sms_log')
    recent_logs = sorted(all_logs, key=lambda x: x.get('sent_at', ''), reverse=True)[:10]
    return render_template('sms_management.html', templates=templates, recent_logs=recent_logs)

@app.route('/add_sms_template', methods=['GET', 'POST'])
@login_required
def add_sms_template():
    form = SMSTemplateForm()

    if form.validate_on_submit():
        # Define placeholders based on template type
        placeholders = {
            'fee_due': ['student_name', 'guardian_name', 'due_amount', 'due_date'],
            'exam_reminder': ['student_name', 'exam_name', 'exam_date', 'exam_time'],
            'result_publish': ['student_name', 'exam_name', 'total_marks', 'obtained_marks', 'grade'],
            'general': ['student_name', 'guardian_name', 'class_name']
        }

        template_data = {
            'name': form.name.data,
            'template_type': form.template_type.data,
            'message': form.message.data,
            'placeholders': json.dumps(placeholders.get(form.template_type.data, [])),
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        save_to_db('sms_template', template_data)
        flash('SMS template created successfully!', 'success')
        return redirect(url_for('sms_management'))

    return render_template('add_sms_template.html', form=form)

@app.route('/attendance')
@login_required
def attendance():
    date = request.args.get('date', datetime.now().date().strftime('%Y-%m-%d'))
    class_id = request.args.get('class_id', '')
    status_filter = request.args.get('status_filter', '')

    # Get students
    if class_id:
        students = query_db('student', class_id=class_id, is_active=True)
    else:
        students = query_db('student', is_active=True)

    # Add class information to students
    for student in students:
        class_data = get_from_db('class', student.get('class_id'))
        if class_data:
            student['class_name'] = f"{class_data.get('name')} - {class_data.get('section')}"

    classes = get_from_db('class')

    # Get existing attendance for the date
    attendance_records = {}
    existing_attendance = query_db('attendance', date=date)
    for record in existing_attendance:
        attendance_records[record.get('student_id')] = record.get('status')

    # Apply status filter
    if status_filter:
        filtered_students = []
        for student in students:
            student_id = student.get('id')
            current_status = attendance_records.get(student_id)
            
            if status_filter == 'present' and current_status == 'Present':
                filtered_students.append(student)
            elif status_filter == 'absent' and current_status == 'Absent':
                filtered_students.append(student)
            elif status_filter == 'not_marked' and not current_status:
                filtered_students.append(student)
        students = filtered_students

    # Sort students by class and roll number
    students.sort(key=lambda x: (x.get('class_name', ''), x.get('roll_number', '')))

    return render_template('attendance.html', 
                         students=students, 
                         classes=classes, 
                         date=date,
                         attendance_records=attendance_records)

@app.route('/teacher_attendance')
@login_required
def teacher_attendance():
    date = request.args.get('date', datetime.now().date().strftime('%Y-%m-%d'))

    # Get all active teachers
    teachers = query_db('teacher', is_active=True)

    # Get existing teacher attendance for the date
    attendance_records = {}
    existing_attendance = query_db('teacher_attendance', date=date)
    for record in existing_attendance:
        attendance_records[record.get('teacher_id')] = record.get('status')

    return render_template('teacher_attendance.html', 
                         teachers=teachers, 
                         date=date,
                         attendance_records=attendance_records)

@app.route('/mark_teacher_attendance', methods=['POST'])
@login_required
def mark_teacher_attendance():
    date = request.form.get('date')
    attendance_data = request.form.to_dict()

    for key, status in attendance_data.items():
        if key.startswith('teacher_'):
            teacher_id = key.replace('teacher_', '')

            # Check if attendance already exists
            existing = query_db('teacher_attendance', teacher_id=teacher_id, date=date)

            if existing:
                # Update existing record
                existing[0]['status'] = status
                update_in_db('teacher_attendance', existing[0]['id'], existing[0])
            else:
                # Create new record
                attendance_record = {
                    'teacher_id': teacher_id,
                    'date': date,
                    'status': status,
                    'marked_by': current_user.id,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                save_to_db('teacher_attendance', attendance_record)

    flash('Teacher attendance marked successfully!', 'success')
    return redirect(url_for('teacher_attendance'))

@app.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    try:
        date = request.form.get('date')
        if not date:
            flash('তারিখ নির্বাচন করুন', 'error')
            return redirect(url_for('attendance'))

        attendance_data = request.form.to_dict()
        marked_count = 0
        updated_count = 0

        for key, status in attendance_data.items():
            if key.startswith('student_'):
                student_id = key.replace('student_', '')
                
                # Validate student exists
                student = get_from_db('student', student_id)
                if not student:
                    continue

                # Validate status
                if status not in ['Present', 'Absent', 'Late']:
                    continue

                # Check if attendance already exists
                existing = query_db('attendance', student_id=student_id, date=date)

                if existing:
                    # Update existing record
                    existing[0]['status'] = status
                    existing[0]['updated_at'] = datetime.now(timezone.utc).isoformat()
                    existing[0]['updated_by'] = current_user.id
                    if update_in_db('attendance', existing[0]['id'], existing[0]):
                        updated_count += 1
                else:
                    # Create new record
                    attendance_record = {
                        'student_id': student_id,
                        'date': date,
                        'status': status,
                        'marked_by': current_user.id,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    if save_to_db('attendance', attendance_record):
                        marked_count += 1

        # Send SMS notifications if requested
        send_sms = request.form.get('send_sms')
        if send_sms == 'true':
            try:
                # Send SMS to parents of absent students
                absent_students = []
                for key, status in attendance_data.items():
                    if key.startswith('student_') and status == 'Absent':
                        student_id = key.replace('student_', '')
                        student = get_from_db('student', student_id)
                        if student and student.get('guardian_phone'):
                            absent_students.append(student)

                sms_sent = 0
                for student in absent_students:
                    message = f"প্রিয় {student.get('guardian_name', 'অভিভাবক')}, আজ {student.get('name')} স্কুলে অনুপস্থিত ছিল। তারিখ: {date}। - স্কুল ম্যানেজমেন্ট"
                    
                    if send_infobip_sms(student.get('guardian_phone'), message):
                        # Log SMS
                        sms_log = {
                            'phone_number': student.get('guardian_phone'),
                            'message': message,
                            'status': 'sent',
                            'template_id': None,
                            'sent_at': datetime.now(timezone.utc).isoformat(),
                            'sent_by': current_user.id,
                            'sms_type': 'attendance_alert'
                        }
                        save_to_db('sms_log', sms_log)
                        sms_sent += 1

                if sms_sent > 0:
                    flash(f'উপস্থিতি সংরক্ষিত হয়েছে! {sms_sent}টি অনুপস্থিতির SMS পাঠানো হয়েছে।', 'success')
                else:
                    flash('উপস্থিতি সংরক্ষিত হয়েছে! কিন্তু SMS পাঠাতে সমস্যা হয়েছে।', 'warning')
            except Exception as sms_error:
                print(f"SMS sending error: {sms_error}")
                flash('উপস্থিতি সংরক্ষিত হয়েছে! কিন্তু SMS পাঠাতে সমস্যা হয়েছে।', 'warning')
        else:
            total_actions = marked_count + updated_count
            if total_actions > 0:
                flash(f'উপস্থিতি সফলভাবে সংরক্ষিত হয়েছে! ({marked_count} নতুন, {updated_count} আপডেট)', 'success')
            else:
                flash('কোনো উপস্থিতি চিহ্নিত করা হয়নি।', 'warning')

        return redirect(url_for('attendance', date=date))

    except Exception as e:
        print(f"Attendance marking error: {e}")
        flash('উপস্থিতি সংরক্ষণে সমস্যা হয়েছে। আবার চেষ্টা করুন।', 'error')
        return redirect(url_for('attendance'))

@app.route('/fees')
@login_required
def fees():
    status_filter = request.args.get('status', 'all')

    all_fees = get_from_db('fee')

    # Filter fees and add student information
    filtered_fees = []
    current_date = datetime.now().date().isoformat()

    for fee in all_fees:
        # Apply status filter
        if status_filter == 'paid' and not fee.get('is_paid', False):
            continue
        elif status_filter == 'unpaid' and fee.get('is_paid', False):
            continue
        elif status_filter == 'overdue' and (fee.get('is_paid', False) or fee.get('due_date', '') >= current_date):
            continue

        # Add student information
        student_data = get_from_db('student', fee.get('student_id'))
        if student_data:
            fee['student_name'] = student_data.get('name')
            fee['student_roll'] = student_data.get('roll_number')

            # Add class information
            class_data = get_from_db('class', student_data.get('class_id'))
            if class_data:
                fee['class_name'] = f"{class_data.get('name')} - {class_data.get('section')}"

        filtered_fees.append(fee)

    return render_template('fees.html', fees=filtered_fees, current_date=current_date)

@app.route('/add_fee', methods=['GET', 'POST'])
@login_required
def add_fee():
    if request.method == 'POST':
        fee_data = {
            'student_id': request.form['student_id'],
            'fee_type': request.form['fee_type'],
            'amount': float(request.form['amount']),
            'due_date': request.form['due_date'],
            'is_paid': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        save_to_db('fee', fee_data)
        flash('Fee record added successfully!', 'success')
        return redirect(url_for('fees'))

    students = query_db('student', is_active=True)
    return render_template('add_fee.html', students=students)

@app.route('/mark_fee_paid/<fee_id>')
@login_required
def mark_fee_paid(fee_id):
    fee_data = get_from_db('fee', fee_id)
    if fee_data:
        fee_data['is_paid'] = True
        fee_data['paid_date'] = datetime.now().date().isoformat()
        update_in_db('fee', fee_id, fee_data)
        flash('Fee marked as paid!', 'success')
    else:
        flash('Fee record not found.', 'error')
    return redirect(url_for('fees'))

@app.route('/exams')
@login_required
def exams():
    exams = get_from_db('exam')

    # Create copies and add class information to exams and convert dates
    exams_display = []
    for exam in exams:
        exam_copy = dict(exam)
        class_data = get_from_db('class', exam.get('class_id'))
        if class_data:
            exam_copy['class_name'] = f"{class_data.get('name')} - {class_data.get('section')}"

        # Convert date strings to datetime objects for template
        if exam_copy.get('exam_date'):
            try:
                if isinstance(exam_copy['exam_date'], str):
                    exam_copy['exam_date'] = datetime.fromisoformat(exam_copy['exam_date']).date()
            except:
                exam_copy['exam_date'] = None

        exams_display.append(exam_copy)

    classes = get_from_db('class')
    return render_template('exams.html', exams=exams_display, classes=classes)

@app.route('/add_exam', methods=['GET', 'POST'])
@login_required
def add_exam():
    if request.method == 'POST':
        exam_data = {
            'name': request.form['name'],
            'class_id': request.form['class_id'],
            'subject': request.form['subject'],
            'exam_date': request.form['exam_date'],
            'total_marks': int(request.form['total_marks']),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        save_to_db('exam', exam_data)
        flash('Exam added successfully!', 'success')
        return redirect(url_for('exams'))

    classes = get_from_db('class')
    return render_template('add_exam.html', classes=classes)

@app.route('/exam_results/<exam_id>')
@login_required
def exam_results(exam_id):
    try:
        exam = get_from_db('exam', exam_id)
        if not exam:
            flash('Exam not found', 'error')
            return redirect(url_for('exams'))

        # Add class information to exam
        class_data = get_from_db('class', exam.get('class_id'))
        if class_data:
            exam['class_section'] = {
                'name': class_data.get('name'),
                'section': class_data.get('section')
            }

        # Convert exam date
        if exam.get('exam_date'):
            try:
                if isinstance(exam['exam_date'], str):
                    exam['exam_date'] = datetime.fromisoformat(exam['exam_date']).date()
            except:
                pass

        # Get students in the class
        students_in_class = query_db('student', class_id=exam.get('class_id'), is_active=True) or []

        # Get results for this exam
        exam_results = query_db('result', exam_id=exam_id) or []

        # Combine results with student data
        results = []
        for result in exam_results:
            student = get_from_db('student', result.get('student_id'))
            if student:
                # Calculate grade
                marks_obtained = result.get('marks_obtained', 0)
                total_marks = exam.get('total_marks', 100)
                grade = calculate_grade(marks_obtained, total_marks)
                result['grade'] = grade
                results.append((result, student))

        return render_template('exam_results.html', 
                             exam=exam, 
                             results=results, 
                             students_in_class=students_in_class)

    except Exception as e:
        print(f"Exam results error: {e}")
        flash('Error loading exam results', 'error')
        return redirect(url_for('exams'))

@app.route('/add_result/<exam_id>', methods=['POST'])
@login_required
def add_result(exam_id):
    try:
        student_id = request.form.get('student_id')
        marks_obtained = float(request.form.get('marks_obtained', 0))

        # Check if result already exists
        existing_results = query_db('result', exam_id=exam_id, student_id=student_id)
        if existing_results:
            # Update existing result
            existing_results[0]['marks_obtained'] = marks_obtained
            update_in_db('result', existing_results[0]['id'], existing_results[0])
            flash('Result updated successfully!', 'success')
        else:
            # Create new result
            result_data = {
                'exam_id': exam_id,
                'student_id': student_id,
                'marks_obtained': marks_obtained,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            save_to_db('result', result_data)
            flash('Result added successfully!', 'success')

        return redirect(url_for('exam_results', exam_id=exam_id))

    except Exception as e:
        flash('Error adding result', 'error')
        return redirect(url_for('exam_results', exam_id=exam_id))

@app.route('/send_exam_reminder/<exam_id>')
@login_required
def send_exam_reminder(exam_id):
    try:
        exam = get_from_db('exam', exam_id)
        if not exam:
            flash('Exam not found', 'error')
            return redirect(url_for('exams'))

        # Get students in the class
        students = query_db('student', class_id=exam.get('class_id'), is_active=True)

        # Get exam reminder template
        templates = query_db('sms_template', template_type='exam_reminder', is_active=True)
        if not templates:
            flash('No exam reminder template found', 'error')
            return redirect(url_for('exams'))

        template = templates[0]
        sent_count = 0

        for student in students:
            if not student.get('guardian_phone'):
                continue

            message = template.get('message', '')
            message = message.replace('{student_name}', student.get('name', ''))
            message = message.replace('{guardian_name}', student.get('guardian_name', ''))
            message = message.replace('{exam_name}', exam.get('name', ''))
            message = message.replace('{exam_date}', exam.get('exam_date', ''))

            if send_infobip_sms(student.get('guardian_phone'), message):
                # Log SMS
                sms_log = {
                    'phone_number': student.get('guardian_phone'),
                    'message': message,
                    'status': 'sent',
                    'template_id': template.get('id'),
                    'sent_at': datetime.now(timezone.utc).isoformat(),
                    'sent_by': current_user.id
                }
                save_to_db('sms_log', sms_log)
                sent_count += 1

        flash(f'Exam reminder sent to {sent_count} parents!', 'success')
        return redirect(url_for('exams'))

    except Exception as e:
        flash('Error sending exam reminders', 'error')
        return redirect(url_for('exams'))

@app.route('/reports')
@login_required
def reports():
    try:
        # Basic statistics
        students = query_db('student', is_active=True) or []
        total_students = len(students)

        teachers = query_db('teacher', is_active=True) or []
        total_teachers = len(teachers)

        classes = get_from_db('class') or []
        total_classes = len(classes)

        # Monthly fee collection
        current_month = datetime.now().month
        current_year = datetime.now().year

        paid_fees = query_db('fee', is_paid=True) or []
        monthly_collection = 0
        for fee in paid_fees:
            if fee and fee.get('paid_date'):
                try:
                    paid_date = datetime.fromisoformat(fee['paid_date'])
                    if paid_date.month == current_month and paid_date.year == current_year:
                        monthly_collection += fee.get('amount', 0)
                except:
                    pass

        # Pending fees
        unpaid_fees = query_db('fee', is_paid=False) or []
        pending_fees = sum(fee.get('amount', 0) for fee in unpaid_fees if fee)

        # Attendance statistics
        today = datetime.now().date().isoformat()
        today_attendance = query_db('attendance', date=today) or []
        today_present = len([a for a in today_attendance if a and a.get('status') == 'Present'])

        # SMS statistics
        all_sms = get_from_db('sms_log') or []
        total_sms_sent = len([s for s in all_sms if s and s.get('status') == 'sent'])

        sms_this_month = 0
        for sms in all_sms:
            if sms and sms.get('sent_at') and sms.get('status') == 'sent':
                try:
                    sent_date = datetime.fromisoformat(sms['sent_at'])
                    if sent_date.month == current_month and sent_date.year == current_year:
                        sms_this_month += 1
                except:
                    pass

        return render_template('reports.html',
                             total_students=total_students,
                             total_teachers=total_teachers,
                             total_classes=total_classes,
                             monthly_collection=monthly_collection,
                             pending_fees=pending_fees,
                             today_attendance=len(today_attendance),
                             today_present=today_present,
                             total_sms_sent=total_sms_sent,
                             sms_this_month=sms_this_month,
                             datetime=datetime)
    except Exception as e:
        print(f"Reports error: {e}")
        flash('Error loading reports. Please try again.', 'error')
        return render_template('reports.html',
                             total_students=0,
                             total_teachers=0,
                             total_classes=0,
                             monthly_collection=0,
                             pending_fees=0,
                             today_attendance=0,
                             today_present=0,
                             total_sms_sent=0,
                             sms_this_month=0,
                             datetime=datetime)

@app.route('/analytics_data')
@login_required
def analytics_data():
    """Provide analytics data for dashboard charts"""
    try:
        # Weekly attendance data
        weekly_attendance = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date().isoformat()
            day_attendance = query_db('attendance', date=date) or []
            total_students = len(query_db('student', is_active=True))
            present = len([a for a in day_attendance if a.get('status') == 'Present'])
            percentage = round((present / total_students * 100), 1) if total_students > 0 else 0
            weekly_attendance.append(percentage)
        
        # Monthly fee collection
        monthly_fees = []
        for month in range(1, 13):
            month_collection = 0
            paid_fees = query_db('fee', is_paid=True) or []
            for fee in paid_fees:
                if fee.get('paid_date'):
                    try:
                        paid_date = datetime.fromisoformat(fee['paid_date'])
                        if paid_date.month == month:
                            month_collection += fee.get('amount', 0)
                    except:
                        pass
            monthly_fees.append(month_collection)
        
        # Class-wise performance
        classes = get_from_db('class') or []
        class_performance = []
        for class_item in classes:
            students = query_db('student', class_id=class_item.get('id'), is_active=True)
            attendance_records = []
            for student in students:
                student_attendance = query_db('attendance', student_id=student.get('id'))
                attendance_records.extend(student_attendance)
            
            if attendance_records:
                present_count = len([a for a in attendance_records if a.get('status') == 'Present'])
                avg_attendance = round((present_count / len(attendance_records) * 100), 1)
            else:
                avg_attendance = 0
                
            class_performance.append({
                'name': f"{class_item.get('name')}-{class_item.get('section')}",
                'attendance': avg_attendance,
                'students': len(students)
            })
        
        return jsonify({
            'weekly_attendance': weekly_attendance[::-1],  # Reverse for chronological order
            'monthly_fees': monthly_fees,
            'class_performance': class_performance
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/performance_insights')
@login_required
def performance_insights():
    """Generate performance insights and recommendations"""
    try:
        insights = []
        
        # Analyze attendance trends
        students = query_db('student', is_active=True) or []
        total_students = len(students)
        
        # Today's attendance
        today = datetime.now().date().isoformat()
        today_attendance = query_db('attendance', date=today) or []
        today_present = len([a for a in today_attendance if a.get('status') == 'Present'])
        today_percentage = round((today_present / total_students * 100), 1) if total_students > 0 else 0
        
        if today_percentage < 80:
            insights.append({
                'type': 'warning',
                'title': 'Low Attendance Alert',
                'message': f'Today\'s attendance is {today_percentage}% - below the recommended 80%',
                'recommendation': 'Send attendance reminders to parents',
                'action': 'send_attendance_reminders'
            })
        
        # Fee collection analysis
        unpaid_fees = query_db('fee', is_paid=False) or []
        total_unpaid = sum(fee.get('amount', 0) for fee in unpaid_fees)
        
        if total_unpaid > 50000:
            insights.append({
                'type': 'info',
                'title': 'Outstanding Fees',
                'message': f'৳{total_unpaid:,.0f} in pending fee collection',
                'recommendation': 'Send automated fee reminders to improve collection',
                'action': 'send_fee_reminders'
            })
        
        # Teacher performance
        teachers = query_db('teacher', is_active=True) or []
        teacher_attendance = query_db('teacher_attendance', date=today) or []
        teacher_present = len([a for a in teacher_attendance if a.get('status') == 'Present'])
        teacher_percentage = round((teacher_present / len(teachers) * 100), 1) if teachers else 0
        
        if teacher_percentage < 95:
            insights.append({
                'type': 'warning',
                'title': 'Teacher Attendance',
                'message': f'Teacher attendance is {teacher_percentage}%',
                'recommendation': 'Monitor teacher attendance patterns',
                'action': 'view_teacher_attendance'
            })
        
        # SMS usage analysis
        sms_logs = get_from_db('sms_log') or []
        recent_sms = [s for s in sms_logs if s.get('sent_at') and 
                     (datetime.now() - datetime.fromisoformat(s['sent_at'])).days <= 7]
        
        if len(recent_sms) > 100:
            insights.append({
                'type': 'success',
                'title': 'High SMS Usage',
                'message': f'{len(recent_sms)} SMS sent this week',
                'recommendation': 'Great communication with parents!',
                'action': 'view_sms_report'
            })
        
        return jsonify({
            'insights': insights,
            'summary': {
                'total_students': total_students,
                'today_attendance': today_percentage,
                'pending_fees': total_unpaid,
                'teacher_attendance': teacher_percentage
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/settings')
@login_required
def settings():
    # Get current SMS configuration
    sms_config = {
        'api_key': INFOBIP_API_KEY,
        'base_url': INFOBIP_BASE_URL,
        'sender': INFOBIP_SENDER,
        'status': 'Active' if INFOBIP_API_KEY else 'Not Configured'
    }

    # Get SMS statistics
    all_sms = get_from_db('sms_log') or []
    total_sms = len([s for s in all_sms if s.get('status') == 'sent'])

    # Current month SMS count
    current_month = datetime.now().month
    current_year = datetime.now().year
    month_sms = 0
    success_count = 0
    failed_count = 0

    for sms in all_sms:
        if sms.get('sent_at'):
            try:
                sent_date = datetime.fromisoformat(sms['sent_at'])
                if sent_date.month == current_month and sent_date.year == current_year:
                    month_sms += 1
                    if sms.get('status') == 'sent':
                        success_count += 1
                    else:
                        failed_count += 1
            except:
                pass

    success_rate = round((success_count / total_sms * 100), 1) if total_sms > 0 else 0

    sms_stats = {
        'total_sms': total_sms,
        'month_sms': month_sms,
        'success_rate': success_rate,
        'failed_count': failed_count
    }

    return render_template('settings.html', sms_config=sms_config, sms_stats=sms_stats)

@app.route('/test_sms', methods=['POST'])
@login_required
def test_sms():
    try:
        phone_number = request.json.get('phone_number')
        if not phone_number:
            return jsonify({'success': False, 'message': 'Phone number required'})

        test_message = f"Test SMS from School Management System. Time: {datetime.now().strftime('%H:%M:%S')}"

        if send_infobip_sms(phone_number, test_message):
            # Log test SMS
            sms_log = {
                'phone_number': phone_number,
                'message': test_message,
                'status': 'sent',
                'template_id': None,
                'sent_at': datetime.now(timezone.utc).isoformat(),
                'sent_by': current_user.id,
                'is_test': True
            }
            save_to_db('sms_log', sms_log)
            return jsonify({'success': True, 'message': 'Test SMS sent successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send test SMS'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/update_sms_config', methods=['POST'])
@login_required
def update_sms_config():
    try:
        # In a real application, you would update environment variables
        # For this demo, we'll just return success
        return jsonify({'success': True, 'message': 'SMS configuration updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating configuration: {str(e)}'})

@app.route('/validate_sms_config', methods=['POST'])
@login_required
def validate_sms_config():
    try:
        # Check if API credentials are valid by making a test request
        url = f"{INFOBIP_BASE_URL}/accounts/1/balance"
        headers = {
            'Authorization': f'App {INFOBIP_API_KEY}',
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'SMS configuration is valid!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid SMS configuration'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Validation error: {str(e)}'})

@app.route('/update_sms_templates', methods=['POST'])
@login_required
def update_sms_templates():
    try:
        fee_template = request.form.get('fee_template')
        exam_template = request.form.get('exam_template')

        # Update fee template
        fee_templates = query_db('sms_template', template_type='fee_due', is_active=True)
        if fee_templates:
            fee_templates[0]['message'] = fee_template
            update_in_db('sms_template', fee_templates[0]['id'], fee_templates[0])

        # Update exam template
        exam_templates = query_db('sms_template', template_type='exam_reminder', is_active=True)
        if exam_templates:
            exam_templates[0]['message'] = exam_template
            update_in_db('sms_template', exam_templates[0]['id'], exam_templates[0])

        flash('SMS templates updated successfully!', 'success')
        return redirect(url_for('settings'))

    except Exception as e:
        flash(f'Error updating templates: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/clear_all_data', methods=['POST'])
@login_required
def clear_all_data():
    try:
        # Delete all data from ReplDB (except admin)
        collections = ['student', 'teacher', 'class', 'attendance', 'fee', 'exam', 'result', 'sms_template', 'sms_log', 'notice']

        for collection in collections:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM app_data WHERE collection = ?", (collection,))
                conn.commit()
            clear_cache(collection)

        flash('All data has been cleared successfully!', 'success')
    except Exception as e:
        flash(f'Error clearing data: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/generate_report/<report_type>')
@login_required
def generate_report(report_type):
    if report_type == 'fees':
        return redirect(url_for('fee_report'))
    elif report_type == 'sms':
        return redirect(url_for('sms_report'))
    elif report_type == 'results':
        return redirect(url_for('results_report'))
    elif report_type == 'attendance':
        return redirect(url_for('attendance_report'))
    elif report_type == 'teacher_attendance':
        return redirect(url_for('teacher_attendance_report'))
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('reports'))

@app.route('/fee_report')
@login_required
def fee_report():
    try:
        fees = get_from_db('fee') or []
        students = query_db('student', is_active=True) or []

        # Calculate statistics
        total_fees = sum(fee.get('amount', 0) for fee in fees if fee)
        paid_fees = sum(fee.get('amount', 0) for fee in fees if fee and fee.get('is_paid', False))
        unpaid_fees = total_fees - paid_fees

        # Create student-wise fee summary
        student_fee_data = []
        for student in students:
            student_fees = [f for f in fees if f.get('student_id') == student.get('id')]

            student_total = sum(f.get('amount', 0) for f in student_fees)
            student_paid = sum(f.get('amount', 0) for f in student_fees if f.get('is_paid', False))
            student_pending = student_total - student_paid

            # Get class information
            class_data = get_from_db('class', student.get('class_id'))
            class_name = f"{class_data.get('name')} - {class_data.get('section')}" if class_data else "N/A"

            student_fee_data.append({
                'name': student.get('name', 'Unknown'),
                'roll_number': student.get('roll_number', 'N/A'),
                'class_name': class_name,
                'total_fees': student_total,
                'paid_fees': student_paid,
                'pending_fees': student_pending
            })

        return render_template('fee_report.html', 
                             fee_data=student_fee_data,
                             fees=fees, 
                             students=students,
                             total_fees=total_fees,
                             paid_fees=paid_fees,
                             unpaid_fees=unpaid_fees)
    except Exception as e:
        print(f"Fee report error: {e}")
        flash('Error loading fee report. Please try again.', 'error')
        return render_template('fee_report.html', 
                             fee_data=[],
                             fees=[], 
                             students=[],
                             total_fees=0,
                             paid_fees=0,
                             unpaid_fees=0)

@app.route('/sms_report')
@login_required
def sms_report():
    try:
        sms_logs = get_from_db('sms_log') or []
        templates = get_from_db('sms_template') or []

        # Calculate SMS statistics
        total_sms = len([s for s in sms_logs if s])
        sent_sms = len([s for s in sms_logs if s and s.get('status') == 'sent'])
        failed_sms = total_sms - sent_sms

        # Template usage statistics
        template_usage = {}
        template_sent = {}
        template_failed = {}

        for sms in sms_logs:
            if sms and sms.get('template_id'):
                template_id = sms['template_id']
                template_usage[template_id] = template_usage.get(template_id, 0) + 1

                if sms.get('status') == 'sent':
                    template_sent[template_id] = template_sent.get(template_id, 0) + 1
                else:
                    template_failed[template_id] = template_failed.get(template_id, 0) + 1

        # Create SMS data with template information
        sms_data = []
        for template in templates:
            if template:
                template_id = template.get('id')
                total_sent = template_usage.get(template_id, 0)
                successful = template_sent.get(template_id, 0)
                failed = template_failed.get(template_id, 0)

                sms_data.append({
                    'template_name': template.get('name', 'Unknown'),
                    'template_type': template.get('template_type', 'general'),
                    'total_sent': total_sent,
                    'successful': successful,
                    'failed': failed
                })

        return render_template('sms_report.html', 
                             sms_data=sms_data,
                             sms_logs=sms_logs, 
                             templates=templates,
                             total_sms=total_sms,
                             sent_sms=sent_sms,
                             failed_sms=failed_sms)
    except Exception as e:
        print(f"SMS report error: {e}")
        flash('Error loading SMS report. Please try again.', 'error')
        return render_template('sms_report.html', 
                             sms_data=[],
                             sms_logs=[], 
                             templates=[],
                             total_sms=0,
                             sent_sms=0,
                             failed_sms=0)

@app.route('/results_report')
@login_required
def results_report():
    try:
        results = get_from_db('result') or []
        exams = get_from_db('exam') or []
        students = query_db('student', is_active=True) or []

        # Calculate exam statistics
        total_exams = len([e for e in exams if e])
        total_results = len([r for r in results if r])

        # Create detailed results data for display
        results_data = []
        for result in results:
            if result:
                student = get_from_db('student', result.get('student_id'))
                exam = get_from_db('exam', result.get('exam_id'))

                if student and exam:
                    # Get class information
                    class_data = get_from_db('class', student.get('class_id'))
                    class_name = f"{class_data.get('name')} - {class_data.get('section')}" if class_data else "N/A"

                    # Calculate grade
                    marks_obtained = result.get('marks_obtained', 0)
                    total_marks = exam.get('total_marks', 100)
                    grade = calculate_grade(marks_obtained, total_marks)

                    results_data.append({
                        'name': student.get('name', 'Unknown'),
                        'roll_number': student.get('roll_number', 'N/A'),
                        'class_name': class_name,
                        'exam_name': exam.get('name', 'Unknown'),
                        'subject': exam.get('subject', 'Unknown'),
                        'marks_obtained': marks_obtained,
                        'total_marks': total_marks,
                        'grade': grade
                    })

        # Create exam performance data
        exam_performance = []
        for exam in exams:
            if exam:
                exam_results = [r for r in results if r and r.get('exam_id') == exam.get('id')]
                if exam_results:
                    total_marks_sum = sum(r.get('marks_obtained', 0) for r in exam_results)
                    avg_marks = total_marks_sum / len(exam_results) if exam_results else 0

                    class_data = get_from_db('class', exam.get('class_id'))
                    exam_performance.append({
                        'exam_name': exam.get('name', 'Unknown'),
                        'subject': exam.get('subject', 'Unknown'),
                        'class_name': f"{class_data.get('name')} - {class_data.get('section')}" if class_data else 'Unknown',
                        'total_students': len(exam_results),
                        'average_marks': round(avg_marks, 2),
                        'total_marks': exam.get('total_marks', 100)
                    })

        return render_template('results_report.html', 
                             results_data=results_data,
                             results=results, 
                             exams=exams,
                             students=students,
                             total_exams=total_exams,
                             total_results=total_results,
                             exam_performance=exam_performance)
    except Exception as e:
        print(f"Results report error: {e}")
        flash('Error loading results report. Please try again.', 'error')
        return render_template('results_report.html', 
                             results_data=[],
                             results=[], 
                             exams=[],
                             students=[],
                             total_exams=0,
                             total_results=0,
                             exam_performance=[])

@app.route('/teacher_attendance_report')
@login_required
def teacher_attendance_report():
    try:
        teacher_attendance = get_from_db('teacher_attendance') or []
        teachers = query_db('teacher', is_active=True) or []
        
        # Calculate teacher attendance statistics
        total_records = len([a for a in teacher_attendance if a])
        present_records = len([a for a in teacher_attendance if a and a.get('status') == 'Present'])
        absent_records = total_records - present_records
        
        # Monthly teacher attendance analysis
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Create teacher-wise attendance data
        teacher_attendance_data = []
        for teacher in teachers:
            teacher_att_records = [a for a in teacher_attendance if a.get('teacher_id') == teacher.get('id')]
            
            # Filter for current month
            monthly_attendance = []
            for record in teacher_att_records:
                if record and record.get('date'):
                    try:
                        record_date = datetime.fromisoformat(record['date'])
                        if record_date.month == current_month and record_date.year == current_year:
                            monthly_attendance.append(record)
                    except:
                        pass
            
            total_days = len(monthly_attendance)
            present_days = len([a for a in monthly_attendance if a.get('status') == 'Present'])
            late_days = len([a for a in monthly_attendance if a.get('status') == 'Late'])
            leave_days = len([a for a in monthly_attendance if a.get('status') == 'Leave'])
            
            if total_days > 0:  # Only include teachers with attendance records
                attendance_percentage = round((present_days / total_days * 100), 2) if total_days > 0 else 0
                teacher_attendance_data.append({
                    'name': teacher.get('name', 'Unknown'),
                    'employee_id': teacher.get('employee_id', 'N/A'),
                    'subject': teacher.get('subject', 'N/A'),
                    'total_days': total_days,
                    'present_days': present_days,
                    'late_days': late_days,
                    'leave_days': leave_days,
                    'absent_days': total_days - present_days - late_days - leave_days,
                    'attendance_percentage': attendance_percentage
                })
        
        # Daily attendance summary for current month
        daily_summary = {}
        for record in teacher_attendance:
            if record and record.get('date'):
                try:
                    record_date = datetime.fromisoformat(record['date'])
                    if record_date.month == current_month and record_date.year == current_year:
                        date_str = record['date']
                        if date_str not in daily_summary:
                            daily_summary[date_str] = {
                                'total': 0,
                                'present': 0,
                                'absent': 0,
                                'late': 0,
                                'leave': 0
                            }
                        
                        daily_summary[date_str]['total'] += 1
                        status = record.get('status', 'Absent')
                        if status == 'Present':
                            daily_summary[date_str]['present'] += 1
                        elif status == 'Late':
                            daily_summary[date_str]['late'] += 1
                        elif status == 'Leave':
                            daily_summary[date_str]['leave'] += 1
                        else:
                            daily_summary[date_str]['absent'] += 1
                except:
                    pass
        
        # Convert daily summary to list and sort by date
        daily_attendance_list = []
        for date_str, summary in daily_summary.items():
            summary['date'] = date_str
            summary['percentage'] = round((summary['present'] / summary['total'] * 100), 2) if summary['total'] > 0 else 0
            daily_attendance_list.append(summary)
        
        daily_attendance_list.sort(key=lambda x: x['date'], reverse=True)
        
        return render_template('teacher_attendance_report.html', 
                             teacher_attendance_data=teacher_attendance_data,
                             teacher_attendance=teacher_attendance, 
                             teachers=teachers,
                             total_records=total_records,
                             present_records=present_records,
                             absent_records=absent_records,
                             daily_attendance=daily_attendance_list[:15],  # Last 15 days
                             current_month=datetime.now().strftime('%B %Y'))
    except Exception as e:
        print(f"Teacher attendance report error: {e}")
        flash('Error loading teacher attendance report. Please try again.', 'error')
        return render_template('teacher_attendance_report.html', 
                             teacher_attendance_data=[],
                             teacher_attendance=[], 
                             teachers=[],
                             total_records=0,
                             present_records=0,
                             absent_records=0,
                             daily_attendance=[],
                             current_month=datetime.now().strftime('%B %Y'))

@app.route('/attendance_report')
@login_required
def attendance_report():
    try:
        # Get filter parameters
        class_filter = request.args.get('class_filter', '')
        month_filter = request.args.get('month_filter', datetime.now().strftime('%Y-%m'))
        min_attendance = request.args.get('min_attendance', '')

        attendance = get_from_db('attendance') or []
        classes = get_from_db('class') or []

        # Filter students by class if specified
        if class_filter:
            students = query_db('student', class_id=class_filter, is_active=True) or []
        else:
            students = query_db('student', is_active=True) or []

        # Parse month filter
        try:
            filter_year, filter_month = map(int, month_filter.split('-'))
        except:
            filter_year, filter_month = datetime.now().year, datetime.now().month

        # Filter attendance by selected month
        filtered_attendance = []
        for record in attendance:
            if record and record.get('date'):
                try:
                    record_date = datetime.fromisoformat(record['date'])
                    if record_date.month == filter_month and record_date.year == filter_year:
                        filtered_attendance.append(record)
                except:
                    pass

        # Calculate attendance statistics
        total_records = len([a for a in filtered_attendance if a])
        present_records = len([a for a in filtered_attendance if a and a.get('status') == 'Present'])
        absent_records = total_records - present_records

        # Create student-wise attendance data
        attendance_data = []
        for student in students:
            student_attendance = [a for a in filtered_attendance if a.get('student_id') == student.get('id')]

            total_days = len(student_attendance)
            present_days = len([a for a in student_attendance if a.get('status') == 'Present'])

            # Get class information
            class_data = get_from_db('class', student.get('class_id'))
            class_name = f"{class_data.get('name')} - {class_data.get('section')}" if class_data else "N/A"

            if total_days > 0:  # Only include students with attendance records
                attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
                
                # Apply minimum attendance filter
                if min_attendance:
                    min_percent = float(min_attendance)
                    if min_percent == 60:  # Below 60%
                        if attendance_percentage >= 60:
                            continue
                    else:  # Above specified percentage
                        if attendance_percentage < min_percent:
                            continue

                attendance_data.append({
                    'name': student.get('name', 'Unknown'),
                    'roll_number': student.get('roll_number', 'N/A'),
                    'class_name': class_name,
                    'class_id': student.get('class_id'),
                    'total_days': total_days,
                    'present_days': present_days,
                    'attendance_percentage': round(attendance_percentage, 2)
                })

        # Sort by class and then by attendance percentage
        attendance_data.sort(key=lambda x: (x['class_name'], -x['attendance_percentage']))

        # Class-wise attendance summary
        class_wise_attendance = {}
        for record in filtered_attendance:
            if record:
                student = get_from_db('student', record.get('student_id'))
                if student and (not class_filter or student.get('class_id') == class_filter):
                    class_id = student.get('class_id')
                    if class_id not in class_wise_attendance:
                        class_data = get_from_db('class', class_id)
                        class_name = f"{class_data.get('name')} - {class_data.get('section')}" if class_data else 'Unknown'
                        class_wise_attendance[class_id] = {
                            'class_name': class_name,
                            'total': 0,
                            'present': 0
                        }

                    class_wise_attendance[class_id]['total'] += 1
                    if record.get('status') == 'Present':
                        class_wise_attendance[class_id]['present'] += 1

        # Calculate percentages for class-wise attendance
        for class_id in class_wise_attendance:
            total = class_wise_attendance[class_id]['total']
            present = class_wise_attendance[class_id]['present']
            class_wise_attendance[class_id]['percentage'] = round((present / total * 100), 2) if total > 0 else 0

        return render_template('attendance_report.html', 
                             attendance_data=attendance_data,
                             attendance=filtered_attendance, 
                             students=students,
                             classes=classes,
                             total_records=total_records,
                             present_records=present_records,
                             absent_records=absent_records,
                             monthly_attendance=len(filtered_attendance),
                             class_wise_attendance=list(class_wise_attendance.values()),
                             datetime=datetime,
                             selected_month=month_filter,
                             selected_class=class_filter,
                             selected_min_attendance=min_attendance)
    except Exception as e:
        print(f"Attendance report error: {e}")
        flash('Error loading attendance report. Please try again.', 'error')
        return render_template('attendance_report.html', 
                             attendance_data=[],
                             attendance=[], 
                             students=[],
                             classes=[],
                             total_records=0,
                             present_records=0,
                             absent_records=0,
                             monthly_attendance=0,
                             class_wise_attendance=[],
                             datetime=datetime,
                             selected_month=datetime.now().strftime('%Y-%m'),
                             selected_class='',
                             selected_min_attendance='')

@app.route('/send_fee_reminder/<fee_id>')
@login_required
def send_fee_reminder(fee_id):
    fee = get_from_db('fee', fee_id)
    if not fee:
        flash('Fee record not found', 'error')
        return redirect(url_for('fees'))

    student = get_from_db('student', fee.get('student_id'))
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('fees'))

    # Get fee reminder template
    templates = query_db('sms_template', template_type='fee_due', is_active=True)
    if not templates:
        flash('No fee reminder template found', 'error')
        return redirect(url_for('fees'))

    template = templates[0]
    message = template.get('message', '')

    # Replace placeholders
    message = message.replace('{student_name}', student.get('name', ''))
    message = message.replace('{guardian_name}', student.get('guardian_name', ''))
    message = message.replace('{due_amount}', str(fee.get('amount', 0)))
    message = message.replace('{due_date}', fee.get('due_date', ''))

    # Send SMS
    if send_infobip_sms(student.get('guardian_phone', ''), message):
        # Log SMS
        sms_log = {
            'phone_number': student.get('guardian_phone', ''),
            'message': message,
            'status': 'sent',
            'template_id': template.get('id'),
            'sent_at': datetime.now(timezone.utc).isoformat(),
            'sent_by': current_user.id
        }
        save_to_db('sms_log', sms_log)
        flash('Fee reminder sent successfully!', 'success')
    else:
        flash('Failed to send fee reminder', 'error')

    return redirect(url_for('fees'))

@app.route('/generate_smart_message', methods=['POST'])
@login_required
def generate_smart_message():
    """Generate smart, personalized messages"""
    try:
        data = request.json
        message_type = data.get('type')
        student_id = data.get('student_id')
        
        student = get_from_db('student', student_id) if student_id else None
        
        smart_messages = {
            'fee_reminder': [
                "প্রিয় {guardian_name}, {student_name} এর {fee_type} ফি ৳{amount} বকেয়া রয়েছে। শেষ তারিখ: {due_date}। অনুগ্রহ করে শীঘ্রই পরিশোধ করুন।",
                "সম্মানিত অভিভাবক, আপনার সন্তান {student_name} এর ৳{amount} টাকা ফি পরিশোধের জন্য অনুরোধ করা হচ্ছে।",
                "বিজ্ঞপ্তি: {student_name} এর {fee_type} বাবদ ৳{amount} পরিশোধ করুন। যোগাযোগ: স্কুল অফিস।"
            ],
            'attendance_low': [
                "প্রিয় {guardian_name}, {student_name} এর উপস্থিতি কম ({attendance}%)। নিয়মিত স্কুলে পাঠান।",
                "মনোযোগ দিন: {student_name} এর উপস্থিতির হার উদ্বেগজনক। স্কুলে যোগাযোগ করুন।"
            ],
            'exam_reminder': [
                "{student_name} এর {exam_name} পরীক্ষা {exam_date} তারিখে। প্রস্তুতি নিশ্চিত করুন।",
                "আসন্ন পরীক্ষার জন্য {student_name} কে প্রস্তুত রাখুন। তারিখ: {exam_date}।"
            ],
            'result_published': [
                "শুভ সংবাদ! {student_name} এর {exam_name} ফলাফল প্রকাশিত। প্রাপ্ত নম্বর: {marks}/{total_marks}।",
                "{student_name} এর পরীক্ষার ফল দেখুন। গ্রেড: {grade}। অভিনন্দন!"
            ]
        }
        
        import random
        messages = smart_messages.get(message_type, ["সাধারণ বার্তা"])
        selected_message = random.choice(messages)
        
        return jsonify({
            'success': True,
            'message': selected_message,
            'variations': messages
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/smart_bulk_notifications', methods=['POST'])
@login_required
def smart_bulk_notifications():
    """Send smart bulk notifications based on system analysis"""
    try:
        notification_type = request.json.get('type')
        
        if notification_type == 'low_attendance':
            # Find students with low attendance
            attendance_records = get_from_db('attendance') or []
            student_attendance = {}
            
            for record in attendance_records:
                if record:
                    student_id = record.get('student_id')
                    if student_id not in student_attendance:
                        student_attendance[student_id] = {'total': 0, 'present': 0}
                    
                    student_attendance[student_id]['total'] += 1
                    if record.get('status') == 'Present':
                        student_attendance[student_id]['present'] += 1
            
            # Find students with <75% attendance
            low_attendance_students = []
            for student_id, attendance in student_attendance.items():
                if attendance['total'] > 0:
                    percentage = (attendance['present'] / attendance['total']) * 100
                    if percentage < 75:
                        student = get_from_db('student', student_id)
                        if student:
                            low_attendance_students.append({
                                'student': student,
                                'attendance': round(percentage, 1)
                            })
            
            # Send notifications
            sent_count = 0
            for item in low_attendance_students:
                student = item['student']
                message = f"প্রিয় {student.get('guardian_name', 'অভিভাবক')}, {student.get('name')} এর উপস্থিতি কম ({item['attendance']}%)। নিয়মিত স্কুলে পাঠান।"
                
                if send_infobip_sms(student.get('guardian_phone'), message):
                    sent_count += 1
            
            return jsonify({
                'success': True,
                'message': f'{sent_count} attendance notifications sent',
                'count': sent_count
            })
            
        elif notification_type == 'fee_reminders':
            return send_bulk_fee_reminders()
            
        else:
            return jsonify({'success': False, 'message': 'Invalid notification type'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_whatsapp_reminder/<fee_id>')
@login_required
def send_whatsapp_reminder(fee_id):
    """Send WhatsApp fee reminder"""
    try:
        fee = get_from_db('fee', fee_id)
        if not fee:
            flash('Fee record not found', 'error')
            return redirect(url_for('fees'))

        student = get_from_db('student', fee.get('student_id'))
        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('fees'))

        if not student.get('guardian_phone'):
            flash('Guardian phone number not found', 'error')
            return redirect(url_for('fees'))

        # Create WhatsApp message
        message = f"""🏫 *School Fee Reminder*

প্রিয় {student.get('guardian_name', 'অভিভাবক')},

আপনার সন্তান *{student.get('name')}* এর ফি বকেয়া রয়েছে:

💰 *পরিমাণ:* ৳{fee.get('amount', 0)}
📅 *শেষ তারিখ:* {fee.get('due_date', '')}
📝 *ফি ধরণ:* {fee.get('fee_type', 'বেতন')}

অনুগ্রহ করে শীঘ্রই পরিশোধ করুন।

ধন্যবাদ,
স্কুল ম্যানেজমেন্ট"""

        # Send WhatsApp message
        if send_whatsapp_instant(student.get('guardian_phone'), message):
            # Log message
            sms_log = {
                'phone_number': student.get('guardian_phone'),
                'message': message,
                'status': 'sent',
                'template_id': None,
                'sent_at': datetime.now(timezone.utc).isoformat(),
                'sent_by': current_user.id,
                'message_type': 'whatsapp_fee_reminder'
            }
            save_to_db('sms_log', sms_log)
            flash('WhatsApp fee reminder sent successfully!', 'success')
        else:
            flash('Failed to send WhatsApp reminder', 'error')

        return redirect(url_for('fees'))

    except Exception as e:
        print(f"WhatsApp reminder error: {e}")
        flash('Error sending WhatsApp reminder', 'error')
        return redirect(url_for('fees'))

@app.route('/send_whatsapp_attendance_alert', methods=['POST'])
@login_required
def send_whatsapp_attendance_alert():
    """Send WhatsApp attendance alerts to parents of absent students"""
    try:
        date = request.form.get('date')
        if not date:
            return jsonify({'success': False, 'message': 'Date required'})

        # Get absent students for the date
        attendance_records = query_db('attendance', date=date)
        absent_students = []

        for record in attendance_records:
            if record and record.get('status') == 'Absent':
                student = get_from_db('student', record.get('student_id'))
                if student and student.get('guardian_phone'):
                    absent_students.append(student)

        sent_count = 0
        for student in absent_students:
            message = f"""🏫 *Attendance Alert*

প্রিয় {student.get('guardian_name', 'অভিভাবক')},

আজ ({date}) আপনার সন্তান *{student.get('name')}* স্কুলে অনুপস্থিত ছিল।

🎓 *শ্রেণি:* {student.get('class_name', 'N/A')}
📞 *রোল নং:* {student.get('roll_number', '')}

অনুগ্রহ করে প্রয়োজনে স্কুলে যোগাযোগ করুন।

ধন্যবাদ,
স্কুল ম্যানেজমেন্ট"""

            if send_whatsapp_instant(student.get('guardian_phone'), message):
                # Log message
                sms_log = {
                    'phone_number': student.get('guardian_phone'),
                    'message': message,
                    'status': 'sent',
                    'template_id': None,
                    'sent_at': datetime.now(timezone.utc).isoformat(),
                    'sent_by': current_user.id,
                    'message_type': 'whatsapp_attendance_alert'
                }
                save_to_db('sms_log', sms_log)
                sent_count += 1

        return jsonify({
            'success': True,
            'message': f'WhatsApp alerts sent to {sent_count} parents',
            'count': sent_count
        })

    except Exception as e:
        print(f"WhatsApp attendance alert error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/send_bulk_fee_reminders', methods=['POST'])
@login_required
def send_bulk_fee_reminders():
    try:
        # Get all unpaid fees
        unpaid_fees = query_db('fee', is_paid=False)

        # Get fee reminder template
        templates = query_db('sms_template', template_type='fee_due', is_active=True)
        if not templates:
            return jsonify({'success': False, 'message': 'No fee reminder template found'})

        template = templates[0]
        sent_count = 0

        for fee in unpaid_fees:
            student = get_from_db('student', fee.get('student_id'))
            if not student or not student.get('guardian_phone'):
                continue

            message = template.get('message', '')
            message = message.replace('{student_name}', student.get('name', ''))
            message = message.replace('{guardian_name}', student.get('guardian_name', ''))
            message = message.replace('{due_amount}', str(fee.get('amount', 0)))
            message = message.replace('{due_date}', fee.get('due_date', ''))

            if send_infobip_sms(student.get('guardian_phone'), message):
                # Log SMS
                sms_log = {
                    'phone_number': student.get('guardian_phone'),
                    'message': message,
                    'status': 'sent',
                    'template_id': template.get('id'),
                    'sent_at': datetime.now(timezone.utc).isoformat(),
                    'sent_by': current_user.id
                }
                save_to_db('sms_log', sms_log)
                sent_count += 1

        return jsonify({'success': True, 'message': f'Sent {sent_count} fee reminders'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_fee/<fee_id>', methods=['POST'])
@login_required
def delete_fee(fee_id):
    try:
        if delete_from_db('fee', fee_id):
            return jsonify({'success': True, 'message': 'Fee deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Fee not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/export_data/<data_type>/<format>')
@login_required
def export_data(data_type, format):
    try:
        if data_type == 'students':
            students = query_db('student', is_active=True)
            if format == 'pdf':
                return generate_students_pdf(students)
            elif format == 'csv':
                return generate_students_csv(students)
        elif data_type == 'attendance':
            date = request.args.get('date', datetime.now().date().isoformat())
            attendance = query_db('attendance', date=date)
            return generate_attendance_csv(attendance, date)
        else:
            flash('Invalid export type', 'error')
            return redirect(url_for('reports'))
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('reports'))

def generate_students_pdf(students):
    """Generate PDF export for students"""
    try:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Student List Report")

        # Table headers
        y = height - 100
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Roll No.")
        p.drawString(120, y, "Name")
        p.drawString(250, y, "Class")
        p.drawString(350, y, "Phone")
        p.drawString(450, y, "Guardian")

        # Student data
        y -= 20
        p.setFont("Helvetica", 9)
        for student in students:
            if y < 50:  # New page if needed
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 9)

            class_data = get_from_db('class', student.get('class_id'))
            class_name = f"{class_data.get('name', '')}-{class_data.get('section', '')}" if class_data else "N/A"

            p.drawString(50, y, str(student.get('roll_number', '')))
            p.drawString(120, y, str(student.get('name', ''))[:15])
            p.drawString(250, y, class_name)
            p.drawString(350, y, str(student.get('phone', '')))
            p.drawString(450, y, str(student.get('guardian_name', ''))[:15])
            y -= 15

        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='students.pdf', mimetype='application/pdf')
    except Exception as e:
        flash(f'PDF generation error: {str(e)}', 'error')
        return redirect(url_for('reports'))

def generate_students_csv(students):
    """Generate CSV export for students"""
    try:
        output = io.StringIO()
        output.write("Roll Number,Name,Class,Phone,Email,Guardian Name,Guardian Phone\n")

        for student in students:
            class_data = get_from_db('class', student.get('class_id'))
            class_name = f"{class_data.get('name', '')}-{class_data.get('section', '')}" if class_data else "N/A"

            output.write(f"{student.get('roll_number', '')},{student.get('name', '')},{class_name},{student.get('phone', '')},{student.get('email', '')},{student.get('guardian_name', '')},{student.get('guardian_phone', '')}\n")

        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), as_attachment=True, download_name='students.csv', mimetype='text/csv')
    except Exception as e:
        flash(f'CSV generation error: {str(e)}', 'error')
        return redirect(url_for('reports'))

def generate_attendance_csv(attendance, date):
    """Generate CSV export for attendance"""
    try:
        output = io.StringIO()
        output.write(f"Attendance Report - {date}\n")
        output.write("Student Name,Roll Number,Class,Status\n")

        for record in attendance:
            student = get_from_db('student', record.get('student_id'))
            if student:
                class_data = get_from_db('class', student.get('class_id'))
                class_name = f"{class_data.get('name', '')}-{class_data.get('section', '')}" if class_data else "N/A"

                output.write(f"{student.get('name', '')},{student.get('roll_number', '')},{class_name},{record.get('status', '')}\n")

        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), as_attachment=True, download_name=f'attendance_{date}.csv', mimetype='text/csv')
    except Exception as e:
        flash(f'Attendance CSV generation error: {str(e)}', 'error')
        return redirect(url_for('reports'))

# WhatsApp Functions
def send_whatsapp_message(phone_number, message, hour=None, minute=None):
    """Send WhatsApp message using pywhatkit"""
    try:
        # Check if pywhatkit is available
        try:
            import pywhatkit as kit
        except ImportError:
            print("⚠️ pywhatkit not installed. Install with: pip install pywhatkit")
            return False
            
        # Format phone number for international use
        if phone_number.startswith('01'):
            phone_number = '+88' + phone_number
        elif phone_number.startswith('88'):
            phone_number = '+' + phone_number
        elif not phone_number.startswith('+'):
            phone_number = '+88' + phone_number

        # If time not specified, send in next 2 minutes
        if hour is None or minute is None:
            now = datetime.now()
            send_time = now + timedelta(minutes=2)
            hour = send_time.hour
            minute = send_time.minute

        # Send message
        kit.sendwhatmsg(phone_number, message, hour, minute, wait_time=15, tab_close=True)
        print(f"✅ WhatsApp message scheduled to {phone_number} at {hour:02d}:{minute:02d}")
        return True

    except Exception as e:
        print(f"❌ WhatsApp message error: {e}")
        return False

def send_whatsapp_instant(phone_number, message):
    """Send instant WhatsApp message"""
    try:
        # Check if pywhatkit is available
        try:
            import pywhatkit as kit
        except ImportError:
            print("⚠️ pywhatkit not installed. Install with: pip install pywhatkit")
            return False
            
        # Format phone number
        if phone_number.startswith('01'):
            phone_number = '+88' + phone_number
        elif phone_number.startswith('88'):
            phone_number = '+' + phone_number
        elif not phone_number.startswith('+'):
            phone_number = '+88' + phone_number

        kit.sendwhatmsg_instantly(phone_number, message, wait_time=15, tab_close=True)
        print(f"✅ Instant WhatsApp message sent to {phone_number}")
        return True

    except Exception as e:
        print(f"❌ Instant WhatsApp error: {e}")
        return False

# SMS Functions
def send_infobip_sms(phone_number, message):
    """Send SMS using Infobip API"""
    try:
        # Format phone number for international use
        if phone_number.startswith('01'):
            phone_number = '+88' + phone_number
        elif phone_number.startswith('88'):
            phone_number = '+' + phone_number
        elif not phone_number.startswith('+'):
            phone_number = '+88' + phone_number

        url = f"{INFOBIP_BASE_URL}/sms/2/text/advanced"

        headers = {
            'Authorization': f'App {INFOBIP_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        payload = {
            "messages": [
                {
                    "from": INFOBIP_SENDER,
                    "destinations": [
                        {
                            "to": phone_number
                        }
                    ],
                    "text": message
                }
            ]
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Infobip SMS sent to {phone_number}")
            print(f"Message ID: {result.get('messages', [{}])[0].get('messageId', 'N/A')}")
            return True
        else:
            print(f"❌ Infobip SMS failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Infobip SMS error: {e}")
        return False

@app.route('/view_sms_template/<id>')
@login_required
def view_sms_template(id):
    template = get_from_db('sms_template', id)
    if not template:
        flash('Template not found', 'error')
        return redirect(url_for('sms_management'))
    return render_template('view_sms_template.html', template=template)

@app.route('/edit_sms_template/<id>', methods=['GET', 'POST'])
@login_required
def edit_sms_template(id):
    template = get_from_db('sms_template', id)
    if not template:
        flash('Template not found', 'error')
        return redirect(url_for('sms_management'))

    form = SMSTemplateForm()

    if form.validate_on_submit():
        template_data = {
            'name': form.name.data,
            'template_type': form.template_type.data,
            'message': form.message.data,
            'placeholders': template.get('placeholders'),
            'is_active': True,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        update_in_db('sms_template', id, template_data)
        flash('Template updated successfully!', 'success')
        return redirect(url_for('sms_management'))

    # Pre-populate form
    form.name.data = template.get('name')
    form.template_type.data = template.get('template_type')
    form.message.data = template.get('message')

    return render_template('edit_sms_template.html', form=form, template=template)

@app.route('/delete_sms_template/<template_id>', methods=['POST'])
@login_required
def delete_sms_template(template_id):
    try:
        template = get_from_db('sms_template', template_id)
        if template:
            template['is_active'] = False
            update_in_db('sms_template', template_id, template)
            flash('Template deleted successfully!', 'success')
        else:
            flash('Template not found', 'error')
    except Exception as e:
        flash('Error deleting template', 'error')
    return redirect(url_for('sms_management'))

@app.route('/send_sms_page/<template_id>')
@login_required
def send_sms_page(template_id):
    template = get_from_db('sms_template', template_id)
    if not template:
        flash('Template not found', 'error')
        return redirect(url_for('sms_management'))

    students = query_db('student', is_active=True)
    classes = get_from_db('class')

    return render_template('send_sms.html', template=template, students=students, classes=classes)

@app.route('/send_sms', methods=['POST'])
@login_required
def send_sms():
    try:
        template_id = request.form.get('template_id')
        recipient_type = request.form.get('recipient_type')  # 'all', 'class', 'individual'
        message = request.form.get('message')

        template = get_from_db('sms_template', template_id) if template_id else None
        recipients = []

        if recipient_type == 'all':
            students = query_db('student', is_active=True)
            recipients = [(s.get('guardian_phone'), s.get('guardian_name'), s.get('name')) for s in students if s.get('guardian_phone')]
        elif recipient_type == 'class':
            class_id = request.form.get('class_id')
            students = query_db('student', class_id=class_id, is_active=True)
            recipients = [(s.get('guardian_phone'), s.get('guardian_name'), s.get('name')) for s in students if s.get('guardian_phone')]
        elif recipient_type == 'individual':
            student_ids = request.form.getlist('student_ids')
            for student_id in student_ids:
                student = get_from_db('student', student_id)
                if student and student.get('guardian_phone'):
                    recipients.append((student.get('guardian_phone'), student.get('guardian_name'), student.get('name')))

        sent_count = 0
        for phone, guardian_name, student_name in recipients:
            # Replace placeholders in message
            personalized_message = message.replace('{guardian_name}', guardian_name or 'Guardian')
            personalized_message = personalized_message.replace('{student_name}', student_name or 'Student')

            if send_infobip_sms(phone, personalized_message):
                # Log SMS
                sms_log = {
                    'phone_number': phone,
                    'message': personalized_message,
                    'status': 'sent',
                    'template_id': template_id,
                    'sent_at': datetime.now(timezone.utc).isoformat(),
                    'sent_by': current_user.id
                }
                save_to_db('sms_log', sms_log)
                sent_count += 1

        flash(f'SMS sent successfully to {sent_count} recipients!', 'success')
        return redirect(url_for('sms_management'))

    except Exception as e:
        flash(f'Error sending SMS: {str(e)}', 'error')
        return redirect(url_for('sms_management'))

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = get_from_db('student', student_id)
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('students'))

    form = StudentForm()
    classes = get_from_db('class') or []
    form.class_id.choices = [('', 'Select a Class')] + [(c.get('id'), f"{c.get('name')} - {c.get('section')}") for c in classes if c]

    if request.method == 'POST':
        if form.validate_on_submit():
            # Check if class_id is valid
            if not form.class_id.data:
                flash('Please select a valid class', 'error')
                return render_template('edit_student.html', form=form, student=student)

            # Check if roll number already exists (exclude current student)
            existing_students = query_db('student', roll_number=form.roll_number.data)
            roll_exists = any(s.get('id') != student_id for s in existing_students if s)
            if roll_exists:
                flash('Roll number already exists. Please use a different roll number.', 'error')
                return render_template('edit_student.html', form=form, student=student)

            try:
                student_data = {
                    'name': form.name.data,
                    'roll_number': form.roll_number.data,
                    'class_id': form.class_id.data,
                    'phone': form.phone.data,
                    'email': form.email.data or '',
                    'guardian_phone': form.guardian_phone.data,
                    'guardian_name': form.guardian_name.data,
                    'date_of_birth': form.date_of_birth.data.isoformat() if form.date_of_birth.data else '',
                    'address': form.address.data or '',
                    'is_active': student.get('is_active', True),
                    'created_at': student.get('created_at'),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                if update_in_db('student', student_id, student_data):
                    flash('Student updated successfully!', 'success')
                    return redirect(url_for('view_student', student_id=student_id))
                else:
                    flash('Error updating student in database', 'error')
            except Exception as e:
                print(f"Error updating student: {e}")
                flash(f'Error updating student: {str(e)}', 'error')
        else:
            # Show form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')

    # Pre-populate form for GET requests or failed POST
    if request.method == 'GET':
        form.name.data = student.get('name', '')
        form.roll_number.data = student.get('roll_number', '')
        form.class_id.data = student.get('class_id', '')
        form.phone.data = student.get('phone', '')
        form.email.data = student.get('email', '')
        form.guardian_phone.data = student.get('guardian_phone', '')
        form.guardian_name.data = student.get('guardian_name', '')
        form.address.data = student.get('address', '')
        
        # Handle date of birth
        if student.get('date_of_birth'):
            try:
                if isinstance(student['date_of_birth'], str):
                    form.date_of_birth.data = datetime.fromisoformat(student['date_of_birth']).date()
                else:
                    form.date_of_birth.data = student['date_of_birth']
            except Exception as e:
                print(f"Date parsing error: {e}")
                form.date_of_birth.data = None

    return render_template('edit_student.html', form=form, student=student)

@app.route('/view_student/<student_id>')
@login_required
def view_student(student_id):
    student = get_from_db('student', student_id)
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('students'))

    # Add class information
    class_data = get_from_db('class', student.get('class_id'))
    if class_data:
        student['class_name'] = f"{class_data.get('name')} - {class_data.get('section')}"

    # Get student's fees
    fees = query_db('fee', student_id=student_id)

    # Get student's attendance (last 10 days)
    attendance = query_db('attendance', student_id=student_id)
    recent_attendance = sorted(attendance, key=lambda x: x.get('date', ''), reverse=True)[:10]

    return render_template('view_student.html', student=student, fees=fees, attendance=recent_attendance)

def calculate_grade(marks, total_marks):
    percentage = (marks / total_marks) * 100
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'A-'
    elif percentage >= 60:
        return 'B+'
    elif percentage >= 50:
        return 'B'
    elif percentage >= 40:
        return 'C'
    elif percentage >= 33:
        return 'D'
    else:
        return 'F'

def can_delete_class(class_id):
    """Check if a class can be safely deleted and return detailed info"""
    try:
        # Get class data
        class_data = get_from_db('class', class_id)
        if not class_data:
            return False, "Class not found"

        # Check students
        students = query_db('student', class_id=class_id)
        if students:
            active_students = [s for s in students if s.get('is_active', True)]
            if active_students:
                return False, f"Class has {len(active_students)} active student(s). Transfer them first."
            else:
                return False, f"Class has {len(students)} inactive student(s) in records."

        # Check attendance records
        attendance_records = query_db('attendance')
        class_attendance = []
        for record in attendance_records:
            if record:
                student = get_from_db('student', record.get('student_id'))
                if student and student.get('class_id') == class_id:
                    class_attendance.append(record)
        
        if class_attendance:
            return False, f"Class has {len(class_attendance)} attendance records."

        # Check exam records
        exams = query_db('exam', class_id=class_id)
        if exams:
            return False, f"Class has {len(exams)} exam record(s)."

        # Check fee records through students
        for student in students:
            fee_records = query_db('fee', student_id=student.get('id'))
            if fee_records:
                return False, f"Students have {len(fee_records)} fee record(s)."

        return True, "Class can be deleted safely"

    except Exception as e:
        return False, f"Error checking class: {str(e)}"

# Initialize database and create admin user if it hasn't been initialized yet
def init_app():
    print("[INIT_APP] Starting init_app() function")
    
    # ALWAYS check for legacy admin migration (regardless of initialization flag)
    admins = get_from_db('admin')
    print(f"[INIT_APP] Admins found: {len(admins) if isinstance(admins, list) else 0}")
    
    if isinstance(admins, list) and len(admins) > 0:
        legacy_admin = admins[0]
        print(f"[INIT_APP] First admin username: '{legacy_admin.get('username')}'")
        
        # Migrate legacy admin with username '7' to 'admin'
        if legacy_admin.get('username') == '7':
            print(f"[INIT_APP] MIGRATING legacy admin from '7' to 'admin'")
            legacy_admin['username'] = 'admin'
            legacy_admin['password_hash'] = generate_password_hash('password123')
            update_in_db('admin', legacy_admin['id'], legacy_admin)
            print(f"[INIT_APP] [OK] Successfully migrated admin to username: admin")
            # Clear cache to ensure new username is used
            clear_cache()
    
    # Check if already initialized (original logic)
    with get_db_connection() as conn:
        row = conn.execute("SELECT id FROM app_data WHERE collection = 'metadata' AND id = 'initialized'").fetchone()
    
    if not row:
        print("[INIT_APP] First time initialization - creating default data")
        # Create default admin if not exists
        admins = get_from_db('admin')
        if not admins:
            admin = Admin()
            admin.username = 'admin'
            admin.email = 'admin@school.com'
            admin.password_hash = generate_password_hash('password123')
            admin.save()
            print(f"[INIT_APP] Created new admin with username: admin")

            # Create default teachers
            default_teachers = [
                {
                    'name': 'নুরুল আমিন',
                    'employee_id': 'T001',
                    'phone': '01711000001',
                    'email': 'nurul@school.com',
                    'subject': 'বাংলা',
                    'salary': 25000.00,
                    'joining_date': '2023-01-01',
                    'is_active': True,
                    'created_at': datetime.now(timezone.utc).isoformat()
                },
                {
                    'name': 'রহিমা খাতুন',
                    'employee_id': 'T002',
                    'phone': '01711000002',
                    'email': 'rahima@school.com',
                    'subject': 'ইংরেজি',
                    'salary': 24000.00,
                    'joining_date': '2023-01-15',
                    'is_active': True,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            ]

            teacher1_id = save_to_db('teacher', default_teachers[0])
            teacher2_id = save_to_db('teacher', default_teachers[1])

            # Create default classes
            default_classes = [
                {'name': 'Class 1', 'section': 'A', 'teacher_id': teacher1_id, 'capacity': 40},
                {'name': 'Class 1', 'section': 'B', 'teacher_id': teacher2_id, 'capacity': 40},
                {'name': 'Class 2', 'section': 'A', 'teacher_id': None, 'capacity': 35},
            ]

            for class_data in default_classes:
                save_to_db('class', class_data)

            # Create default SMS templates
            templates = [
                {
                    'name': 'Fee Due Reminder',
                    'template_type': 'fee_due',
                    'message': 'Dear {guardian_name}, Fee due for {student_name}. Amount: {due_amount}. Due date: {due_date}. Please pay soon.',
                    'placeholders': json.dumps(['student_name', 'guardian_name', 'due_amount', 'due_date']),
                    'is_active': True,
                    'created_at': datetime.now(timezone.utc).isoformat()
                },
                {
                    'name': 'Exam Reminder',
                    'template_type': 'exam_reminder',
                    'message':'Dear {guardian_name}, Exam reminder for {student_name}. Exam: {exam_name} on {exam_date}. Best wishes!',
                    'placeholders': json.dumps(['student_name', 'guardian_name', 'exam_name', 'exam_date']),
                    'is_active': True,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            ]

            for template_data in templates:
                save_to_db('sms_template', template_data)

            # Mark initialization as complete
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO app_data (collection, id, data) VALUES (?, ?, ?)",
                    ('metadata', 'initialized', json.dumps(True))
                )
                conn.commit()

@app.route('/smart_search')
@login_required
def smart_search():
    """Smart search across all entities"""
    try:
        query = request.args.get('q', '').lower()
        results = []
        
        if len(query) < 2:
            return jsonify(results)
        
        # Search students
        students = query_db('student', is_active=True) or []
        for student in students:
            if (query in student.get('name', '').lower() or 
                query in student.get('roll_number', '').lower()):
                
                class_data = get_from_db('class', student.get('class_id'))
                class_name = f"{class_data.get('name')}-{class_data.get('section')}" if class_data else "N/A"
                
                results.append({
                    'type': 'student',
                    'id': student.get('id'),
                    'title': student.get('name'),
                    'subtitle': f"Roll: {student.get('roll_number')} | Class: {class_name}",
                    'icon': 'fas fa-user-graduate',
                    'url': f"/view_student/{student.get('id')}"
                })
        
        # Search teachers
        teachers = query_db('teacher', is_active=True) or []
        for teacher in teachers:
            if (query in teacher.get('name', '').lower() or 
                query in teacher.get('employee_id', '').lower()):
                
                results.append({
                    'type': 'teacher',
                    'id': teacher.get('id'),
                    'title': teacher.get('name'),
                    'subtitle': f"ID: {teacher.get('employee_id')} | Subject: {teacher.get('subject', 'N/A')}",
                    'icon': 'fas fa-chalkboard-teacher',
                    'url': f"/teachers"
                })
        
        # Search classes
        classes = get_from_db('class') or []
        for class_item in classes:
            class_name = f"{class_item.get('name')} {class_item.get('section')}"
            if query in class_name.lower():
                results.append({
                    'type': 'class',
                    'id': class_item.get('id'),
                    'title': class_name,
                    'subtitle': f"Capacity: {class_item.get('capacity', 0)}",
                    'icon': 'fas fa-users',
                    'url': f"/classes"
                })
        
        # Add quick actions if no specific results
        if len(results) == 0:
            quick_actions = [
                {'title': 'Add New Student', 'subtitle': 'Register a new student', 'icon': 'fas fa-user-plus', 'url': '/add_student'},
                {'title': 'Mark Attendance', 'subtitle': 'Record student attendance', 'icon': 'fas fa-calendar-check', 'url': '/attendance'},
                {'title': 'Send SMS', 'subtitle': 'Send notifications', 'icon': 'fas fa-sms', 'url': '/sms_management'},
                {'title': 'View Reports', 'subtitle': 'Generate reports', 'icon': 'fas fa-chart-bar', 'url': '/reports'}
            ]
            results.extend(quick_actions)
        
        return jsonify(results[:10])  # Limit to 10 results
        
    except Exception as e:
        return jsonify([])

@app.route('/get_notifications')
@login_required
def get_notifications():
    """Get system notifications"""
    try:
        notifications = []
        
        # Check for pending fees
        unpaid_fees = query_db('fee', is_paid=False) or []
        if len(unpaid_fees) > 10:
            notifications.append({
                'id': 'pending_fees',
                'type': 'warning',
                'title': 'Pending Fees',
                'message': f'{len(unpaid_fees)} fees pending collection',
                'time': 'now',
                'action': '/fees',
                'icon': 'fas fa-money-bill-wave'
            })
        
        # Check for low attendance
        today = datetime.now().date().isoformat()
        today_attendance = query_db('attendance', date=today) or []
        total_students_list = query_db('student', is_active=True) or []
        total_students = len(total_students_list)
        
        if total_students > 0:
            present_count = len([a for a in today_attendance if a and a.get('status') == 'Present'])
            attendance_percentage = (present_count / total_students) * 100
            
            if attendance_percentage < 80:
                notifications.append({
                    'id': 'low_attendance',
                    'type': 'warning',
                    'title': 'Low Attendance',
                    'message': f'Today\'s attendance: {attendance_percentage:.1f}%',
                    'time': 'today',
                    'action': '/attendance',
                    'icon': 'fas fa-calendar-times'
                })
        
        # Check for recent SMS/WhatsApp activity
        recent_sms = get_from_db('sms_log') or []
        failed_sms = []
        for s in recent_sms:
            if s and s.get('status') != 'sent':
                try:
                    sent_at = s.get('sent_at', datetime.now().isoformat())
                    if isinstance(sent_at, str):
                        sent_date = datetime.fromisoformat(sent_at)
                        if (datetime.now() - sent_date).days <= 1:
                            failed_sms.append(s)
                except:
                    continue
        
        if len(failed_sms) > 0:
            notifications.append({
                'id': 'message_failures',
                'type': 'error',
                'title': 'Message Failures',
                'message': f'{len(failed_sms)} messages failed to send',
                'time': 'recent',
                'action': '/sms_management',
                'icon': 'fas fa-exclamation-triangle'
            })
        
        # Add success notification if no issues
        if len(notifications) == 0:
            notifications.append({
                'id': 'all_good',
                'type': 'success',
                'title': 'All Systems Running',
                'message': 'School management system is operating normally',
                'time': 'now',
                'action': '/dashboard',
                'icon': 'fas fa-check-circle'
            })
        
        return jsonify(notifications)
        
    except Exception as e:
        print(f"Notification error: {e}")
        return jsonify([{
            'id': 'system_error',
            'type': 'error',
            'title': 'System Error',
            'message': 'Error loading notifications',
            'time': 'now',
            'action': '/dashboard',
            'icon': 'fas fa-exclamation-circle'
        }])

@app.route('/mark_notification_read', methods=['POST'])
@login_required
def mark_notification_read():
    """Mark notification as read"""
    try:
        notification_id = request.json.get('id')
        # In a real app, you would update the notification status in the database
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/check_class_deletion/<class_id>')
@login_required
def check_class_deletion(class_id):
    """API endpoint to check if class can be deleted"""
    try:
        can_delete, message = can_delete_class(class_id)
        
        return jsonify({
            'can_delete': can_delete,
            'message': message,
            'class_id': class_id
        })
    except Exception as e:
        return jsonify({
            'can_delete': False,
            'message': f'Error checking class: {str(e)}',
            'class_id': class_id
        })

@app.route('/class_schedule')
@login_required
def class_schedule():
    """Class schedule management page"""
    try:
        # Get filter parameters
        selected_class = request.args.get('class_filter', '')
        selected_day = request.args.get('day_filter', '')
        selected_subject = request.args.get('subject_filter', '')

        # Get all data
        classes = get_from_db('class') or []
        teachers = query_db('teacher', is_active=True) or []
        schedules = get_from_db('schedule') or []
        subjects = get_from_db('subject') or []

        # Add default subjects if none exist
        if not subjects:
            default_subjects = [
                {'name': 'বাংলা', 'code': 'BAN', 'color': '#4CAF50', 'is_active': True},
                {'name': 'ইংরেজি', 'code': 'ENG', 'color': '#2196F3', 'is_active': True},
                {'name': 'গণিত', 'code': 'MAT', 'color': '#FF9800', 'is_active': True},
                {'name': 'বিজ্ঞান', 'code': 'SCI', 'color': '#9C27B0', 'is_active': True},
                {'name': 'সমাজবিজ্ঞান', 'code': 'SOC', 'color': '#607D8B', 'is_active': True},
                {'name': 'ধর্ম ও নৈতিক শিক্ষা', 'code': 'REL', 'color': '#795548', 'is_active': True},
                {'name': 'শারীরিক শিক্ষা', 'code': 'PE', 'color': '#E91E63', 'is_active': True},
            ]
            for subject_data in default_subjects:
                subject_data['created_at'] = datetime.now(timezone.utc).isoformat()
                save_to_db('subject', subject_data)
            subjects = get_from_db('subject')

        # Filter schedules based on parameters
        filtered_schedules = []
        for schedule in schedules:
            if schedule:
                # Apply filters
                if selected_class and schedule.get('class_id') != selected_class:
                    continue
                if selected_day and schedule.get('day_of_week') != selected_day:
                    continue
                if selected_subject and schedule.get('subject') != selected_subject:
                    continue

                # Add teacher information
                teacher_data = get_from_db('teacher', schedule.get('teacher_id'))
                if teacher_data:
                    schedule['teacher_name'] = teacher_data.get('name')

                # Add subject color
                subject_data = next((s for s in subjects if s.get('name') == schedule.get('subject')), None)
                if subject_data:
                    schedule['subject_color'] = subject_data.get('color', '#e3f2fd')
                else:
                    schedule['subject_color'] = '#e3f2fd'

                filtered_schedules.append(schedule)

        # Define time slots
        time_slots = [
            "09:00-09:45",
            "09:45-10:30", 
            "10:30-11:15",
            "11:15-12:00",
            "12:00-12:45",
            "02:00-02:45",
            "02:45-03:30",
            "03:30-04:15"
        ]

        # Get unique subjects from schedules for filter
        schedule_subjects = list(set([s.get('subject') for s in schedules if s and s.get('subject')]))

        return render_template('class_schedule.html',
                             classes=classes,
                             teachers=teachers,
                             schedules=filtered_schedules,
                             subjects=subjects,
                             schedule_subjects=schedule_subjects,
                             time_slots=time_slots,
                             selected_class=selected_class,
                             selected_day=selected_day,
                             selected_subject=selected_subject)
    except Exception as e:
        print(f"Class schedule error: {e}")
        flash('Error loading class schedule. Please try again.', 'error')
        return render_template('class_schedule.html',
                             classes=[],
                             teachers=[],
                             schedules=[],
                             subjects=[],
                             schedule_subjects=[],
                             time_slots=[],
                             selected_class='',
                             selected_day='',
                             selected_subject='')

@app.route('/add_schedule', methods=['POST'])
@login_required
def add_schedule():
    """Add new schedule entry"""
    try:
        class_id = request.form.get('class_id')
        day_of_week = request.form.get('day_of_week')
        time_slot = request.form.get('time_slot')
        subject = request.form.get('subject')
        teacher_id = request.form.get('teacher_id') or None
        room_number = request.form.get('room_number') or ''
        color = request.form.get('color') or '#e3f2fd'

        # Check for conflicts
        existing_schedules = query_db('schedule', 
                                    class_id=class_id, 
                                    day_of_week=day_of_week, 
                                    time_slot=time_slot)
        if existing_schedules:
            flash('Schedule conflict! This time slot is already occupied.', 'error')
            return redirect(url_for('class_schedule', class_filter=class_id))

        # Check teacher availability if teacher is assigned
        if teacher_id:
            teacher_schedules = query_db('schedule',
                                       teacher_id=teacher_id,
                                       day_of_week=day_of_week,
                                       time_slot=time_slot)
            if teacher_schedules:
                flash('Teacher is not available at this time slot.', 'error')
                return redirect(url_for('class_schedule', class_filter=class_id))

        # Create schedule
        schedule_data = {
            'class_id': class_id,
            'day_of_week': day_of_week,
            'time_slot': time_slot,
            'subject': subject,
            'teacher_id': teacher_id,
            'room_number': room_number,
            'color': color,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'created_by': current_user.id
        }

        save_to_db('schedule', schedule_data)
        flash('Schedule added successfully!', 'success')
        return redirect(url_for('class_schedule', class_filter=class_id))

    except Exception as e:
        print(f"Add schedule error: {e}")
        flash('Error adding schedule. Please try again.', 'error')
        return redirect(url_for('class_schedule'))

@app.route('/edit_schedule/<schedule_id>', methods=['POST'])
@login_required
def edit_schedule(schedule_id):
    """Edit existing schedule"""
    try:
        schedule = get_from_db('schedule', schedule_id)
        if not schedule:
            flash('Schedule not found.', 'error')
            return redirect(url_for('class_schedule'))

        subject = request.form.get('subject')
        teacher_id = request.form.get('teacher_id') or None

        # Check teacher availability if teacher is being changed
        if teacher_id and teacher_id != schedule.get('teacher_id'):
            teacher_schedules = query_db('schedule',
                                       teacher_id=teacher_id,
                                       day_of_week=schedule.get('day_of_week'),
                                       time_slot=schedule.get('time_slot'))
            # Exclude current schedule from conflict check
            teacher_schedules = [s for s in teacher_schedules if s.get('id') != schedule_id]
            if teacher_schedules:
                flash('Teacher is not available at this time slot.', 'error')
                return redirect(url_for('class_schedule', class_filter=schedule.get('class_id')))

        # Update schedule
        schedule['subject'] = subject
        schedule['teacher_id'] = teacher_id
        schedule['updated_at'] = datetime.now(timezone.utc).isoformat()
        schedule['updated_by'] = current_user.id

        update_in_db('schedule', schedule_id, schedule)
        flash('Schedule updated successfully!', 'success')
        return redirect(url_for('class_schedule', class_filter=schedule.get('class_id')))

    except Exception as e:
        print(f"Edit schedule error: {e}")
        flash('Error updating schedule. Please try again.', 'error')
        return redirect(url_for('class_schedule'))

@app.route('/delete_schedule/<schedule_id>', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Delete schedule entry"""
    try:
        schedule = get_from_db('schedule', schedule_id)
        if not schedule:
            return jsonify({'success': False, 'message': 'Schedule not found'})

        class_id = schedule.get('class_id')
        
        if delete_from_db('schedule', schedule_id):
            return jsonify({'success': True, 'message': 'Schedule deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Error deleting schedule'})

    except Exception as e:
        print(f"Delete schedule error: {e}")
        return jsonify({'success': False, 'message': 'Error deleting schedule'})

@app.route('/print_schedule/<class_id>')
@login_required
def print_schedule(class_id):
    """Generate printable schedule for a class"""
    try:
        class_data = get_from_db('class', class_id)
        if not class_data:
            flash('Class not found.', 'error')
            return redirect(url_for('class_schedule'))

        schedules = query_db('schedule', class_id=class_id)
        
        # Add teacher information
        for schedule in schedules:
            teacher_data = get_from_db('teacher', schedule.get('teacher_id'))
            if teacher_data:
                schedule['teacher_name'] = teacher_data.get('name')

        time_slots = [
            "09:00-09:45", "09:45-10:30", "10:30-11:15", "11:15-12:00",
            "12:00-12:45", "02:00-02:45", "02:45-03:30", "03:30-04:15"
        ]

        return render_template('print_schedule.html',
                             class_data=class_data,
                             schedules=schedules,
                             time_slots=time_slots)
    except Exception as e:
        print(f"Print schedule error: {e}")
        flash('Error generating printable schedule.', 'error')
        return redirect(url_for('class_schedule'))

@app.route('/teacher_schedule/<teacher_id>')
@login_required
def teacher_schedule(teacher_id):
    """View teacher's schedule"""
    try:
        teacher = get_from_db('teacher', teacher_id)
        if not teacher:
            flash('Teacher not found.', 'error')
            return redirect(url_for('teachers'))

        # Get teacher's schedules
        schedules = query_db('schedule', teacher_id=teacher_id)

        # Add class information
        for schedule in schedules:
            class_data = get_from_db('class', schedule.get('class_id'))
            if class_data:
                schedule['class_name'] = f"{class_data.get('name')} - {class_data.get('section')}"

        time_slots = [
            "09:00-09:45", "09:45-10:30", "10:30-11:15", "11:15-12:00",
            "12:00-12:45", "02:00-02:45", "02:45-03:30", "03:30-04:15"
        ]

        return render_template('teacher_schedule.html',
                             teacher=teacher,
                             schedules=schedules,
                             time_slots=time_slots)
    except Exception as e:
        print(f"Teacher schedule error: {e}")
        flash('Error loading teacher schedule.', 'error')
        return redirect(url_for('teachers'))

@app.route('/manage_subjects')
@login_required
def manage_subjects():
    """Subject management page"""
    try:
        subjects = get_from_db('subject') or []
        active_subjects = [s for s in subjects if s.get('is_active', True)]
        return render_template('manage_subjects.html', subjects=active_subjects)
    except Exception as e:
        print(f"Manage subjects error: {e}")
        flash('Error loading subjects. Please try again.', 'error')
        return render_template('manage_subjects.html', subjects=[])

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    """Add new subject"""
    try:
        name = request.form.get('name')
        code = request.form.get('code')
        color = request.form.get('color', '#e3f2fd')
        description = request.form.get('description', '')

        # Check if subject already exists
        existing_subjects = query_db('subject', name=name)
        if existing_subjects:
            flash('Subject already exists!', 'error')
            return redirect(url_for('manage_subjects'))

        subject_data = {
            'name': name,
            'code': code,
            'color': color,
            'description': description,
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'created_by': current_user.id
        }

        save_to_db('subject', subject_data)
        flash('Subject added successfully!', 'success')
        return redirect(url_for('manage_subjects'))

    except Exception as e:
        print(f"Add subject error: {e}")
        flash('Error adding subject.', 'error')
        return redirect(url_for('manage_subjects'))

@app.route('/edit_subject/<subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    """Edit existing subject"""
    try:
        subject = get_from_db('subject', subject_id)
        if not subject:
            flash('Subject not found.', 'error')
            return redirect(url_for('manage_subjects'))

        name = request.form.get('name')
        code = request.form.get('code')
        color = request.form.get('color')
        description = request.form.get('description', '')

        # Check if name already exists (exclude current subject)
        existing_subjects = query_db('subject', name=name)
        name_exists = any(s.get('id') != subject_id for s in existing_subjects if s)
        if name_exists:
            flash('Subject name already exists!', 'error')
            return redirect(url_for('manage_subjects'))

        subject_data = {
            'name': name,
            'code': code,
            'color': color,
            'description': description,
            'is_active': subject.get('is_active', True),
            'created_at': subject.get('created_at'),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'updated_by': current_user.id
        }

        update_in_db('subject', subject_id, subject_data)
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('manage_subjects'))

    except Exception as e:
        print(f"Edit subject error: {e}")
        flash('Error updating subject.', 'error')
        return redirect(url_for('manage_subjects'))

@app.route('/delete_subject/<subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    """Delete subject"""
    try:
        subject = get_from_db('subject', subject_id)
        if not subject:
            return jsonify({'success': False, 'message': 'Subject not found'})

        # Check if subject is used in schedules
        schedules = query_db('schedule', subject=subject.get('name'))
        if schedules:
            return jsonify({'success': False, 'message': f'Cannot delete subject. It is used in {len(schedules)} schedule(s).'})

        # Soft delete
        subject['is_active'] = False
        subject['deleted_at'] = datetime.now(timezone.utc).isoformat()
        subject['deleted_by'] = current_user.id
        
        if update_in_db('subject', subject_id, subject):
            return jsonify({'success': True, 'message': 'Subject deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Error deleting subject'})

    except Exception as e:
        print(f"Delete subject error: {e}")
        return jsonify({'success': False, 'message': 'Error deleting subject'})

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    print(f"[ERROR 404] {request.path} - {error}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    print(f"[ERROR 500] {request.path} - {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    print(f"[ERROR 403] {request.path} - Access denied")
    flash('Access denied. You do not have permission to access this resource.', 'error')
    return redirect(url_for('index')), 403

@app.errorhandler(401)
def unauthorized_error(error):
    """Handle 401 errors"""
    print(f"[ERROR 401] {request.path} - Unauthorized")
    flash('You need to login to access this page.', 'error')
    return redirect(url_for('login')), 401

# ==================== DATABASE ERROR RECOVERY ====================

def safe_query_db(collection, **filters):
    """Safe database query with error handling"""
    try:
        return query_db(collection, **filters)
    except Exception as e:
        print(f"[DB ERROR] Query failed for collection '{collection}': {e}")
        print(f"[DB ERROR] Filters: {filters}")
        return []

def safe_get_from_db(collection, data_id=None):
    """Safe database get with error handling"""
    try:
        return get_from_db(collection, data_id)
    except Exception as e:
        print(f"[DB ERROR] Get failed for collection '{collection}', id '{data_id}': {e}")
        return None if data_id else []

def safe_save_to_db(collection, data):
    """Safe database save with error handling"""
    try:
        return save_to_db(collection, data)
    except Exception as e:
        print(f"[DB ERROR] Save failed for collection '{collection}': {e}")
        print(f"[DB ERROR] Data: {data}")
        return None

def safe_update_in_db(collection, data_id, data):
    """Safe database update with error handling"""
    try:
        return update_in_db(collection, data_id, data)
    except Exception as e:
        print(f"[DB ERROR] Update failed for collection '{collection}', id '{data_id}': {e}")
        print(f"[DB ERROR] Data: {data}")
        return False

def safe_delete_from_db(collection, data_id):
    """Safe database delete with error handling"""
    try:
        return delete_from_db(collection, data_id)
    except Exception as e:
        print(f"[DB ERROR] Delete failed for collection '{collection}', id '{data_id}': {e}")
        return False

# ==================== REQUEST LOGGING ====================

@app.before_request
def log_request():
    """Log incoming requests"""
    print(f"[REQUEST] {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response(response):
    """Log outgoing responses"""
    print(f"[RESPONSE] {response.status_code} {request.method} {request.path}")
    return response

# ==================== APPLICATION INITIALIZATION ====================

if __name__ == '__main__':
    init_app()
    print("\n" + "="*70)
    print("SCHOOL MANAGEMENT SYSTEM STARTED")
    print("="*70)
    print(f"Database: {DATABASE}")
    port = int(os.environ.get('PORT', 8000))
    print(f"Running on: http://0.0.0.0:{port}")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)
