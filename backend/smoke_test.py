from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as c:
    h = c.get('/health')
    print('health', h.status_code, h.json())

    r = c.post('/api/auth/register', json={'username': 'alice', 'email': 'alice@x.com', 'password': 'secret1'})
    print('register', r.status_code, r.json().get('username'))

    r = c.post('/api/auth/login', json={'username': 'alice', 'password': 'secret1'})
    print('login', r.status_code, 'has_token', 'access_token' in r.json())
    tok = r.json()['access_token']

    r = c.get('/api/users/me', headers={'Authorization': f'Bearer {tok}'})
    print('me', r.status_code, r.json().get('username'), r.json().get('role'))

    r = c.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    print('admin_login', r.status_code, r.json().get('access_token', '')[:12])
    admin_tok = r.json().get('access_token', '')

    r = c.get('/api/users/me', headers={'Authorization': f'Bearer {admin_tok}'})
    print('admin_me', r.status_code, r.json().get('role'))
