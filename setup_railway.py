import os

files = {}

files['Dockerfile'] = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD gunicorn run:app --bind 0.0.0.0:8080 --workers 2
"""

files['Procfile'] = """web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 2
"""

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

# Add gunicorn to requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    reqs = f.read()
if 'gunicorn' not in reqs:
    with open('requirements.txt', 'a', encoding='utf-8') as f:
        f.write('\ngunicorn\n')
    print("Added gunicorn to requirements.txt")

print("\nDone! Now run: git add . && git commit -m 'Add Dockerfile for Railway' && git push")
