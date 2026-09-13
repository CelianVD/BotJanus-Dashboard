import os
import io
import signal
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, g, request, session, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect

load_dotenv()

# ============================================================
# 1. CONFIGURATION
# ============================================================

SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'votre_cle_secrete_par_defaut')

SESSION_CONFIG = dict(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=True,  # Mettre à True si vous êtes en HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=60)
)

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.environ.get('GITHUB_REDIRECT_URI', 'votre_domaine/callback')
GITHUB_API_BASE_URL = "https://api.github.com"

RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')

DB_PATH = os.environ.get('DB_PATH', 'che')
BOTS_DIR = os.environ.get('BOTS_DIR', 'chemin/vers/vos/scripts')  # Répertoire des scripts .py

MANUAL_ADMIN_ID = "MANUAL_ADMIN"
MANUAL_ADMIN_USERNAME = "Administrateur"
MANUAL_LOGIN_ID = "identifiant_admin"
MANUAL_LOGIN_PASS = "mdp"

API_KEY = SECRET_KEY

ROLE_NONE = "None"
ROLE_COLLAB = "Collaborateur"
ROLE_ADMIN = "Admin"

TRANSLATIONS = {
    'fr': {
        'status_running': '🟢 EN COURS : ', 'status_stopped': '🔴 Arrêté', 'btn_stop': 'Arrêter BotJanus',
        'btn_start': 'DÉMARRER', 'script_running': 'Script en cours d\'exécution.', 'login_required': 'Connectez-vous pour lancer des scripts.',
        'locked_msg': '⛔ Lancement verrouillé par l\'administrateur.', 'console': 'Console', 'history': '📂 Historique',
        'my_account': '👤 Mon Compte', 'settings': '🛠 Paramètres', 'login_github': 'Connexion GitHub',
        'login_manual': 'Connexion Admin', 'logout': 'Se déconnecter', 'back': 'Retour', 'welcome': 'Bienvenue',
        'actions': 'Actions', 'banned': 'BANNI', 'ban': 'Bannir', 'unban': 'Débannir', 'update': 'Maj',
        'save': 'Enregistrer', 'users_roles': 'Utilisateurs & Rôles', 'system_settings': 'Paramètres Système',
        'security': 'Sécurité', 'lock_option': 'Verrouiller le lancement (admins seulement)', 'clean_logs': 'Nettoyer Logs',
        'login_title': 'Connexion Admin', 'username_ph': 'Identifiant', 'password_ph': 'Mot de passe',
        'connect_btn': 'Se connecter', 'lang_tag': 'Langue', 'role_tag': 'Rôle', 'days': 'jours',
        'error_auth': 'Erreur d\'authentification : Réservé à la connexion manuelle.', 'error_manual_login': 'Identifiants incorrects.',
        'contact': '✉️ Contact', 'messages': '📩 Messages'
    },
    'en': {
        'status_running': '🟢 RUNNING: ', 'status_stopped': '🔴 Stopped', 'btn_stop': 'Stop BotJanus',
        'btn_start': 'START', 'script_running': 'Script is currently running.', 'login_required': 'Please login to start scripts.',
        'locked_msg': '⛔ Launch locked by administrator.', 'console': 'Console', 'history': '📂 History',
        'my_account': '👤 My Account', 'settings': '🛠 Settings', 'login_github': 'GitHub Login',
        'login_manual': 'Admin Login', 'logout': 'Logout', 'back': 'Back', 'welcome': 'Welcome',
        'actions': 'Actions', 'banned': 'BANNED', 'ban': 'Ban', 'unban': 'Unban', 'update': 'Update',
        'save': 'Save', 'users_roles': 'Users & Roles', 'system_settings': 'System Settings', 'security': 'Security',
        'lock_option': 'Lock launching (Admins only)', 'clean_logs': 'Clean Logs', 'login_title': 'Admin Login',
        'username_ph': 'Username', 'password_ph': 'Password', 'connect_btn': 'Connect', 'lang_tag': 'Language',
        'role_tag': 'Role', 'days': 'days', 'error_auth': 'Auth Error: Manual login only.', 'error_manual_login': 'Incorrect credentials.',
        'contact': '✉️ Contact', 'messages': '📩 Messages'
    }
}


def get_text(key):
    lang = session.get('lang', 'fr')
    return TRANSLATIONS.get(lang, TRANSLATIONS['fr']).get(key, key)


def verify_recaptcha(response):
    payload = {'secret': RECAPTCHA_SECRET_KEY, 'response': response}
    try:
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        return r.json().get('success', False)
    except Exception:
        return False


# ============================================================
# 2. BASE DE DONNÉES
# ============================================================

def get_db():
    """Connexion SQLite liée au contexte de la requête courante."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db(app):
    """Crée les tables si elles n'existent pas encore. Appelé une fois au démarrage."""
    with app.app_context():
        try:
            db = get_db()
            db.execute('''CREATE TABLE IF NOT EXISTS logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT, script TEXT, message TEXT)''')
            db.execute('''CREATE TABLE IF NOT EXISTS settings (
                            key TEXT PRIMARY KEY, value TEXT)''')
            db.execute('''CREATE TABLE IF NOT EXISTS users (
                            github_id TEXT PRIMARY KEY, username TEXT, avatar TEXT,
                            role TEXT, is_banned INTEGER DEFAULT 0, lang TEXT DEFAULT 'fr',
                            ban_reason TEXT)''')
            db.execute('''CREATE TABLE IF NOT EXISTS script_config (
                            filename TEXT PRIMARY KEY, is_active INTEGER DEFAULT 1)''')
            db.execute('''CREATE TABLE IF NOT EXISTS schedules (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, script_name TEXT, frequency TEXT,
                            time_value INTEGER, last_run TEXT, next_run TEXT, is_enabled INTEGER DEFAULT 1)''')
            # Table du formulaire de contact
            db.execute('''CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            github_id TEXT, username TEXT, content TEXT,
                            date TEXT, is_read INTEGER DEFAULT 0)''')
            db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('lock_launch', '0')")
            db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('captcha_enabled', '0')")
            db.commit()
        except Exception as e:
            print(f"Erreur DB Init: {e}")


def log_to_db(script_name, message):
    """Insère une ligne de log (connexion indépendante, appelable depuis un thread)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO logs (date, script, message) VALUES (?, ?, ?)", (timestamp, script_name, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur DB Insert: {e}")


def get_unread_messages_count():
    """Nombre de messages de contact non lus, pour la pastille rouge de l'admin."""
    try:
        db = get_db()
        row = db.execute("SELECT COUNT(*) FROM messages WHERE is_read = 0").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0


def get_all_bots():
    """Liste les scripts .py disponibles dans BOTS_DIR (les crée si besoin)."""
    if not os.path.exists(BOTS_DIR):
        try:
            os.makedirs(BOTS_DIR)
        except Exception:
            pass
    defaults = [""]  # Remplacez par vos scripts par défaut
    for d in defaults:
        p = os.path.join(BOTS_DIR, d)
        if not os.path.exists(p):
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(f"# Script {d}\nprint('Initialisation du bot {d}...')\n")
            except Exception:
                pass
    return sorted([f for f in os.listdir(BOTS_DIR) if f.endswith('.py')])


def get_script_status(filename):
    try:
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute("SELECT is_active FROM script_config WHERE filename = ?", (filename,)).fetchone()
        conn.close()
        return res[0] if res is not None else 1
    except Exception:
        return 1


# ============================================================
# 3. DÉCORATEURS DE SÉCURITÉ
# ============================================================

def require_api_key(f):
    """Vérifie que la requête (bot Discord) porte la bonne clé secrète."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({"error": "Clé API invalide"}), 401
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter.")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


def check_role(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('dashboard.index'))
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE github_id = ?', (session['user_id'],)).fetchone()
            if not user or user['is_banned']:
                reason = user['ban_reason'] if user and user['ban_reason'] else "Non spécifiée"
                session.clear()
                flash(f"Compte banni. Raison : {reason}")
                return redirect(url_for('dashboard.index'))
            if user['role'] not in required_roles and 'All' not in required_roles:
                flash("Droits insuffisants.")
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================
# 4. MOTEUR DE LANCEMENT DES SCRIPTS + PLANIFICATEUR
# ============================================================
# NOTE: la suppression AUTOMATIQUE des vieux logs a été retirée volontairement.
# Le nettoyage des logs se fait désormais uniquement via le bouton
# "Supprimer tous les logs" dans les Paramètres (voir admin.delete_all_logs).

status = {
    "running": False, "process": None, "script_name": None,
    "live_output": [], "last_activity": None
}


def launch_script_core(script_name, path, args=None, user_name="SYSTEM"):
    if status["running"]:
        return False
    args = args or []
    cmd = ["python3", "-u", path] + args
    status["live_output"] = [f"--- Démarrage {script_name} par {user_name} ---"]
    if args:
        status["live_output"].append(f"Args: {' '.join(args)}")
    log_to_db("SYSTEM", f"Start {script_name} par {user_name}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=read_output, args=(process, script_name), daemon=True).start()
        status["running"], status["script_name"], status["process"], status["last_activity"] = True, script_name, process, datetime.now()
        return True
    except Exception as e:
        status["live_output"].append(f"Erreur de lancement : {str(e)}")
        return False


def read_output(process, script_name):
    for line in iter(process.stdout.readline, ''):
        cleaned = line.strip()
        if cleaned:
            status["last_activity"] = datetime.now()
            status["live_output"].append(cleaned)
            log_to_db(script_name, cleaned)
    process.stdout.close()
    status["running"] = False


def stop_current_script(user_name="SYSTEM"):
    if status["running"] and status["process"]:
        try:
            os.kill(status["process"].pid, signal.SIGTERM)
        except Exception:
            pass
        status["running"], status["script_name"], status["process"] = False, None, None
        log_to_db("SYSTEM", f"Arrêt par {user_name}")


def scheduler_loop():
    """Boucle de fond : lance les scripts planifiés dont l'heure est passée."""
    while True:
        try:
            time.sleep(30)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            schedules = conn.execute("SELECT * FROM schedules WHERE is_enabled = 1").fetchall()
            for sched in schedules:
                next_run = sched['next_run']
                if next_run and next_run <= now_str and not status["running"]:
                    script_name = sched['script_name']
                    script_path = os.path.join(BOTS_DIR, script_name)
                    if os.path.exists(script_path):
                        launch_script_core(script_name, script_path, args=[], user_name="Planificateur Auto")
                        freq = sched['frequency']
                        val = int(sched['time_value'] or 60)
                        last_run_time = datetime.now()
                        if freq == 'minutes':
                            next_run_time = last_run_time + timedelta(minutes=val)
                        elif freq == 'hours':
                            next_run_time = last_run_time + timedelta(hours=val)
                        elif freq == 'days':
                            next_run_time = last_run_time + timedelta(days=val)
                        else:
                            next_run_time = last_run_time + timedelta(days=1)
                        next_run_str = next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                        conn.execute("UPDATE schedules SET last_run = ?, next_run = ? WHERE id = ?",
                                     (now_str, next_run_str, sched['id']))
                        conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erreur du boucle du planificateur : {e}")


def start_scheduler_thread():
    threading.Thread(target=scheduler_loop, daemon=True).start()


# ============================================================
# 5. FABRIQUE DE L'APPLICATION FLASK
# ============================================================

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config.update(SESSION_CONFIG)
    csrf.init_app(app)

    # Import différé pour éviter les imports circulaires (les blueprints importent app.py)
    from routes_user import auth_bp, dashboard_bp, api_bp
    from routes_admin import admin_bp
    from routes_contact import contact_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(contact_bp)

    app.teardown_appcontext(close_connection)

    EXEMPT_ENDPOINTS = {'auth.security_gate', 'auth.verify_gate', 'static', 'auth.callback', 'auth.login_github'}

    @app.before_request
    def check_security_gate():
        if request.endpoint in EXEMPT_ENDPOINTS or not request.endpoint:
            return
        db = sqlite3.connect(DB_PATH)
        res = db.execute("SELECT value FROM settings WHERE key='captcha_enabled'").fetchone()
        db.close()
        captcha_on = (res[0] == '1') if res else False
        if captcha_on and not session.get('captcha_passed'):
            return redirect(url_for('auth.security_gate'))

    @app.context_processor
    def inject_globals():
        unread_messages = 0
        if session.get('user_id'):
            try:
                db = get_db()
                user = db.execute("SELECT role FROM users WHERE github_id=?", (session['user_id'],)).fetchone()
                if user and user['role'] == ROLE_ADMIN:
                    unread_messages = get_unread_messages_count()
            except Exception:
                unread_messages = 0
        return dict(t=get_text, current_lang=session.get('lang', 'fr'), unread_messages=unread_messages)

    return app


app = create_app()
init_db(app)
start_scheduler_thread()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
