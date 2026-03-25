from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Course, Lesson, User, Enrollment
from app import db
from functools import wraps
import re
import requests

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
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
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

@admin.route('/upload-video', methods=['POST'])
@login_required
@admin_required
def upload_video():
    import requests
    import os
    video = request.files.get('video')
    if not video:
        return jsonify({'error': 'No video file'}), 400
    library_id = os.getenv('BUNNY_LIBRARY_ID')
    api_key = os.getenv('BUNNY_API_KEY')
    title = request.form.get('title', video.filename)
    # Create video object
    create_url = f'https://video.bunnycdn.com/library/{library_id}/videos'
    headers = {'AccessKey': api_key, 'Content-Type': 'application/json'}
    import json
    r = requests.post(create_url, headers=headers, data=json.dumps({'title': title}))
    video_data = r.json()
    video_id = video_data.get('guid')
    if not video_id:
        return jsonify({'error': 'Failed to create video'}), 500
    # Upload video
    upload_url = f'https://video.bunnycdn.com/library/{library_id}/videos/{video_id}'
    upload_headers = {'AccessKey': api_key, 'Content-Type': 'application/octet-stream'}
    requests.put(upload_url, headers=upload_headers, data=video.read())
    # Return embed URL
    embed_url = f'https://iframe.mediadelivery.net/embed/{library_id}/{video_id}'
    return jsonify({'success': True, 'video_id': video_id, 'embed_url': embed_url})

@admin.route('/media')
@login_required
@admin_required
def media():
    import requests, os
    library_id = os.getenv('BUNNY_LIBRARY_ID')
    api_key = os.getenv('BUNNY_API_KEY')
    storage_api_key = os.getenv('BUNNY_STORAGE_API_KEY', api_key)
    storage_zone = os.getenv('BUNNY_STORAGE_ZONE', '3dartstuff-academy')

    # Get videos from Bunny Stream
    videos = []
    try:
        r = requests.get(
            f'https://video.bunnycdn.com/library/{library_id}/videos?page=1&itemsPerPage=50',
            headers={'AccessKey': api_key}
        )
        if r.status_code == 200:
            videos = r.json().get('items', [])
    except:
        pass

    return render_template('admin/media.html', videos=videos, library_id=library_id)

@admin.route('/upload-image', methods=['POST'])
@login_required
@admin_required
def upload_image():
    import requests, os, uuid
    image = request.files.get('image')
    if not image:
        return jsonify({'error': 'No image file'}), 400
    storage_api_key = os.getenv('BUNNY_STORAGE_API_KEY', os.getenv('BUNNY_API_KEY'))
    storage_zone = os.getenv('BUNNY_STORAGE_ZONE', '3dartstuff-academy')
    storage_host = os.getenv('BUNNY_STORAGE_HOST', 'ny.storage.bunnycdn.com')
    cdn_base = os.getenv('BUNNY_CDN_URL', f'https://{storage_zone}-cdn.b-cdn.net')
    ext = image.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_url = f'https://{storage_host}/{storage_zone}/images/{filename}'
    headers = {'AccessKey': storage_api_key, 'Content-Type': 'application/octet-stream'}
    r = requests.put(upload_url, headers=headers, data=image.read())
    if r.status_code in [200, 201]:
        cdn_url = f'{cdn_base}/images/{filename}'
        return jsonify({'success': True, 'url': cdn_url, 'filename': filename})
    return jsonify({'error': f'Upload failed: {r.status_code} - {r.text}'}), 500

@admin.route('/delete-video/<video_id>', methods=['POST'])
@login_required
@admin_required
def delete_video(video_id):
    import requests, os
    library_id = os.getenv('BUNNY_LIBRARY_ID')
    api_key = os.getenv('BUNNY_API_KEY')
    r = requests.delete(
        f'https://video.bunnycdn.com/library/{library_id}/videos/{video_id}',
        headers={'AccessKey': api_key}
    )
    return jsonify({'success': r.status_code in [200, 204]})
