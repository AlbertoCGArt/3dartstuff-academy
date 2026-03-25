import os

files = {}

files['run.py'] = """from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5055)
"""

files['app/__init__.py'] = """from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///academy.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY', '')
    app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY', '')

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'

    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.courses import courses
    from app.routes.admin import admin

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(courses)
    app.register_blueprint(admin)

    return app
"""

files['app/models/__init__.py'] = """from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    enrollments = db.relationship('Enrollment', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_enrolled(self, course_id):
        return Enrollment.query.filter_by(user_id=self.id, course_id=course_id).first() is not None

    def lesson_completed(self, lesson_id):
        p = Progress.query.filter_by(user_id=self.id, lesson_id=lesson_id).first()
        return p.completed if p else False

    def course_progress(self, course_id):
        from app.models import Lesson
        total = Lesson.query.filter_by(course_id=course_id).count()
        if total == 0:
            return 0
        completed = Progress.query.join(Lesson).filter(
            Progress.user_id == self.id,
            Lesson.course_id == course_id,
            Progress.completed == True
        ).count()
        return int((completed / total) * 100)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(300))
    thumbnail = db.Column(db.String(300), default='')
    price = db.Column(db.Float, default=0.0)
    is_free = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    stripe_price_id = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lessons = db.relationship('Lesson', backref='course', lazy=True, order_by='Lesson.order')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

    @property
    def lesson_count(self):
        return len(self.lessons)

    @property
    def enrollment_count(self):
        return len(self.enrollments)

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    video_url = db.Column(db.String(500), default='')
    duration = db.Column(db.String(20), default='')
    order = db.Column(db.Integer, default=0)
    is_free_preview = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.relationship('Progress', backref='lesson', lazy=True)

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(200), default='')
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

class Progress(db.Model):
    __tablename__ = 'progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
"""

files['app/routes/__init__.py'] = ""

files['app/routes/main.py'] = """from flask import Blueprint, render_template
from app.models import Course

main = Blueprint('main', __name__)

@main.route('/')
def index():
    courses = Course.query.filter_by(is_published=True).all()
    free_courses = [c for c in courses if c.is_free]
    paid_courses = [c for c in courses if not c.is_free]
    return render_template('main/index.html', free_courses=free_courses, paid_courses=paid_courses)
"""

files['app/routes/auth.py'] = """from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.signup'))
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('auth.signup'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Welcome to 3DArtStuff Academy!', 'success')
        return redirect(url_for('main.index'))
    return render_template('auth/signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/dashboard')
@login_required
def dashboard():
    from app.models import Enrollment
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_courses = [e.course for e in enrollments]
    return render_template('auth/dashboard.html', courses=enrolled_courses)
"""

files['app/routes/courses.py'] = """from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models import Course, Lesson, Enrollment, Progress
from app import db
import stripe
from datetime import datetime

courses = Blueprint('courses', __name__)

@courses.route('/courses')
def list_courses():
    all_courses = Course.query.filter_by(is_published=True).all()
    return render_template('courses/list.html', courses=all_courses)

@courses.route('/courses/<slug>')
def course_detail(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    enrolled = False
    if current_user.is_authenticated:
        enrolled = current_user.is_enrolled(course.id)
    return render_template('courses/detail.html', course=course, enrolled=enrolled)

@courses.route('/courses/<course_slug>/lessons/<lesson_slug>')
@login_required
def lesson(course_slug, lesson_slug):
    course = Course.query.filter_by(slug=course_slug).first_or_404()
    lesson = Lesson.query.filter_by(course_id=course.id, slug=lesson_slug).first_or_404()
    if not course.is_free and not current_user.is_enrolled(course.id):
        if not lesson.is_free_preview:
            flash('Please enroll in this course to access this lesson.', 'error')
            return redirect(url_for('courses.course_detail', slug=course_slug))
    lessons = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.order).all()
    current_index = next((i for i, l in enumerate(lessons) if l.id == lesson.id), 0)
    prev_lesson = lessons[current_index - 1] if current_index > 0 else None
    next_lesson = lessons[current_index + 1] if current_index < len(lessons) - 1 else None
    completed = current_user.lesson_completed(lesson.id)
    progress_pct = current_user.course_progress(course.id)
    return render_template('courses/lesson.html',
        course=course, lesson=lesson, lessons=lessons,
        prev_lesson=prev_lesson, next_lesson=next_lesson,
        completed=completed, progress_pct=progress_pct)

@courses.route('/courses/<course_slug>/lessons/<lesson_slug>/complete', methods=['POST'])
@login_required
def complete_lesson(course_slug, lesson_slug):
    course = Course.query.filter_by(slug=course_slug).first_or_404()
    lesson = Lesson.query.filter_by(course_id=course.id, slug=lesson_slug).first_or_404()
    progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = Progress(user_id=current_user.id, lesson_id=lesson.id)
        db.session.add(progress)
    progress.completed = True
    progress.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'progress': current_user.course_progress(course.id)})

@courses.route('/courses/<slug>/enroll', methods=['POST'])
@login_required
def enroll(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    if current_user.is_enrolled(course.id):
        flash('You are already enrolled!', 'info')
        return redirect(url_for('courses.course_detail', slug=slug))
    if course.is_free:
        enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
        db.session.add(enrollment)
        db.session.commit()
        flash('You are now enrolled!', 'success')
        first_lesson = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.order).first()
        if first_lesson:
            return redirect(url_for('courses.lesson', course_slug=slug, lesson_slug=first_lesson.slug))
        return redirect(url_for('courses.course_detail', slug=slug))
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    try:
        checkout = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': course.title},
                    'unit_amount': int(course.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('courses.enroll_success', slug=slug, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('courses.course_detail', slug=slug, _external=True),
            metadata={'course_id': course.id, 'user_id': current_user.id}
        )
        return redirect(checkout.url)
    except Exception as e:
        flash(f'Payment error: {str(e)}', 'error')
        return redirect(url_for('courses.course_detail', slug=slug))

@courses.route('/courses/<slug>/success')
@login_required
def enroll_success(slug):
    course = Course.query.filter_by(slug=slug).first_or_404()
    session_id = request.args.get('session_id')
    if not current_user.is_enrolled(course.id):
        enrollment = Enrollment(user_id=current_user.id, course_id=course.id, stripe_payment_id=session_id)
        db.session.add(enrollment)
        db.session.commit()
    flash(f'Successfully enrolled in {course.title}!', 'success')
    first_lesson = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.order).first()
    if first_lesson:
        return redirect(url_for('courses.lesson', course_slug=slug, lesson_slug=first_lesson.slug))
    return redirect(url_for('courses.course_detail', slug=slug))
"""

files['app/routes/admin.py'] = """from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Course, Lesson, User, Enrollment
from app import db
from functools import wraps
import re

admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\\w\\s-]', '', text)
    text = re.sub(r'[\\s_-]+', '-', text)
    return text.strip('-')

@admin.route('/')
@login_required
@admin_required
def dashboard():
    courses = Course.query.all()
    users = User.query.count()
    enrollments = Enrollment.query.count()
    return render_template('admin/dashboard.html', courses=courses, user_count=users, enrollment_count=enrollments)

@admin.route('/courses/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_course():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = slugify(title)
        existing = Course.query.filter_by(slug=slug).first()
        if existing:
            slug = slug + '-2'
        course = Course(
            title=title, slug=slug,
            description=request.form.get('description'),
            short_description=request.form.get('short_description'),
            thumbnail=request.form.get('thumbnail', ''),
            price=float(request.form.get('price', 0)),
            is_free=request.form.get('is_free') == 'on',
            is_published=request.form.get('is_published') == 'on',
            stripe_price_id=request.form.get('stripe_price_id', '')
        )
        db.session.add(course)
        db.session.commit()
        flash(f'Course created!', 'success')
        return redirect(url_for('admin.edit_course', course_id=course.id))
    return render_template('admin/course_form.html', course=None)

@admin.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.short_description = request.form.get('short_description')
        course.thumbnail = request.form.get('thumbnail', '')
        course.price = float(request.form.get('price', 0))
        course.is_free = request.form.get('is_free') == 'on'
        course.is_published = request.form.get('is_published') == 'on'
        course.stripe_price_id = request.form.get('stripe_price_id', '')
        db.session.commit()
        flash('Course updated!', 'success')
    return render_template('admin/course_form.html', course=course)

@admin.route('/courses/<int:course_id>/lessons/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_lesson(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        title = request.form.get('title')
        slug = slugify(title)
        existing = Lesson.query.filter_by(course_id=course_id, slug=slug).first()
        if existing:
            slug = slug + '-2'
        order = Lesson.query.filter_by(course_id=course_id).count() + 1
        lesson = Lesson(
            course_id=course_id, title=title, slug=slug,
            content=request.form.get('content', ''),
            video_url=request.form.get('video_url', ''),
            duration=request.form.get('duration', ''),
            order=order,
            is_free_preview=request.form.get('is_free_preview') == 'on'
        )
        db.session.add(lesson)
        db.session.commit()
        flash(f'Lesson created!', 'success')
        return redirect(url_for('admin.edit_course', course_id=course_id))
    return render_template('admin/lesson_form.html', course=course, lesson=None)

@admin.route('/courses/<int:course_id>/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(course_id, lesson_id):
    course = Course.query.get_or_404(course_id)
    lesson = Lesson.query.get_or_404(lesson_id)
    if request.method == 'POST':
        lesson.title = request.form.get('title')
        lesson.content = request.form.get('content', '')
        lesson.video_url = request.form.get('video_url', '')
        lesson.duration = request.form.get('duration', '')
        lesson.order = int(request.form.get('order', lesson.order))
        lesson.is_free_preview = request.form.get('is_free_preview') == 'on'
        db.session.commit()
        flash('Lesson updated!', 'success')
    return render_template('admin/lesson_form.html', course=course, lesson=lesson)
"""

# Create all directories and files
for path, content in files.items():
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

print("\nAll Python files created!")
print("Now run: git add . && git commit -m 'Add all source files' && git push")