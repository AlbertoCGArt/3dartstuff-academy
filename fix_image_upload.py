import os

with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """@admin.route('/upload-image', methods=['POST'])
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
    return jsonify({'error': f'Upload failed: {r.status_code}'}), 500"""

new = """@admin.route('/upload-image', methods=['POST'])
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
    return jsonify({'error': f'Upload failed: {r.status_code} - {r.text}'}), 500"""

if old in content:
    content = content.replace(old, new)
    with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed upload_image route!")
else:
    print("Route not found - may already be updated")

print("Done! Run: git add . && git commit -m 'Fix image upload with correct storage keys' && git push")
