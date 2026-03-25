import os

files = {}

# Add file manager route to admin.py
files['app/routes/admin.py'] = open('app/routes/admin.py', 'r', encoding='utf-8').read() + '''
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
    storage_api_key = os.getenv('BUNNY_API_KEY')
    storage_zone = os.getenv('BUNNY_STORAGE_ZONE', '3dartstuff-academy')
    ext = image.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    url = f'https://storage.bunnycdn.com/{storage_zone}/images/{filename}'
    headers = {'AccessKey': storage_api_key, 'Content-Type': 'application/octet-stream'}
    r = requests.put(url, headers=headers, data=image.read())
    if r.status_code in [200, 201]:
        cdn_url = f'https://{storage_zone}.b-cdn.net/images/{filename}'
        return jsonify({'success': True, 'url': cdn_url, 'filename': filename})
    return jsonify({'error': f'Upload failed: {r.status_code}'}), 500

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
'''

files['app/templates/admin/media.html'] = """{% extends 'base.html' %}
{% block title %}Media Library - Admin{% endblock %}
{% block content %}
<div class="admin-page">
  <div class="admin-header">
    <h1>Media Library</h1>
    <a href="{{ url_for('admin.dashboard') }}" class="btn-ghost">Back to Admin</a>
  </div>

  <!-- Image Upload -->
  <div class="media-section">
    <h2>Upload Image</h2>
    <div class="upload-box">
      <input type="file" id="image-file" accept="image/*">
      <button type="button" id="upload-image-btn" class="btn-primary">Upload Image</button>
      <span id="image-status" class="upload-status"></span>
    </div>
    <div id="image-result" class="url-result" style="display:none">
      <label>Image URL (click to copy):</label>
      <input type="text" id="image-url" readonly onclick="this.select();document.execCommand('copy');showCopied(this)">
    </div>
  </div>

  <!-- Video Upload -->
  <div class="media-section">
    <h2>Upload Video</h2>
    <p class="media-note">// For files over 200MB, upload directly via bunny.net dashboard for reliability</p>
    <div class="upload-box">
      <input type="file" id="video-file" accept="video/*">
      <input type="text" id="video-title" placeholder="Video title (optional)">
      <button type="button" id="upload-video-btn" class="btn-primary">Upload Video</button>
      <span id="video-status" class="upload-status"></span>
    </div>
    <div id="video-result" class="url-result" style="display:none">
      <label>Embed URL (click to copy):</label>
      <input type="text" id="video-url" readonly onclick="this.select();document.execCommand('copy');showCopied(this)">
    </div>
  </div>

  <!-- Video Library -->
  <div class="media-section">
    <h2>Video Library</h2>
    {% if videos %}
    <div class="media-grid">
      {% for video in videos %}
      <div class="media-card" id="video-{{ video.guid }}">
        <div class="media-thumb">
          {% if video.thumbnail %}
          <img src="{{ video.thumbnail }}" alt="{{ video.title }}" onerror="this.style.display='none'">
          {% else %}
          <div class="thumb-placeholder">{{ video.title[0] if video.title else 'V' }}</div>
          {% endif %}
          <div class="media-overlay">
            <span class="media-duration">{{ '%d:%02d'|format(video.length // 60, video.length % 60) if video.length else '?' }}</span>
          </div>
        </div>
        <div class="media-info">
          <div class="media-name">{{ video.title }}</div>
          <div class="media-status {% if video.status == 4 %}ready{% else %}processing{% endif %}">
            {{ 'Ready' if video.status == 4 else 'Processing...' }}
          </div>
          <div class="media-actions">
            <button class="btn-ghost-sm copy-embed"
              data-url="https://iframe.mediadelivery.net/embed/{{ library_id }}/{{ video.guid }}">
              Copy Embed
            </button>
            <button class="btn-ghost-sm copy-direct"
              data-url="https://player.mediadelivery.net/play/{{ library_id }}/{{ video.guid }}">
              Copy URL
            </button>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
      <p>No videos uploaded yet.</p>
    </div>
    {% endif %}
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
function showCopied(el) {
  const orig = el.style.borderColor;
  el.style.borderColor = '#4caf50';
  setTimeout(() => el.style.borderColor = orig, 1000);
}

// Copy embed/url buttons
document.querySelectorAll('.copy-embed, .copy-direct').forEach(btn => {
  btn.addEventListener('click', function() {
    navigator.clipboard.writeText(this.dataset.url);
    const orig = this.textContent;
    this.textContent = 'Copied!';
    this.style.color = '#4caf50';
    setTimeout(() => { this.textContent = orig; this.style.color = ''; }, 1500);
  });
});

// Image upload
document.getElementById('upload-image-btn').addEventListener('click', function() {
  const file = document.getElementById('image-file').files[0];
  if (!file) { alert('Select an image first'); return; }
  const status = document.getElementById('image-status');
  const btn = this;
  btn.textContent = 'Uploading...'; btn.disabled = true;
  status.textContent = 'Uploading...';
  const formData = new FormData();
  formData.append('image', file);
  fetch('/admin/upload-image', { method: 'POST', body: formData })
  .then(r => r.json()).then(data => {
    if (data.success) {
      document.getElementById('image-url').value = data.url;
      document.getElementById('image-result').style.display = 'block';
      status.textContent = 'Uploaded!';
      status.style.color = '#4caf50';
    } else {
      status.textContent = 'Failed: ' + (data.error || 'Unknown');
      status.style.color = '#ff5c3a';
    }
    btn.textContent = 'Upload Image'; btn.disabled = false;
  });
});

// Video upload
document.getElementById('upload-video-btn').addEventListener('click', function() {
  const file = document.getElementById('video-file').files[0];
  if (!file) { alert('Select a video first'); return; }
  const status = document.getElementById('video-status');
  const btn = this;
  const title = document.getElementById('video-title').value || file.name;
  btn.textContent = 'Uploading...'; btn.disabled = true;
  status.textContent = 'Uploading to Bunny.net...';
  const formData = new FormData();
  formData.append('video', file);
  formData.append('title', title);
  fetch('/admin/upload-video', { method: 'POST', body: formData })
  .then(r => r.json()).then(data => {
    if (data.success) {
      document.getElementById('video-url').value = data.embed_url;
      document.getElementById('video-result').style.display = 'block';
      status.textContent = 'Uploaded! Refresh page to see in library.';
      status.style.color = '#4caf50';
    } else {
      status.textContent = 'Failed: ' + (data.error || 'Unknown');
      status.style.color = '#ff5c3a';
    }
    btn.textContent = 'Upload Video'; btn.disabled = false;
  });
});
</script>
{% endblock %}"""

# Update base.html to add Media Library link in admin nav
base = open('app/templates/base.html', 'r', encoding='utf-8').read()
if 'media' not in base:
    base = base.replace(
        '{% if current_user.is_admin %}\n          <li><a href="{{ url_for(\'admin.dashboard\') }}" class="admin-link">Admin</a></li>',
        '{% if current_user.is_admin %}\n          <li><a href="{{ url_for(\'admin.dashboard\') }}" class="admin-link">Admin</a></li>\n          <li><a href="{{ url_for(\'admin.media\') }}" class="admin-link">Media</a></li>'
    )
    with open('app/templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base)
    print("base.html updated with Media link!")

# Add media CSS to main.css
media_css = """
/* MEDIA LIBRARY */
.media-section { margin-bottom: 4rem; }
.media-section h2 { font-family: var(--font-display); font-size: 2rem; color: var(--text); margin-bottom: 1.5rem; }
.media-note { font-family: var(--font-mono); font-size: 0.65rem; letter-spacing: 0.1em; color: var(--accent); margin-bottom: 1rem; }
.upload-box { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; padding: 2rem; background: var(--surface); border: 1px solid var(--border); margin-bottom: 1rem; }
.upload-box input[type="file"] { font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted); }
.upload-box input[type="text"] { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 0.6rem 1rem; font-family: var(--font-body); font-size: 0.85rem; min-width: 200px; }
.upload-status { font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); }
.url-result { padding: 1rem 1.5rem; background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--accent); }
.url-result label { font-family: var(--font-mono); font-size: 0.62rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-dim); display: block; margin-bottom: 0.5rem; }
.url-result input { width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--accent); padding: 0.7rem 1rem; font-family: var(--font-mono); font-size: 0.75rem; cursor: pointer; }
.media-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: var(--border); }
.media-card { background: var(--bg); transition: background 0.2s; }
.media-card:hover { background: var(--surface); }
.media-thumb { width: 100%; aspect-ratio: 16/9; background: var(--surface2); position: relative; overflow: hidden; }
.media-thumb img { width: 100%; height: 100%; object-fit: cover; }
.media-overlay { position: absolute; bottom: 0.5rem; right: 0.5rem; }
.media-duration { font-family: var(--font-mono); font-size: 0.6rem; background: rgba(0,0,0,0.8); color: var(--text); padding: 0.2rem 0.4rem; }
.media-info { padding: 1rem; }
.media-name { font-size: 0.82rem; color: var(--text); margin-bottom: 0.4rem; line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.media-status { font-family: var(--font-mono); font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.8rem; }
.media-status.ready { color: #4caf50; }
.media-status.processing { color: var(--accent); }
.media-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
@media (max-width: 900px) { .media-grid { grid-template-columns: repeat(2, 1fr); } .upload-box { flex-direction: column; align-items: flex-start; } }
"""

with open('app/static/css/main.css', 'a', encoding='utf-8') as f:
    f.write(media_css)
print("CSS updated!")

# Write all files
for path, content in files.items():
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated: {path}")

print("\nDone! Run: git add . && git commit -m 'Add media library and image upload' && git push")
