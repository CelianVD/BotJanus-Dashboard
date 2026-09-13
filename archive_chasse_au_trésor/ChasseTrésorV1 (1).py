import sqlite3
import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, g
from functools import wraps

app = Flask(__name__)
# CHANGEZ CETTE CLÉ POUR UNE VRAIE SÉCURITÉ
app.secret_key = 'zrépzifezpfbeaphbcpdzibsifbeosqoufbedisbcezàpsnfàipfbzàipqsbfbipzebfzepisbczibcpisbqqipczdbidpcbq'

# --- CONFIGURATION SPECIFIQUE PYTHONANYWHERE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "enigmes.db")
# -----------------------------------------------

ADMIN_USER = "janus"
ADMIN_PASS = "adm"

# --- NOUVELLE FONCTION UTILITAIRE POUR LA VÉRIFICATION DES RÉPONSES ---
def normalize_answer(answer_str):
    """Nettoie une chaîne de caractères pour la comparaison (minuscule et sans espace)"""
    if answer_str is None:
        return ""
    # On met en minuscule et on retire les espaces au début et à la fin
    return answer_str.strip().lower()

# --- Gestion Base de Données ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS riddles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_index INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                answer TEXT NOT NULL,
                btn_label TEXT DEFAULT 'Valider'
            )
        ''')
        db.commit()

# --- Décorateur Admin ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- HTML HEADER & FOOTER ---

HTML_HEAD = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>La Chasse au Trésor</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --bg-color: #1a1c2c; --accent-color: #c5a47e; --card-bg: #fdfaf6; --text-dark: #2c3e50; }
        body { background-color: var(--bg-color); background-image: radial-gradient(circle at center, #2a2d42 0%, #1a1c2c 100%); color: #e0e0e0; font-family: 'Lato', sans-serif; display: flex; flex-direction: column; min-height: 100vh; }
        h1, h2, h3, h4, .brand-font { font-family: 'Cinzel', serif; color: var(--accent-color); }
        .navbar { background: transparent !important; border-bottom: 1px solid rgba(197, 164, 126, 0.2); padding: 20px; }
        .navbar .btn-outline-accent { color: var(--accent-color); border-color: var(--accent-color); }
        .navbar .btn-outline-accent:hover { background-color: var(--accent-color); color: var(--bg-color); }
        .main-container { flex: 1; display: flex; justify-content: center; align-items: center; padding: 20px; flex-direction: column; }
        .riddle-card, .admin-card { max-width: 700px; width: 100%; padding: 40px; background: var(--card-bg); color: var(--text-dark); border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border-top: 3px solid var(--accent-color); }
        .riddle-content { font-size: 1.2rem; line-height: 1.6; }
        .btn-accent { background-color: var(--accent-color); border: none; color: var(--bg-color); font-weight: bold; letter-spacing: 1px; }
        .btn-accent:hover { background-color: #b08d66; color: var(--bg-color); }
        .alert { border-radius: 0; border: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2); width: 100%; max-width: 600px; margin-bottom: 20px; }
        .admin-container { background: white; padding: 30px; border-radius: 8px; color: var(--text-dark); width: 100%; max-width: 900px; }
    </style>
</head>
<body>
    <nav class="navbar px-4 justify-content-between">
        <span class="brand-font fs-4">La Chasse au Trésor</span>
        <div>
            {% if not session.get('admin_logged_in') %}
                <a href="{{ url_for('login') }}" class="btn btn-outline-accent btn-sm opacity-50">Admin</a>
            {% else %}
                <span class="badge bg-accent me-2" style="background:var(--accent-color); color:var(--bg-color)">Mode Créateur</span>
                <a href="{{ url_for('admin_dashboard') }}" class="btn btn-accent btn-sm mx-1">Tableau de bord</a>
                <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm mx-1">Sortir</a>
            {% endif %}
        </div>
    </nav>
    <div class="main-container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} text-center">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
"""

HTML_FOOT = """
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# --- Routes Utilisateur (Jeu) ---

@app.route('/')
def index():
    if 'current_riddle_index' not in session:
        session['current_riddle_index'] = 0

    db = get_db()
    riddles = db.execute('SELECT * FROM riddles ORDER BY order_index ASC').fetchall()
    current_idx = session['current_riddle_index']

    # Fin du jeu ou Vide
    if not riddles or current_idx >= len(riddles):
        msg_titre = "Le vide..." if not riddles else "Épreuve Ultime Achevée"
        msg_corps = "Il n'y a aucune énigme à résoudre pour le moment." if not riddles else "Vous avez percé tous les secrets du dédale."

        content = f"""
        <div class="text-center" style="max-width: 600px;">
            <h1 class="display-4 mb-4">{msg_titre}</h1>
            <p class="lead mb-5">{msg_corps}</p>
            {"<a href='/reset' class='btn btn-outline-accent'>Recommencer le voyage</a>" if riddles else ""}
        </div>
        """
        return render_template_string(HTML_HEAD + content + HTML_FOOT)

    # Affichage énigme
    riddle = riddles[current_idx]
    content = """
    <div class="riddle-card text-center">
        <h2 class="mb-5 display-5">{{ r['title'] }}</h2>
        <div class="mb-5 riddle-content">{{ r['content'] | safe }}</div>
        <form method="POST" action="{{ url_for('check_answer') }}" class="mt-4">
            <div class="mb-4">
                <input type="text" name="answer" class="form-control form-control-lg text-center" placeholder="Inscrivez la réponse..." autocomplete="off" required style="font-family: 'Cinzel', serif; letter-spacing: 2px;">
            </div>
            <button type="submit" class="btn btn-accent w-100 btn-lg py-3">{{ r['btn_label'] }}</button>
        </form>
    </div>
    """
    return render_template_string(HTML_HEAD + content + HTML_FOOT, r=riddle)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    # Normalisation de l'entrée utilisateur
    user_input = normalize_answer(request.form.get('answer', ''))
    db = get_db()
    riddles = db.execute('SELECT * FROM riddles ORDER BY order_index ASC').fetchall()
    current_idx = session.get('current_riddle_index', 0)

    is_correct = False

    if current_idx < len(riddles):
        correct_answers_str = riddles[current_idx]['answer']

        # Séparation des réponses par la virgule (,) et normalisation de chaque option
        correct_answers_list = [
            normalize_answer(a) for a in correct_answers_str.split(',')
        ]

        # Vérification : si l'entrée utilisateur correspond à l'une des réponses normalisées
        if user_input in correct_answers_list:
            is_correct = True

        if is_correct:
            session['current_riddle_index'] += 1
            flash("La voie s'ouvre...", "success")
        else:
            flash("Ce n'est pas la bonne réponse... Réessayez !", "danger")
            return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    session['current_riddle_index'] = 0
    return redirect(url_for('index'))

# --- Routes Admin (Identiques mais la description du champ réponse est changée) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('id')
        pwd = request.form.get('mdp')
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Identité non reconnue.", "danger")

    content = """
    <div class="admin-card">
        <h3 class="text-center mb-4">Accès Créateur</h3>
        <form method="POST">
            <div class="mb-3"><label class="form-label fw-bold">Identifiant</label><input type="text" name="id" class="form-control"></div>
            <div class="mb-3"><label class="form-label fw-bold">Mot de passe</label><input type="password" name="mdp" class="form-control"></div>
            <button class="btn btn-accent w-100 mt-3">Entrer</button>
        </form>
    </div>
    """
    return render_template_string(HTML_HEAD + content + HTML_FOOT)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("Déconnexion effectuée.", "success")
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db()
    riddles = db.execute('SELECT * FROM riddles ORDER BY order_index ASC').fetchall()

    content = """
    <div class="container admin-container shadow-lg">
        <div class="d-flex justify-content-between align-items-center mb-5 pb-3 border-bottom">
            <h2 class="m-0">Configuration du Dédale</h2>
            <a href="{{ url_for('admin_edit') }}" class="btn btn-accent">+ Créer une Énigme</a>
        </div>
        <div class="table-responsive">
        <table class="table table-hover align-middle">
            <thead>
                <tr>
                    <th width="5%">#</th>
                    <th width="40%">Titre</th>
                    <th width="25%">Code (Réponse)</th>
                    <th width="30%" class="text-end">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for riddle in riddles %}
                <tr>
                    <td class="fw-bold">{{ loop.index }}</td>
                    <td><strong>{{ riddle['title'] }}</strong></td>
                    <td><code class="bg-light px-2 py-1 rounded text-dark border">{{ riddle['answer'] }}</code></td>
                    <td class="text-end">
                            <div class="btn-group" role="group">
                            <a href="{{ url_for('move_riddle', id=riddle['id'], direction='up') }}" class="btn btn-sm btn-outline-secondary">↑</a>
                            <a href="{{ url_for('move_riddle', id=riddle['id'], direction='down') }}" class="btn btn-sm btn-outline-secondary">↓</a>
                        </div>
                        <a href="{{ url_for('admin_edit', id=riddle['id']) }}" class="btn btn-sm btn-primary ms-2">Éditer</a>
                        <a href="{{ url_for('admin_delete', id=riddle['id']) }}" class="btn btn-sm btn-danger ms-1" onclick="return confirm('Supprimer ?')">X</a>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="4" class="text-center py-4 text-muted">Le dédale est vide.</td></tr>
                {% endfor %}
            </tbody>
        </table>
        </div>
        <div class="mt-4 text-center"><a href="{{ url_for('index') }}" class="btn btn-outline-dark">Retourner au jeu</a></div>
    </div>
    """
    return render_template_string(HTML_HEAD + content + HTML_FOOT, riddles=riddles)

@app.route('/admin/edit', methods=['GET', 'POST'])
@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit(id=None):
    db = get_db()
    riddle = None
    if id:
        riddle = db.execute('SELECT * FROM riddles WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        content_txt = request.form['content']
        # Assurez-vous que la réponse est propre avant l'enregistrement
        answer = request.form['answer'].strip()
        btn_label = request.form['btn_label']

        if id:
            db.execute('UPDATE riddles SET title=?, content=?, answer=?, btn_label=? WHERE id=?',
                       (title, content_txt, answer, btn_label, id))
        else:
            last = db.execute('SELECT MAX(order_index) as m FROM riddles').fetchone()
            new_order = (last['m'] + 1) if last['m'] is not None else 1
            db.execute('INSERT INTO riddles (order_index, title, content, answer, btn_label) VALUES (?, ?, ?, ?, ?)',
                       (new_order, title, content_txt, answer, btn_label))

        db.commit()
        return redirect(url_for('admin_dashboard'))

    content = """
    <div class="admin-card">
        <h3 class="mb-4" style="font-family:'Cinzel', serif;">{{ 'Modifier' if r else 'Forger' }} une épreuve</h3>
        <form method="POST">
            <div class="mb-3">
                <label class="form-label fw-bold">Titre de l'énigme</label>
                <input type="text" name="title" class="form-control" value="{{ r['title'] if r else '' }}" required>
            </div>
            <div class="mb-4">
                <label class="form-label fw-bold">Texte (HTML autorisé)</label>
                <textarea name="content" class="form-control" rows="5" required>{{ r['content'] if r else '' }}</textarea>
            </div>
            <div class="row mb-4">
                <div class="col-md-6">
                        <label class="form-label fw-bold text-primary">Code Réponse(s)</label>
                        <input type="text" name="answer" class="form-control border-primary" value="{{ r['answer'] if r else '' }}" required placeholder="Ex: clé, clef, le secret">
                        <div class="form-text text-muted">Séparez les réponses multiples par une **virgule** (ex: pomme,poire).</div>
                </div>
                <div class="col-md-6">
                    <label class="form-label fw-bold">Texte Bouton</label>
                    <input type="text" name="btn_label" class="form-control" value="{{ r['btn_label'] if r else 'Valider' }}">
                </div>
            </div>
            <hr>
            <div class="d-flex justify-content-between">
                    <a href="{{ url_for('admin_dashboard') }}" class="btn btn-outline-secondary px-4">Annuler</a>
                    <button class="btn btn-accent px-5 py-2">ENREGISTRER</button>
            </div>
        </form>
    </div>
    """
    return render_template_string(HTML_HEAD + content + HTML_FOOT, r=riddle)

@app.route('/admin/delete/<int:id>')
@login_required
def admin_delete(id):
    db = get_db()
    db.execute('DELETE FROM riddles WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/move/<int:id>/<direction>')
@login_required
def move_riddle(id, direction):
    db = get_db()
    current = db.execute('SELECT * FROM riddles WHERE id = ?', (id,)).fetchone()
    if current:
        current_order = current['order_index']
        if direction == 'up':
            neighbor = db.execute('SELECT * FROM riddles WHERE order_index < ? ORDER BY order_index DESC LIMIT 1', (current_order,)).fetchone()
        else:
            neighbor = db.execute('SELECT * FROM riddles WHERE order_index > ? ORDER BY order_index ASC LIMIT 1', (current_order,)).fetchone()

        if neighbor:
            neighbor_order = neighbor['order_index']
            db.execute('UPDATE riddles SET order_index = ? WHERE id = ?', (neighbor_order, id))
            db.execute('UPDATE riddles SET order_index = ? WHERE id = ?', (current_order, neighbor['id']))
            db.commit()
    return redirect(url_for('admin_dashboard'))

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)