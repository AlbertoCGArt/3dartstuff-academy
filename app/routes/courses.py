from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
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
