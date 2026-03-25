import os

# Add bunny upload route to admin.py
bunny_route = '''
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
'''

# Read admin.py and add import + route
with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add jsonify import if not there
if 'jsonify' not in content:
    content = content.replace(
        'from flask import Blueprint, render_template, redirect, url_for, flash, request',
        'from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify'
    )

# Add requests import if not there
if 'import requests' not in content:
    content = content.replace(
        'import re\n',
        'import re\nimport requests\n'
    )

if 'upload-video' not in content:
    content += bunny_route

with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Admin upload route added!")

# Add requests to requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    reqs = f.read()
if 'requests' not in reqs:
    with open('requirements.txt', 'a', encoding='utf-8') as f:
        f.write('requests\n')
    print("Added requests to requirements.txt")

# Update lesson form to include video upload
lesson_form_update = """{% extends 'base.html' %}
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
      <label>Video URL (paste Bunny.net embed URL or upload below)</label>
      <input type="text" name="video_url" id="video_url" value="{{ lesson.video_url if lesson else '' }}" placeholder="https://iframe.mediadelivery.net/embed/...">
    </div>
    <div class="form-group">
      <label>Upload Video to Bunny.net</label>
      <div class="upload-area">
        <input type="file" id="video_file" accept="video/*">
        <button type="button" id="upload-btn" class="btn-ghost">Upload Video</button>
        <span id="upload-status" style="font-family:var(--font-mono);font-size:0.7rem;color:var(--text-muted);margin-left:1rem;"></span>
      </div>
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
{% endblock %}
{% block scripts %}
<script>
document.getElementById('upload-btn').addEventListener('click', function() {
  const file = document.getElementById('video_file').files[0];
  if (!file) { alert('Please select a video file first'); return; }
  const status = document.getElementById('upload-status');
  const btn = this;
  btn.textContent = 'Uploading...';
  btn.disabled = true;
  status.textContent = 'Uploading to Bunny.net...';
  const formData = new FormData();
  formData.append('video', file);
  formData.append('title', file.name);
  fetch('/admin/upload-video', { method: 'POST', body: formData })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      document.getElementById('video_url').value = data.embed_url;
      status.textContent = 'Uploaded! Embed URL filled in automatically.';
      status.style.color = '#4caf50';
      btn.textContent = 'Upload Another';
      btn.disabled = false;
    } else {
      status.textContent = 'Upload failed: ' + (data.error || 'Unknown error');
      status.style.color = '#ff5c3a';
      btn.textContent = 'Upload Video';
      btn.disabled = false;
    }
  });
});
</script>
{% endblock %}"""

with open('app/templates/admin/lesson_form.html', 'w', encoding='utf-8') as f:
    f.write(lesson_form_update)
print("Lesson form updated with video upload!")

print("\nDone! Now run: git add . && git commit -m 'Add Bunny.net video upload' && git push")
