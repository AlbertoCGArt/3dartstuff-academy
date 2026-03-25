from flask import Blueprint, render_template
from app.models import Course

main = Blueprint('main', __name__)

@main.route('/')
def index():
    courses = Course.query.filter_by(is_published=True).all()
    free_courses = [c for c in courses if c.is_free]
    paid_courses = [c for c in courses if not c.is_free]
    return render_template('main/index.html', free_courses=free_courses, paid_courses=paid_courses)
