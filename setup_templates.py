import os

files = {}

files['app/templates/base.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}3DArtStuff Academy{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
  {% block head %}{% endblock %}
</head>
<body>
  <nav id="nav">
    <a href="{{ url_for('main.index') }}" class="nav-logo">3D<span>Art</span>Academy</a>
    <ul class="nav-links">
      <li><a href="{{ url_for('courses.list_courses') }}">Courses</a></li>
      <li><a href="https://3dartstuff.com" target="_blank">Portfolio</a></li>
      {% if current_user.is_authenticated %}
        <li><a href="{{ url_for('auth.dashboard') }}">My Learning</a></li>
        {% if current_user.is_admin %}
          <li><a href="{{ url_for('admin.dashboard') }}" class="admin-link">Admin</a></li>
        {% endif %}
      {% endif %}
    </ul>
    <div class="nav-right">
      {% if current_user.is_authenticated %}
        <span class="nav-user">{{ current_user.username }}</span>
        <a href="{{ url_for('auth.logout') }}" class="btn-ghost-sm">Logout</a>
      {% else %}
        <a href="{{ url_for('auth.login') }}" class="btn-ghost-sm">Login</a>
        <a href="{{ url_for('auth.signup') }}" class="btn-primary-sm">Sign Up Free</a>
      {% endif %}
    </div>
  </nav>
  <div class="flash-messages">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="flash flash-{{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}
  </div>
  <main>{% block content %}{% endblock %}</main>
  <footer>
    <span class="footer-brand">3D<span>Art</span>Academy</span>
    <span class="footer-copy">2026 3DArtStuff - Alberto CGArt</span>
    <div class="footer-links">
      <a href="https://3dartstuff.com" target="_blank">Portfolio</a>
      <a href="https://albertocgart.gumroad.com" target="_blank">Gumroad</a>
      <a href="https://www.youtube.com/@AlbertoCGArt" target="_blank">YouTube</a>
    </div>
  </footer>
  <script src="{{ url_for('static', filename='js/main.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>"""

files['app/templates/main/index.html'] = """{% extends 'base.html' %}
{% block title %}3DArtStuff Academy - Learn Hard Surface 3D Art{% endblock %}
{% block content %}
<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-scan"></div>
  <p class="hero-label">Hard Surface 3D Art Education</p>
  <h1 class="hero-title"><span class="dim">3D</span><br><span class="accent">ART</span><br>ACADEMY</h1>
  <div class="hero-bottom">
    <p class="hero-desc">Master hard surface modeling in Blender and Plasticity. Real-time lessons, no fluff, taught by a working 3D artist at Sony.</p>
    <div class="hero-actions">
      <a href="{{ url_for('courses.list_courses') }}" class="btn-primary">Browse Courses</a>
      {% if not current_user.is_authenticated %}
        <a href="{{ url_for('auth.signup') }}" class="btn-ghost">Sign Up Free</a>
      {% endif %}
    </div>
  </div>
</section>
{% if free_courses %}
<section class="courses-section">
  <div class="section-header">
    <p class="section-tag">Free Courses</p>
    <h2 class="section-heading">Start Learning Today</h2>
  </div>
  <div class="course-grid">
    {% for course in free_courses %}
    <a href="{{ url_for('courses.course_detail', slug=course.slug) }}" class="course-card">
      <div class="course-thumb">
        {% if course.thumbnail %}<img src="{{ course.thumbnail }}" alt="{{ course.title }}">
        {% else %}<div class="thumb-placeholder">{{ course.title[0] }}</div>{% endif %}
      </div>
      <div class="course-info">
        <span class="course-badge free">Free</span>
        <h3 class="course-title">{{ course.title }}</h3>
        <p class="course-desc">{{ course.short_description }}</p>
        <div class="course-meta">
          <span>{{ course.lesson_count }} lessons</span>
          <span>{{ course.enrollment_count }} students</span>
        </div>
      </div>
    </a>
    {% endfor %}
  </div>
</section>
{% endif %}
{% if paid_courses %}
<section class="courses-section dark">
  <div class="section-header">
    <p class="section-tag">Premium Courses</p>
    <h2 class="section-heading">Go Deeper</h2>
  </div>
  <div class="course-grid">
    {% for course in paid_courses %}
    <a href="{{ url_for('courses.course_detail', slug=course.slug) }}" class="course-card">
      <div class="course-thumb">
        {% if course.thumbnail %}<img src="{{ course.thumbnail }}" alt="{{ course.title }}">
        {% else %}<div class="thumb-placeholder">{{ course.title[0] }}</div>{% endif %}
      </div>
      <div class="course-info">
        <span class="course-badge paid">${{ "%.0f"|format(course.price) }}</span>
        <h3 class="course-title">{{ course.title }}</h3>
        <p class="course-desc">{{ course.short_description }}</p>
        <div class="course-meta">
          <span>{{ course.lesson_count }} lessons</span>
          <span>{{ course.enrollment_count }} students</span>
        </div>
      </div>
    </a>
    {% endfor %}
  </div>
</section>
{% endif %}
<section class="cta-section">
  <h2 class="cta-heading">Built by a working artist.<br><span>Taught like one.</span></h2>
  <p class="cta-sub">No timelapses. No magic cuts. Real workflows from someone who ships 3D art professionally at Sony.</p>
  {% if not current_user.is_authenticated %}
    <a href="{{ url_for('auth.signup') }}" class="btn-primary">Create Free Account</a>
  {% else %}
    <a href="{{ url_for('courses.list_courses') }}" class="btn-primary">Browse All Courses</a>
  {% endif %}
</section>
{% endblock %}"""

files['app/templates/courses/list.html'] = """{% extends 'base.html' %}
{% block title %}All Courses - 3DArtStuff Academy{% endblock %}
{% block content %}
<div class="page-hero">
  <p class="section-tag">All Courses</p>
  <h1 class="page-hero-title">Learn <span>3D Art</span></h1>
  <p class="page-hero-desc">From beginner Blender basics to advanced hard surface techniques in Plasticity.</p>
</div>
<section class="courses-section">
  <div class="course-grid">
    {% for course in courses %}
    <a href="{{ url_for('courses.course_detail', slug=course.slug) }}" class="course-card">
      <div class="course-thumb">
        {% if course.thumbnail %}<img src="{{ course.thumbnail }}" alt="{{ course.title }}">
        {% else %}<div class="thumb-placeholder">{{ course.title[0] }}</div>{% endif %}
      </div>
      <div class="course-info">
        {% if course.is_free %}
          <span class="course-badge free">Free</span>
        {% else %}
          <span class="course-badge paid">${{ "%.0f"|format(course.price) }}</span>
        {% endif %}
        <h3 class="course-title">{{ course.title }}</h3>
        <p class="course-desc">{{ course.short_description }}</p>
        <div class="course-meta">
          <span>{{ course.lesson_count }} lessons</span>
          <span>{{ course.enrollment_count }} students</span>
        </div>
      </div>
    </a>
    {% else %}
    <div class="empty-state">
      <p>No courses published yet. Check back soon!</p>
    </div>
    {% endfor %}
  </div>
</section>
{% endblock %}"""

files['app/templates/courses/detail.html'] = """{% extends 'base.html' %}
{% block title %}{{ course.title }} - 3DArtStuff Academy{% endblock %}
{% block content %}
<div class="course-detail-hero">
  <div class="course-detail-info">
    <p class="section-tag">{{ 'Free Course' if course.is_free else 'Premium Course' }}</p>
    <h1 class="course-detail-title">{{ course.title }}</h1>
    <p class="course-detail-desc">{{ course.short_description }}</p>
    <div class="course-detail-meta">
      <span>{{ course.lesson_count }} lessons</span>
      <span>{{ course.enrollment_count }} students enrolled</span>
    </div>
    {% if enrolled %}
      <a href="{{ url_for('courses.lesson', course_slug=course.slug, lesson_slug=course.lessons[0].slug) }}" class="btn-primary">Continue Learning</a>
    {% elif course.is_free %}
      <form method="POST" action="{{ url_for('courses.enroll', slug=course.slug) }}">
        <button type="submit" class="btn-primary">Enroll Free</button>
      </form>
    {% else %}
      <form method="POST" action="{{ url_for('courses.enroll', slug=course.slug) }}">
        <button type="submit" class="btn-primary">Enroll - ${{ "%.0f"|format(course.price) }}</button>
      </form>
    {% endif %}
  </div>
  {% if course.thumbnail %}
  <div class="course-detail-thumb"><img src="{{ course.thumbnail }}" alt="{{ course.title }}"></div>
  {% endif %}
</div>
<div class="course-detail-body">
  <div class="course-description">
    <h2>About This Course</h2>
    <div class="content-body">{{ course.description|safe }}</div>
  </div>
  <div class="course-curriculum">
    <h2>Curriculum - {{ course.lesson_count }} Lessons</h2>
    <div class="lesson-list">
      {% for lesson in course.lessons %}
      <div class="lesson-row {% if lesson.is_free_preview %}preview{% endif %}">
        <div class="lesson-row-left">
          <span class="lesson-num">{{ loop.index }}</span>
          <span class="lesson-title">{{ lesson.title }}</span>
          {% if lesson.is_free_preview %}<span class="preview-badge">Free Preview</span>{% endif %}
        </div>
        <div class="lesson-row-right">
          {% if lesson.duration %}<span class="lesson-duration">{{ lesson.duration }}</span>{% endif %}
          {% if enrolled or lesson.is_free_preview %}
            <a href="{{ url_for('courses.lesson', course_slug=course.slug, lesson_slug=lesson.slug) }}" class="lesson-link">Watch</a>
          {% else %}
            <span class="lesson-lock">locked</span>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}"""

files['app/templates/courses/lesson.html'] = """{% extends 'base.html' %}
{% block title %}{{ lesson.title }} - {{ course.title }}{% endblock %}
{% block content %}
<div class="lesson-layout">
  <aside class="lesson-sidebar">
    <div class="sidebar-header">
      <a href="{{ url_for('courses.course_detail', slug=course.slug) }}" class="back-link">Back to {{ course.title }}</a>
      <div class="progress-bar-wrap"><div class="progress-bar" style="width: {{ progress_pct }}%"></div></div>
      <span class="progress-label">{{ progress_pct }}% complete</span>
    </div>
    <div class="lesson-nav">
      {% for l in lessons %}
      <a href="{{ url_for('courses.lesson', course_slug=course.slug, lesson_slug=l.slug) }}"
         class="lesson-nav-item {% if l.id == lesson.id %}active{% endif %}">
        <span class="lesson-nav-num">{{ loop.index }}</span>
        <span class="lesson-nav-title">{{ l.title }}</span>
        {% if current_user.lesson_completed(l.id) %}<span class="check">done</span>{% endif %}
      </a>
      {% endfor %}
    </div>
  </aside>
  <div class="lesson-main">
    <div class="lesson-header">
      <h1 class="lesson-title">{{ lesson.title }}</h1>
      {% if lesson.duration %}<span class="lesson-duration-badge">{{ lesson.duration }}</span>{% endif %}
    </div>
    {% if lesson.video_url %}
    <div class="video-wrap">
      <iframe src="{{ lesson.video_url }}" frameborder="0" allowfullscreen></iframe>
    </div>
    {% endif %}
    {% if lesson.content %}
    <div class="lesson-content content-body">{{ lesson.content|safe }}</div>
    {% endif %}
    <div class="lesson-footer">
      <div class="lesson-nav-btns">
        {% if prev_lesson %}
          <a href="{{ url_for('courses.lesson', course_slug=course.slug, lesson_slug=prev_lesson.slug) }}" class="btn-ghost">Previous</a>
        {% endif %}
        <button id="complete-btn" class="btn-primary {% if completed %}completed{% endif %}"
                data-course="{{ course.slug }}" data-lesson="{{ lesson.slug }}">
          {% if completed %}Completed{% else %}Mark Complete{% endif %}
        </button>
        {% if next_lesson %}
          <a href="{{ url_for('courses.lesson', course_slug=course.slug, lesson_slug=next_lesson.slug) }}" class="btn-primary">Next</a>
        {% endif %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
document.getElementById('complete-btn').addEventListener('click', function() {
  const btn = this;
  fetch('/courses/' + btn.dataset.course + '/lessons/' + btn.dataset.lesson + '/complete', {
    method: 'POST', headers: {'X-Requested-With': 'XMLHttpRequest'}
  }).then(r => r.json()).then(data => {
    if (data.success) {
      btn.textContent = 'Completed';
      btn.classList.add('completed');
      document.querySelector('.progress-bar').style.width = data.progress + '%';
      document.querySelector('.progress-label').textContent = data.progress + '% complete';
    }
  });
});
</script>
{% endblock %}"""

files['app/templates/auth/signup.html'] = """{% extends 'base.html' %}
{% block title %}Sign Up - 3DArtStuff Academy{% endblock %}
{% block content %}
<div class="auth-page">
  <div class="auth-card">
    <h1 class="auth-title">Create Account</h1>
    <p class="auth-sub">Join 3DArtStuff Academy and start learning for free.</p>
    <form method="POST" class="auth-form">
      <div class="form-group">
        <label>Username</label>
        <input type="text" name="username" required placeholder="albertocgart">
      </div>
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" required placeholder="you@email.com">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" required placeholder="min 8 characters">
      </div>
      <button type="submit" class="btn-primary btn-full">Create Account</button>
    </form>
    <p class="auth-switch">Already have an account? <a href="{{ url_for('auth.login') }}">Log in</a></p>
  </div>
</div>
{% endblock %}"""

files['app/templates/auth/login.html'] = """{% extends 'base.html' %}
{% block title %}Login - 3DArtStuff Academy{% endblock %}
{% block content %}
<div class="auth-page">
  <div class="auth-card">
    <h1 class="auth-title">Welcome Back</h1>
    <p class="auth-sub">Log in to continue your learning.</p>
    <form method="POST" class="auth-form">
      <div class="form-group">
        <label>Email</label>
        <input type="email" name="email" required placeholder="you@email.com">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" name="password" required placeholder="your password">
      </div>
      <button type="submit" class="btn-primary btn-full">Log In</button>
    </form>
    <p class="auth-switch">No account? <a href="{{ url_for('auth.signup') }}">Sign up free</a></p>
  </div>
</div>
{% endblock %}"""

files['app/templates/auth/dashboard.html'] = """{% extends 'base.html' %}
{% block title %}My Learning - 3DArtStuff Academy{% endblock %}
{% block content %}
<div class="page-hero">
  <p class="section-tag">My Learning</p>
  <h1 class="page-hero-title">Hey, <span>{{ current_user.username }}</span></h1>
</div>
<section class="courses-section">
  {% if courses %}
  <div class="course-grid">
    {% for course in courses %}
    <a href="{{ url_for('courses.course_detail', slug=course.slug) }}" class="course-card">
      <div class="course-thumb">
        {% if course.thumbnail %}<img src="{{ course.thumbnail }}" alt="{{ course.title }}">
        {% else %}<div class="thumb-placeholder">{{ course.title[0] }}</div>{% endif %}
      </div>
      <div class="course-info">
        <h3 class="course-title">{{ course.title }}</h3>
        <div class="progress-bar-wrap">
          <div class="progress-bar" style="width: {{ current_user.course_progress(course.id) }}%"></div>
        </div>
        <span class="progress-label">{{ current_user.course_progress(course.id) }}% complete</span>
      </div>
    </a>
    {% endfor %}
  </div>
  {% else %}
  <div class="empty-state">
    <p>No courses enrolled yet.</p>
    <a href="{{ url_for('courses.list_courses') }}" class="btn-primary">Browse Courses</a>
  </div>
  {% endif %}
</section>
{% endblock %}"""

files['app/templates/admin/dashboard.html'] = """{% extends 'base.html' %}
{% block title %}Admin - 3DArtStuff Academy{% endblock %}
{% block content %}
<div class="admin-page">
  <div class="admin-header">
    <h1>Admin Dashboard</h1>
    <a href="{{ url_for('admin.new_course') }}" class="btn-primary">+ New Course</a>
  </div>
  <div class="admin-stats">
    <div class="stat-card"><div class="stat-num">{{ user_count }}</div><div class="stat-label">Students</div></div>
    <div class="stat-card"><div class="stat-num">{{ enrollment_count }}</div><div class="stat-label">Enrollments</div></div>
    <div class="stat-card"><div class="stat-num">{{ courses|length }}</div><div class="stat-label">Courses</div></div>
  </div>
  <div class="admin-courses">
    <h2>Courses</h2>
    <table class="admin-table">
      <thead><tr><th>Title</th><th>Type</th><th>Lessons</th><th>Students</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>
        {% for course in courses %}
        <tr>
          <td>{{ course.title }}</td>
          <td>{% if course.is_free %}Free{% else %}${{ "%.0f"|format(course.price) }}{% endif %}</td>
          <td>{{ course.lesson_count }}</td>
          <td>{{ course.enrollment_count }}</td>
          <td><span class="status {% if course.is_published %}published{% else %}draft{% endif %}">{% if course.is_published %}Published{% else %}Draft{% endif %}</span></td>
          <td>
            <a href="{{ url_for('admin.edit_course', course_id=course.id) }}">Edit</a>
            <a href="{{ url_for('admin.new_lesson', course_id=course.id) }}">+ Lesson</a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}"""

files['app/templates/admin/course_form.html'] = """{% extends 'base.html' %}
{% block title %}{{ 'Edit' if course else 'New' }} Course - Admin{% endblock %}
{% block content %}
<div class="admin-page">
  <div class="admin-header">
    <h1>{{ 'Edit Course' if course else 'New Course' }}</h1>
    <a href="{{ url_for('admin.dashboard') }}" class="btn-ghost">Back</a>
  </div>
  <form method="POST" class="admin-form">
    <div class="form-group">
      <label>Title</label>
      <input type="text" name="title" required value="{{ course.title if course else '' }}">
    </div>
    <div class="form-group">
      <label>Short Description</label>
      <input type="text" name="short_description" value="{{ course.short_description if course else '' }}">
    </div>
    <div class="form-group">
      <label>Full Description (HTML ok)</label>
      <textarea name="description" rows="8">{{ course.description if course else '' }}</textarea>
    </div>
    <div class="form-group">
      <label>Thumbnail URL</label>
      <input type="text" name="thumbnail" value="{{ course.thumbnail if course else '' }}">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Price ($)</label>
        <input type="number" name="price" step="0.01" value="{{ course.price if course else '0' }}">
      </div>
      <div class="form-group">
        <label>Stripe Price ID</label>
        <input type="text" name="stripe_price_id" value="{{ course.stripe_price_id if course else '' }}">
      </div>
    </div>
    <div class="form-checks">
      <label class="check-label"><input type="checkbox" name="is_free" {% if course and course.is_free %}checked{% endif %}> Free Course</label>
      <label class="check-label"><input type="checkbox" name="is_published" {% if course and course.is_published %}checked{% endif %}> Published</label>
    </div>
    <button type="submit" class="btn-primary">{{ 'Update' if course else 'Create' }} Course</button>
  </form>
  {% if course %}
  <div class="admin-lessons">
    <div class="admin-subheader">
      <h2>Lessons</h2>
      <a href="{{ url_for('admin.new_lesson', course_id=course.id) }}" class="btn-primary">+ Add Lesson</a>
    </div>
    {% if course.lessons %}
    <table class="admin-table">
      <thead><tr><th>Order</th><th>Title</th><th>Duration</th><th>Free Preview</th><th>Actions</th></tr></thead>
      <tbody>
        {% for lesson in course.lessons %}
        <tr>
          <td>{{ lesson.order }}</td>
          <td>{{ lesson.title }}</td>
          <td>{{ lesson.duration or '-' }}</td>
          <td>{{ 'Yes' if lesson.is_free_preview else 'No' }}</td>
          <td><a href="{{ url_for('admin.edit_lesson', course_id=course.id, lesson_id=lesson.id) }}">Edit</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% endif %}
  </div>
  {% endif %}
</div>
{% endblock %}"""

files['app/templates/admin/lesson_form.html'] = """{% extends 'base.html' %}
{% block title %}{{ 'Edit' if lesson else 'New' }} Lesson - Admin{% endblock %}
{% block content %}
<div class="admin-page">
  <div class="admin-header">
    <h1>{{ 'Edit' if lesson else 'New' }} Lesson - {{ course.title }}</h1>
    <a href="{{ url_for('admin.edit_course', course_id=course.id) }}" class="btn-ghost">Back to Course</a>
  </div>
  <form method="POST" class="admin-form">
    <div class="form-group">
      <label>Lesson Title</label>
      <input type="text" name="title" required value="{{ lesson.title if lesson else '' }}">
    </div>
    <div class="form-group">
      <label>Video URL (Bunny.net embed or YouTube)</label>
      <input type="text" name="video_url" value="{{ lesson.video_url if lesson else '' }}">
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Duration (e.g. 12:30)</label>
        <input type="text" name="duration" value="{{ lesson.duration if lesson else '' }}">
      </div>
      <div class="form-group">
        <label>Order</label>
        <input type="number" name="order" value="{{ lesson.order if lesson else '1' }}">
      </div>
    </div>
    <div class="form-group">
      <label>Notes / Content (HTML ok)</label>
      <textarea name="content" rows="10">{{ lesson.content if lesson else '' }}</textarea>
    </div>
    <div class="form-checks">
      <label class="check-label"><input type="checkbox" name="is_free_preview" {% if lesson and lesson.is_free_preview %}checked{% endif %}> Free Preview</label>
    </div>
    <button type="submit" class="btn-primary">{{ 'Update' if lesson else 'Create' }} Lesson</button>
  </form>
</div>
{% endblock %}"""

files['app/static/js/main.js'] = """window.addEventListener('scroll', () => {
  const nav = document.getElementById('nav');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 50);
});
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(f => {
    f.style.transition = 'opacity 0.5s';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 500);
  });
}, 4000);"""

for path, content in files.items():
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

print("\nAll template files created!")
print("Now run: git add . && git commit -m 'Add templates and static files' && git push")
