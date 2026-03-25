import os

# Add webhook route to courses.py
webhook_code = '''
@courses.route('/webhook', methods=['POST'])
def webhook():
    import stripe
    from flask import current_app, request
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        return str(e), 400
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        course_id = int(session['metadata']['course_id'])
        user_id = int(session['metadata']['user_id'])
        from app.models import Enrollment
        from app import db
        existing = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if not existing:
            enrollment = Enrollment(
                user_id=user_id,
                course_id=course_id,
                stripe_payment_id=session['id']
            )
            db.session.add(enrollment)
            db.session.commit()
    return '', 200
'''

# Read current courses.py and append webhook
with open('app/routes/courses.py', 'r', encoding='utf-8') as f:
    content = f.read()

if '/webhook' not in content:
    with open('app/routes/courses.py', 'a', encoding='utf-8') as f:
        f.write(webhook_code)
    print("Webhook route added to courses.py!")
else:
    print("Webhook route already exists!")

print("Done! Now run: git add . && git commit -m 'Add Stripe webhook' && git push")
