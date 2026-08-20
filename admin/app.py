#!/usr/bin/env python3
"""
🛠️ Hermes Admin Panel v2 — полноценная админка с авторизацией и 2FA
Запуск: PYTHONPATH="" venv/bin/python app.py
Порт: 3030
"""
import hashlib, hmac, json, os, sqlite3, subprocess, sys, time, base64
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import parse_qs, urlencode

from flask import (
    Flask, render_template, request, redirect, session, 
    jsonify, flash, url_for, abort
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user, 
    login_required, current_user
)
from werkzeug.middleware.proxy_fix import ProxyFix

# === Configuration ===
SECRET_KEY = os.urandom(32).hex()
ADMIN_DB = Path(__file__).parent / 'data' / 'admin.db'
DEV = Path('/Volumes/External/dev')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # CHANGE ME

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)

# Fix proxy headers (Caddy reverse proxy)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# === Database ===
def init_db():
    ADMIN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ADMIN_DB))
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        totp_secret TEXT,
        totp_enabled INTEGER DEFAULT 0,
        role TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        ip TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Create default admin if not exists
    existing = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not existing:
        pw_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                    ('admin', pw_hash, 'superadmin'))
    # Default settings
    default_settings = {
        'bitget_pair': 'ETH/USDT',
        'bitget_leverage': '2',
        'bitget_order_size': '9.5',
        'bitget_tp': '2.0',
        'bitget_stop': '5.0',
        'hh_remote_area': '113',
        'hh_jobs_area': '97',
        'hh_min_score': '0.7',
        'telegram_chat': '-1004297012607',
        'telegram_thread': '116',
    }
    for k, v in default_settings.items():
        conn.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))
    conn.commit()
    conn.close()

# === User Model ===
class User(UserMixin):
    def __init__(self, id, username, role='admin', totp_enabled=False):
        self.id = id
        self.username = username
        self.role = role
        self.totp_enabled = bool(totp_enabled)

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(str(ADMIN_DB))
    u = conn.execute('SELECT id, username, role, totp_enabled FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if u:
        return User(u[0], u[1], u[2], u[3])
    return None

# === Audit ===
def log_action(action, details=''):
    try:
        conn = sqlite3.connect(str(ADMIN_DB))
        conn.execute('INSERT INTO audit_log (user_id, action, details, ip) VALUES (?, ?, ?, ?)',
                    (current_user.id if current_user.is_authenticated else 0,
                     action, details, request.remote_addr))
        conn.commit()
        conn.close()
    except:
        pass

# === Routes ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect(str(ADMIN_DB))
        u = conn.execute('SELECT id, username, password_hash, role, totp_enabled, totp_secret FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if u and u[2] == pw_hash:
            user = User(u[0], u[1], u[3], u[4])
            if u[4]:  # 2FA enabled
                session['pending_user'] = u[0]
                session['pending_totp'] = True
                return redirect(url_for('verify_2fa'))
            login_user(user, remember=True)
            log_action('login', f'User {username} logged in')
            return redirect(url_for('index'))
        
        flash('Invalid credentials', 'error')
    return render_template('login.html', year=datetime.now().year)

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'pending_user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        code = request.form.get('code', '')
        conn = sqlite3.connect(str(ADMIN_DB))
        u = conn.execute('SELECT id, username, role, totp_enabled, totp_secret FROM users WHERE id = ?', (session['pending_user'],)).fetchone()
        conn.close()
        
        if u and u[4]:
            import pyotp
            totp = pyotp.TOTP(u[4])
            if totp.verify(code, valid_window=1):
                user = User(u[0], u[1], u[2], u[3])
                login_user(user, remember=True)
                del session['pending_user']
                del session['pending_totp']
                log_action('login_2fa', f'User {u[1]} verified 2FA')
                return redirect(url_for('index'))
        
        flash('Invalid 2FA code', 'error')
    return render_template('verify_2fa.html', year=datetime.now().year)

@app.route('/logout')
@login_required
def logout():
    log_action('logout', f'User {current_user.username} logged out')
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/admin')
@app.route('/admin/')
@login_required
def index():
    return render_template('index.html', year=datetime.now().year)

@app.route('/api/status')
@login_required
def api_status():
    """Get comprehensive system status"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'pm2': {},
        'bitget': {},
        'hh_jobs': {},
        'servers': {},
        'system': {},
    }
    
    # PM2
    try:
        r = subprocess.run(['pm2', 'list'], capture_output=True, text=True, timeout=10)
        for line in r.stdout.split('\n'):
            if '│' in line:
                parts = [p.strip() for p in line.split('│') if p.strip()]
                if len(parts) >= 5:
                    status['pm2'][parts[1]] = {
                        'status': parts[4],
                        'uptime': parts[3],
                        'cpu': parts[6],
                        'mem': parts[7],
                    }
    except:
        pass
    
    # Bitget state
    state_file = DEV / 'bitget-bot' / 'config' / 'state_dca.json'
    if state_file.exists():
        try:
            status['bitget'] = json.loads(state_file.read_text())
        except:
            pass
    
    # HH Jobs
    hh_db = DEV / 'my-project' / 'hh-jobs' / 'data' / 'hh.db'
    if hh_db.exists():
        try:
            conn = sqlite3.connect(str(hh_db))
            c = conn.execute('SELECT COUNT(*) FROM vacancies').fetchone()
            m = conn.execute('SELECT COUNT(*) FROM vacancies WHERE matched_score > 0').fetchone()
            status['hh_jobs'] = {'total': c[0], 'matched': m[0]}
            conn.close()
        except:
            pass
    
    # System
    status['system'] = {
        'time': datetime.now().strftime('%H:%M:%S'),
        'date': datetime.now().strftime('%Y-%m-%d'),
    }
    
    log_action('api_status', 'Status check')
    return jsonify(status)

@app.route('/api/services/<name>/<action>', methods=['POST'])
@login_required
def service_action(name, action):
    """Start/stop/restart PM2 services"""
    valid_actions = ['start', 'stop', 'restart']
    if action not in valid_actions:
        return jsonify({'error': 'Invalid action'}), 400
    
    try:
        subprocess.run(['pm2', action, name], capture_output=True, text=True, timeout=30)
        log_action('service_action', f'{action} {name}')
        return jsonify({'success': True, 'action': action, 'service': name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        conn = sqlite3.connect(str(ADMIN_DB))
        rows = conn.execute('SELECT key, value FROM settings').fetchall()
        conn.close()
        return jsonify(dict(rows))
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    conn = sqlite3.connect(str(ADMIN_DB))
    for key, value in data.items():
        conn.execute('INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
                    (key, str(value)))
    conn.commit()
    conn.close()
    log_action('settings_update', f'Updated {len(data)} settings')
    return jsonify({'success': True})

@app.route('/api/audit')
@login_required
def audit_log():
    conn = sqlite3.connect(str(ADMIN_DB))
    rows = conn.execute('SELECT a.id, u.username, a.action, a.details, a.ip, a.created_at FROM audit_log a LEFT JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([{'id': r[0], 'user': r[1], 'action': r[2], 'details': r[3], 'ip': r[4], 'time': r[5]} for r in rows])

@app.route('/setup-2fa')
@login_required
def setup_2fa():
    import pyotp
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(current_user.username, issuer_name='Hermes Admin')
    
    # Store secret temporarily
    session['new_totp_secret'] = secret
    
    return render_template('setup_2fa.html', 
                         secret=secret, 
                         uri=provisioning_uri,
                         year=datetime.now().year)

@app.route('/confirm-2fa', methods=['POST'])
@login_required
def confirm_2fa():
    import pyotp
    code = request.form.get('code', '')
    secret = session.get('new_totp_secret', '')
    
    if not secret:
        flash('2FA setup expired', 'error')
        return redirect(url_for('setup_2fa'))
    
    totp = pyotp.TOTP(secret)
    if totp.verify(code, valid_window=1):
        conn = sqlite3.connect(str(ADMIN_DB))
        conn.execute('UPDATE users SET totp_secret = ?, totp_enabled = 1 WHERE id = ?',
                    (secret, current_user.id))
        conn.commit()
        conn.close()
        del session['new_totp_secret']
        log_action('enable_2fa', '2FA enabled')
        flash('2FA enabled successfully!', 'success')
        return redirect(url_for('index'))
    
    flash('Invalid code', 'error')
    return redirect(url_for('setup_2fa'))

# === Templates ===
@app.template_filter('datetime')
def datetime_filter(value, fmt='%Y-%m-%d %H:%M'):
    if value:
        return datetime.fromisoformat(value).strftime(fmt) if isinstance(value, str) else value
    return ''

# === Main ===
if __name__ == '__main__':
    init_db()
    print(f"✅ Hermes Admin Panel v2")
    print(f"   URL: http://0.0.0.0:3030")
    print(f"   Login: admin / {ADMIN_PASSWORD}")
    print(f"   2FA: Enable in settings")
    app.run(host='0.0.0.0', port=3030, debug=False)