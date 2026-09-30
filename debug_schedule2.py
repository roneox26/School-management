import sys
import traceback
sys.stdout.reconfigure(encoding='utf-8')

from main import app, get_from_db
from werkzeug.security import check_password_hash

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

with app.test_client() as c:
    # Login first
    admins = get_from_db('admin')
    print(f"Admin found: {admins[0].get('username') if admins else 'NONE'}")

    resp = c.post('/login', data={
        'username': admins[0].get('username'),
        'password': 'password123',
        'role': 'admin'
    }, follow_redirects=True)
    print(f"Login status: {resp.status_code}")
    print(f"Login response URL: {resp.request.path}")

    # Now hit class_schedule
    resp2 = c.get('/class_schedule', follow_redirects=True)
    print(f"Schedule status: {resp2.status_code}")
    body = resp2.data.decode('utf-8', errors='replace')

    if 'Error loading class schedule' in body:
        print("ERROR MESSAGE FOUND IN RESPONSE")
    else:
        print("Page loaded successfully")

    # Check for Python traceback clues in the page
    if 'Internal Server Error' in body or 'Traceback' in body:
        print("SERVER ERROR DETECTED")
        idx = body.find('Traceback')
        print(body[idx:idx+1000])
