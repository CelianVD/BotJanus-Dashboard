GLASS_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    * { box-sizing: border-box; }

    :root {
        --bg-gradient: linear-gradient(120deg, #0093E9 0%, #80D0C7 100%);
        --panel-bg: rgba(255, 255, 255, 0.15);
        --panel-border: rgba(255, 255, 255, 0.18);
        --panel-shadow: rgba(31, 38, 135, 0.20);
        --text-color: #fff;
        --input-bg: rgba(255, 255, 255, 0.1);
        --input-border: rgba(255, 255, 255, 0.3);
        --th-bg: rgba(0,0,0,0.2);
        --console-bg: rgba(0, 0, 0, 0.6);
        --console-border: rgba(255,255,255,0.1);
    }

    /* Configuration Mode Sombre Spécifique (Bleu Nuit & Noir Profond) */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-gradient: linear-gradient(135deg, #02040a 0%, #0b132b 50%, #000000 100%);
            --panel-bg: rgba(11, 19, 43, 0.55);
            --panel-border: rgba(255, 255, 255, 0.08);
            --panel-shadow: rgba(0, 0, 0, 0.6);
            --text-color: #f0f4f8;
            --input-bg: rgba(2, 4, 8, 0.7);
            --input-border: rgba(255, 255, 255, 0.15);
            --th-bg: rgba(5, 10, 20, 0.7);
            --console-bg: rgba(2, 4, 8, 0.95);
            --console-border: rgba(0, 180, 216, 0.3);
        }
    }

    body { font-family: 'Poppins', sans-serif; margin: 0; padding: 0; min-height: 100vh; background: var(--bg-gradient); background-size: 200% 200%; animation: gradientBG 15s ease infinite; color: var(--text-color); }
    @keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .container { width: 95%; max-width: 900px; margin: 20px auto; padding-bottom: 80px; }
    .glass-panel { background: var(--panel-bg); box-shadow: 0 8px 32px 0 var(--panel-shadow); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-radius: 16px; border: 1px solid var(--panel-border); padding: 25px; margin-bottom: 20px; text-align: center; }
    h1, h2, h3 { margin-top: 0; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .flex-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
    .flex-center { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
    .btn { padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: 50px; cursor: pointer; border: none; transition: 0.3s; text-decoration: none; display: inline-flex; justify-content: center; align-items: center; margin: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); white-space: nowrap; color: white; position: relative; }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }
    .btn-github { background: #5865F2; } .btn-manual { background: #333; border: 1px solid #555; } .btn-action { background: linear-gradient(45deg, #11998e, #38ef7d); } .btn-danger { background: linear-gradient(45deg, #ff416c, #ff4b2b); } .btn-nav { background: rgba(255,255,255,0.3); border: 1px solid rgba(255,255,255,0.4); }
    input, select, textarea { padding: 10px; border-radius: 8px; border: 1px solid var(--input-border); background: var(--input-bg); color: var(--text-color); outline: none; }
    option { background: #111; color: white; }
    .table-responsive { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; min-width: 600px; }
    th, td { padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
    th { background: var(--th-bg); }
    .console-window { background: var(--console-bg); border-radius: 12px; padding: 15px; height: 350px; overflow-y: scroll; text-align: left; font-family: 'Courier New', monospace; font-size: 13px; color: #0f0; border: 1px solid var(--console-border); }
    .alert { background: rgba(255, 200, 0, 0.3); padding: 10px; border-radius: 8px; margin-bottom: 15px; border: 1px solid orange; color: white; }
    .user-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
    .role-Admin { background: #ff416c; } .role-Collaborateur { background: #38ef7d; color: #000; } .role-None { background: #ccc; color: #333; }
    .admin-nav-bar { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; }

    /* --- Pastille de notification (messages non lus) --- */
    .badge-dot {
        position: absolute; top: -4px; right: -4px;
        width: 18px; height: 18px; border-radius: 50%;
        background: #ff2d55; color: #fff; font-size: 0.7em; font-weight: bold;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 0 2px rgba(0,0,0,0.3);
    }
</style>
"""
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BotJanus</title>
  {{ glass_css|safe }}
  <style>
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
    .modal-content { background: rgba(25, 35, 50, 0.95); padding: 30px; border-radius: 16px; width: 90%; max-width: 400px; border: 1px solid rgba(255,255,255,0.2); text-align: left; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-size: 0.9em; color: #ccc; }
    .form-group input, .form-group select { width: 100%; }
  </style>
</head>
<body>
  <div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}<div class="alert">{% for message in messages %}{{ message }}<br>{% endfor %}</div>{% endif %}
    {% endwith %}

    <div class="glass-panel flex-row">
        <div><h1>BotJanus</h1></div>
        <div>
            {% if session.get('user_id') %}
                <a href="{{ url_for('contact.contact_form') }}" class="btn btn-nav">{{ t('contact') }}</a>
                <a href="{{ url_for('auth.account') }}" class="btn btn-nav">
                    {{ t('my_account') }}
                    {% if role == 'Admin' and unread_messages and unread_messages > 0 %}
                        <span class="badge-dot">{{ unread_messages }}</span>
                    {% endif %}
                </a>
                {% if role == 'Admin' %}
                   <a href="{{ url_for('admin.admin_users') }}" class="btn btn-danger">{{ t('settings') }}</a>
                {% endif %}
            {% else %}
                <a href="{{ url_for('auth.login_wiki') }}" class="btn btn-github">{{ t('login_wiki') }}</a>
                <a href="{{ url_for('auth.manual_login_page') }}" class="btn btn-manual">{{ t('login_manual') }}</a>
            {% endif %}
        </div>
    </div>

    <div class="glass-panel">
        <div style="margin-bottom: 10px;">Statut : <span style="font-weight:bold; color: {{ 'lightgreen' if running else 'salmon' }};">{{ t('status_running') + script_name if running else t('status_stopped') }}</span></div>
        {% if running %}
            {% if role in ['Collaborateur', 'Admin'] %}
                <form action="{{ url_for('dashboard.stop_script') }}" method="post">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <button class="btn btn-danger" type="submit">{{ t('btn_stop') }}</button>
                </form>
            {% else %}
                <p><em>{{ t('script_running') }}</em></p>
            {% endif %}
        {% else %}
            {% if session.get('user_id') %}
                {# Tout utilisateur connecté VOIT l'interface de lancement (y compris rôle None).
                   Seuls Collaborateur/Admin peuvent réellement lancer : pour un None, la
                   vérification autopatrol multi-wikis est faite côté serveur au clic sur
                   DÉMARRER (dashboard.start_script) ; si elle réussit, il est promu
                   Collaborateur en base et le script part. Sinon : message via flash(). #}
                {% if locked == '1' and role != 'Admin' %}
                    <div style="background: rgba(255,0,0,0.2); padding: 15px; border-radius: 10px;">{{ t('locked_msg') }}</div>
                {% else %}
                    <form id="startForm" action="{{ url_for('dashboard.start_script') }}" method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <input type="hidden" name="arg_lang" id="hidden_lang">
                        <input type="hidden" name="arg_cat" id="hidden_cat">
                        <input type="hidden" name="arg_portal" id="hidden_portal">

                        <select id="scriptSelect" name="choice" style="min-width: 200px; margin-bottom: 10px;">
                            <optgroup label="Scripts Disponibles">
                                {% for s in available_scripts %}
                                    <option value="{{ s.filename }}">{{ s.filename }}{% if role == 'Admin' and s.is_active == 0 %} (Verrouillé aux Users){% endif %}</option>
                                {% endfor %}
                            </optgroup>
                        </select>
                        <button class="btn btn-action" type="button" onclick="handleStart()">{{ t('btn_start') }}</button>
                    </form>
                    {% if role not in ['Collaborateur', 'Admin'] %}
                        <p style="font-size:0.85em; opacity:0.8; margin-top:10px;">ℹ️ {{ t('launch_hint') }}</p>
                    {% endif %}
                {% endif %}
            {% else %}
                <p><em>{{ t('login_required') }}</em></p>
            {% endif %}
        {% endif %}
    </div>

    <div class="glass-panel" style="text-align: left;">
        <div class="flex-row">
            <h3 style="margin:0;">{{ t('console') }}</h3>
            <a href="{{ url_for('dashboard.history') }}" class="btn btn-nav">{{ t('history') }}</a>
        </div>
        <div class="console-window" id="logBox">
            {% for line in logs %}<div>{{ line }}</div>{% endfor %}
        </div>
    </div>
  </div>

  <div id="portalModal" class="modal-overlay">
      <div class="modal-content">
          <h3>⚙️ Configuration Portal Bot</h3>
          <div class="form-group">
              <label>Langue Vikidia</label>
              <select id="modal_lang">
                  <option value="fr">Français (fr)</option>
                  <option value="en">English (en)</option>
              </select>
          </div>
          <div class="form-group">
              <label>Nom de la Catégorie</label>
              <input type="text" id="modal_cat" placeholder="Ex: Histoire de France">
          </div>
          <div class="form-group">
              <label>Nom du Portail à ajouter</label>
              <input type="text" id="modal_portal" placeholder="Ex: France">
          </div>
          <div style="text-align:right; margin-top:20px;">
              <button class="btn btn-nav" onclick="closeModal()">Annuler</button>
              <button class="btn btn-action" onclick="confirmPortalLaunch()">Lancer</button>
          </div>
      </div>
  </div>

  <script>
    var logBox = document.getElementById("logBox");
    if(logBox) {
        logBox.scrollTop = logBox.scrollHeight;
        setInterval(function(){
            fetch("/api/live_logs").then(r => r.text()).then(data => {
                let isScrolled = logBox.scrollHeight - logBox.clientHeight <= logBox.scrollTop + 50;
                logBox.innerHTML = data;
                if(isScrolled) logBox.scrollTop = logBox.scrollHeight;
            });
        }, 2000);
    }

    // SYSTEM DE NOTIFICATION PUSH CE CÔTÉ CLIENT
    if (window.Notification && Notification.permission === "default") {
        Notification.requestPermission();
    }

    let wasRunning = {{ 'true' if running else 'false' }};
    let activeScriptName = "{{ script_name }}";

    setInterval(function(){
        fetch("/api/status_json").then(r => r.json()).then(res => {
            if (wasRunning && !res.running) {
                if (window.Notification && Notification.permission === "granted") {
                    new Notification("🤖 BotJanus - Script Terminé", {
                        body: "Le traitement du script '" + activeScriptName + "' s'est achevé.",
                        icon: "https://ui-avatars.com/api/?name=Bot+Janus&background=0093E9&color=fff"
                    });
                }
            }
            wasRunning = res.running;
            activeScriptName = res.script_name;
        });
    }, 3000);

    function handleStart() {
        var choice = document.getElementById('scriptSelect').value;
        if (choice.includes('portal.py') || choice === 'Portail') {
            document.getElementById('portalModal').style.display = 'flex';
        } else {
            document.getElementById('startForm').submit();
        }
    }
    function closeModal() { document.getElementById('portalModal').style.display = 'none'; }
    function confirmPortalLaunch() {
        document.getElementById('hidden_lang').value = document.getElementById('modal_lang').value;
        document.getElementById('hidden_cat').value = document.getElementById('modal_cat').value;
        document.getElementById('hidden_portal').value = document.getElementById('modal_portal').value;
        document.getElementById('startForm').submit();
        closeModal();
    }
  </script>
</body>
</html>
"""
GATE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sécurité - BotJanus</title>
  <script src="https://www.google.com/recaptcha/api.js" async defer></script>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container" style="max-width:450px; padding-top:100px;">
    <div class="glass-panel">
        <h2>🛡️ Portail de Sécurité</h2>
        <form action="{{ url_for('auth.verify_gate') }}" method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <div class="g-recaptcha" data-sitekey="{{ site_key }}" style="display: inline-block; margin-bottom: 20px;"></div>
            <button type="submit" class="btn btn-action" style="width:100%;">Entrer sur le site</button>
        </form>
    </div>
  </div>
</body>
</html>
"""

LOGIN_MANUAL_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ t('login_title') }}</title>
  {{ glass_css|safe }}
</head>
<body>
<div class="container" style="max-width:400px; padding-top:100px;">
    <div class="glass-panel">
        <h2>{{ t('login_title') }}</h2>
        <form action="{{ url_for('auth.manual_login_post') }}" method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="text" name="username" placeholder="{{ t('username_ph') }}" style="width:100%; margin-bottom:10px;"><br>
            <input type="password" name="password" placeholder="{{ t('password_ph') }}" style="width:100%; margin-bottom:10px;"><br>
            <button class="btn btn-action" type="submit" style="width:100%;">{{ t('connect_btn') }}</button>
        </form>
        <br><a href="{{ url_for('dashboard.index') }}" class="btn btn-nav" style="width:100%;">{{ t('back') }}</a>
    </div>
</div>
</body>
</html>
"""

ACCOUNT_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ t('my_account') }}</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container" style="max-width: 500px;">
    <div class="glass-panel">
        <div style="position: relative; display: inline-block;">
            <img src="{{ user.avatar }}" style="width:80px; border-radius:50%; border: 2px solid white; margin-bottom:10px;">
            {% if user.role == 'Admin' and unread_messages and unread_messages > 0 %}
                <span class="badge-dot" style="top:0; right:0;">{{ unread_messages }}</span>
            {% endif %}
        </div>
        <h2>{{ t('my_account') }}</h2>
        <h3>{{ user.username }}</h3>
        <p>{{ t('role_tag') }} : <span class="user-tag role-{{ user.role }}">{{ user.role }}</span></p>

        {% if user.role == 'Admin' %}
        <div style="margin: 15px 0;">
            <a href="{{ url_for('contact.admin_messages') }}" class="btn btn-action" style="position: relative;">
                {{ t('messages') }}
                {% if unread_messages and unread_messages > 0 %}
                    <span class="badge-dot">{{ unread_messages }}</span>
                {% endif %}
            </a>
        </div>
        {% endif %}

        <div style="margin: 20px 0; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 12px;">
            <label for="lang-select" style="margin-right: 10px; font-weight: bold;">{{ t('lang_tag') }} :</label>
            <select id="lang-select" onchange="window.location.href = '{{ url_for('auth.set_language', code='') }}' + this.value">
                <option value="fr" {{ 'selected' if current_lang == 'fr' else '' }}>Français</option>
                <option value="en" {{ 'selected' if current_lang == 'en' else '' }}>English</option>
            </select>
        </div>
        <hr style="border-color: rgba(255,255,255,0.2); margin-bottom: 20px;">
        <a href="{{ url_for('auth.logout') }}" class="btn btn-danger">{{ t('logout') }}</a>
        <a href="{{ url_for('dashboard.index') }}" class="btn btn-nav">{{ t('back') }}</a>
    </div>
  </div>
</body>
</html>
"""
CONTACT_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contact - BotJanus</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container" style="max-width: 500px;">
    {% with messages = get_flashed_messages() %}
      {% if messages %}<div class="alert">{% for message in messages %}{{ message }}<br>{% endfor %}</div>{% endif %}
    {% endwith %}
    <div class="glass-panel" style="text-align:left;">
        <h2 style="text-align:center;">✉️ Contacter l'administrateur</h2>
        <p style="font-size:0.9em; opacity:0.8;">Un problème, une question, une suggestion ? Envoyez un message, il sera transmis directement à l'administrateur.</p>
        <form action="{{ url_for('contact.contact_form') }}" method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <textarea name="content" placeholder="Votre message..." required style="width:100%; height:150px; resize:vertical;"></textarea>
            <button type="submit" class="btn btn-action" style="width:100%; margin-top:10px;">Envoyer</button>
        </form>
        <a href="{{ url_for('dashboard.index') }}" class="btn btn-nav" style="width:100%; margin-top:10px;">{{ t('back') }}</a>
    </div>
  </div>
</body>
</html>
"""

ADMIN_MESSAGES_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Messages - Admin</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}<div class="alert">{% for message in messages %}{{ message }}<br>{% endfor %}</div>{% endif %}
    {% endwith %}
    <div class="glass-panel">
        <h2>📩 Messages reçus</h2>
        <div class="admin-nav-bar">
            <a href="{{ url_for('admin.admin_users') }}" class="btn btn-nav">Utilisateurs</a>
            <a href="{{ url_for('admin.admin_scripts') }}" class="btn btn-nav">Scripts</a>
            <a href="{{ url_for('admin.admin_schedules') }}" class="btn btn-nav">Planification</a>
            <a href="{{ url_for('admin.admin_stats') }}" class="btn btn-nav">Statistiques</a>
            <a href="{{ url_for('admin.settings') }}" class="btn btn-nav">Système</a>
            <a href="{{ url_for('contact.admin_messages') }}" class="btn btn-action">Messages</a>
            <a href="{{ url_for('dashboard.index') }}" class="btn btn-nav">← Dashboard</a>
        </div>
    </div>

    <div class="glass-panel" style="text-align:left;">
        {% if not msgs %}
            <p style="opacity:0.7;">Aucun message pour le moment.</p>
        {% endif %}
        {% for m in msgs %}
        <div class="glass-panel" style="margin-bottom:10px; {{ 'border: 1px solid #ff2d55;' if not m.is_read else '' }}">
            <div class="flex-row">
                <div>
                    <b>{{ m.username }}</b>
                    {% if not m.is_read %}<span class="user-tag" style="background:#ff2d55;">NOUVEAU</span>{% endif %}
                    <div style="font-size:0.8em; opacity:0.7;">{{ m.date }}</div>
                </div>
                <div style="display:flex; gap:5px;">
                    {% if not m.is_read %}
                    <form action="{{ url_for('contact.mark_read', message_id=m.id) }}" method="POST" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <button type="submit" class="btn btn-nav" style="padding:5px 10px; font-size:0.8em; margin:0;">Marquer comme lu</button>
                    </form>
                    {% endif %}
                    <form action="{{ url_for('contact.delete_message', message_id=m.id) }}" method="POST" style="margin:0;" onsubmit="return confirm('Supprimer ce message ?');">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        <button type="submit" class="btn btn-danger" style="padding:5px 10px; font-size:0.8em; margin:0;">Supprimer</button>
                    </form>
                </div>
            </div>
            <p style="text-align:left; margin-bottom:0; white-space:pre-wrap;">{{ m.content }}</p>
        </div>
        {% endfor %}
    </div>
  </div>
</body>
</html>
"""
ADMIN_NAV = """
<div class="admin-nav-bar">
    <a href="{{ url_for('admin.admin_users') }}" class="btn {{ 'btn-action' if active == 'users' else 'btn-nav' }}">Utilisateurs</a>
    <a href="{{ url_for('admin.admin_scripts') }}" class="btn {{ 'btn-action' if active == 'scripts' else 'btn-nav' }}">Scripts</a>
    <a href="{{ url_for('admin.admin_schedules') }}" class="btn {{ 'btn-action' if active == 'schedules' else 'btn-nav' }}">Planification</a>
    <a href="{{ url_for('admin.admin_stats') }}" class="btn {{ 'btn-action' if active == 'stats' else 'btn-nav' }}">Statistiques</a>
    <a href="{{ url_for('admin.settings') }}" class="btn {{ 'btn-action' if active == 'settings' else 'btn-nav' }}">Système</a>
    <a href="{{ url_for('contact.admin_messages') }}" class="btn {{ 'btn-action' if active == 'messages' else 'btn-nav' }}" style="position:relative;">
        Messages
        {% if unread_messages and unread_messages > 0 %}<span class="badge-dot">{{ unread_messages }}</span>{% endif %}
    </a>
    <a href="{{ url_for('dashboard.index') }}" class="btn btn-nav">← Dashboard</a>
</div>
"""

ADMIN_SCRIPTS_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Scripts - Administration</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}<div class="alert">{% for message in messages %}{{ message }}<br>{% endfor %}</div>{% endif %}
    {% endwith %}

    <div class="glass-panel">
        <h2>🛠️ Espace Administration</h2>
        """ + ADMIN_NAV + """
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>📁 Créer un script (.py)</h3>
        <form action="{{ url_for('admin.admin_create_script') }}" method="POST" style="display: flex; gap: 10px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="text" name="filename" placeholder="Ex: mon_bot.py" required style="flex: 1;">
            <button type="submit" class="btn btn-action" style="margin:0;">Créer</button>
        </form>
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>📜 Liste des Scripts (/bots)</h3>
        <div class="table-responsive">
            <table>
                <tr><th>Nom du Fichier</th><th>Accès Collaborateurs</th><th>Actions</th></tr>
                {% for script in scripts %}
                <tr>
                    <td><b>{{ script }}</b></td>
                    <td>
                        {% set is_active = configs.get(script, 1) %}
                        <span class="user-tag" style="background: {{ '#38ef7d' if is_active == 1 else '#ff416c' }}; color: {{ '#000' if is_active == 1 else '#fff' }};">
                            {{ 'Disponible' if is_active == 1 else 'Masqué' }}
                        </span>
                    </td>
                    <td>
                        <div style="display: flex; gap: 5px;">
                            <form action="{{ url_for('admin.admin_toggle_script') }}" method="POST" style="margin:0;">
                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                <input type="hidden" name="filename" value="{{ script }}">
                                <input type="hidden" name="current_val" value="{{ is_active }}">
                                <button type="submit" class="btn btn-nav" style="padding:5px 10px; font-size:0.85em;">Changer Droits</button>
                            </form>
                            <a href="{{ url_for('admin.admin_edit_script_page', filename=script) }}" class="btn btn-manual" style="padding:5px 10px; font-size:0.85em;">✏️ Éditer</a>
                            <form action="{{ url_for('admin.admin_run_script_direct') }}" method="POST" style="margin:0;">
                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                                <input type="hidden" name="filename" value="{{ script }}">
                                <button type="submit" class="btn btn-action" style="padding:5px 10px; font-size:0.85em;">⚡ Run Direct</button>
                            </form>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
  </div>
</body>
</html>
"""

SCRIPT_EDITOR_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Éditeur - {{ filename }}</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container">
    <div class="glass-panel">
        <div class="flex-row">
            <h2>✏️ Éditeur : {{ filename }}</h2>
            <a href="{{ url_for('admin.admin_scripts') }}" class="btn btn-nav">Retour</a>
        </div>
        <form action="{{ url_for('admin.admin_save_script') }}" method="POST" style="text-align: left; margin-top:15px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="hidden" name="filename" value="{{ filename }}"/>
            <textarea name="content" style="width: 100%; height: 450px; font-family: monospace; font-size: 13px; background: #070c14; color: #00ff66; padding: 10px; border-radius: 8px;">{{ content }}</textarea>
            <button type="submit" class="btn btn-action" style="width:100%; margin-top:10px;">Sauvegarder le Script</button>
        </form>
    </div>
  </div>
</body>
</html>
"""

SCHEDULES_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Planification - Admin</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container">
    <div class="glass-panel">
        <h2>⏳ Automatisation Planifiée</h2>
        """ + ADMIN_NAV + """
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>⏰ Ajouter une tâche</h3>
        <form action="{{ url_for('admin.admin_schedules') }}" method="POST" style="display: flex; gap: 10px; flex-wrap: wrap;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="hidden" name="action" value="add"/>
            <select name="script_name">
                {% for s in scripts %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
            </select>
            <select name="frequency">
                <option value="minutes">Minutes</option>
                <option value="hours">Heures</option>
                <option value="days">Jours</option>
            </select>
            <input type="number" name="time_value" value="30" style="width:80px;">
            <button type="submit" class="btn btn-action" style="margin:0;">Créer Répétition</button>
        </form>
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>📋 Planifications actives</h3>
        <div class="table-responsive">
            <table>
                <tr><th>Script</th><th>Intervalle</th><th>Dernier Run</th><th>Prochain Run</th><th>Action</th></tr>
                {% for s in schedules %}
                <tr>
                    <td><b>{{ s.script_name }}</b></td>
                    <td>Toutes les {{ s.time_value }} {{ s.frequency }}</td>
                    <td>{{ s.last_run }}</td>
                    <td style="color:#38ef7d;">{{ s.next_run }}</td>
                    <td>
                        <form action="{{ url_for('admin.admin_schedules') }}" method="POST" style="margin:0;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                            <input type="hidden" name="action" value="delete"/>
                            <input type="hidden" name="id" value="{{ s.id }}"/>
                            <button type="submit" class="btn btn-danger" style="padding:5px;">Supprimer</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
  </div>
</body>
</html>
"""

STATS_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Statistiques - Admin</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container">
    <div class="glass-panel">
        <h2>📊 Rapports & Statistiques</h2>
        """ + ADMIN_NAV + """
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
        <div class="glass-panel"><h3>Membres inscrits</h3><p style="font-size:2em; color:#38ef7d;">{{ total_users }}</p></div>
        <div class="glass-panel"><h3>Volume Logs</h3><p style="font-size:2em; color:#00b4d8;">{{ total_logs }}</p></div>
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>📈 Activité par Module (Lignes de logs)</h3>
        <table>
            <tr><th>Nom du Module</th><th>Volume d'activité</th></tr>
            {% for c in script_counts %}
            <tr><td>{{ c.script }}</td><td><b>{{ c.cnt }}</b> lignes</td></tr>
            {% endfor %}
        </table>
    </div>
  </div>
</body>
</html>
"""

ADMIN_USERS_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ t('users_roles') }}</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container">
    <div class="glass-panel">
        <h2>{{ t('settings') }}</h2>
        """ + ADMIN_NAV + """
    </div>
    <div class="glass-panel" style="text-align:left;">
        <h3>✅ {{ t('users_roles') }}</h3>
        <div class="table-responsive">
            <table>
                <tr><th>User</th><th>{{ t('role_tag') }}</th><th>{{ t('actions') }}</th></tr>
                {% for u in users if not u.is_banned %}
                <tr>
                    <td><b>{{ u.username }}</b></td>
                    <td><span class="user-tag role-{{ u.role }}">{{ u.role }}</span></td>
                    <td>
                        <form action="{{ url_for('admin.admin_update_user') }}" method="POST" id="form-{{ u.wiki_id }}" style="display:flex; gap:5px;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                            <input type="hidden" name="wiki_id" value="{{ u.wiki_id }}">
                            <input type="hidden" name="reason" id="reason-{{ u.wiki_id }}" value="">
                            <input type="hidden" name="action" id="action-{{ u.wiki_id }}" value="update">
                            <select name="new_role" style="padding:5px;">
                                <option value="None" {{ 'selected' if u.role == 'None' else '' }}>None</option>
                                <option value="Collaborateur" {{ 'selected' if u.role == 'Collaborateur' else '' }}>Collaborateur</option>
                                <option value="Admin" {{ 'selected' if u.role == 'Admin' else '' }}>Admin</option>
                            </select>
                            <button type="submit" class="btn btn-nav" style="padding:5px 10px; margin:0; font-size:0.8em;">{{ t('update') }}</button>
                            <button type="button" onclick="confirmBan('{{ u.wiki_id }}', '{{ u.username }}')" class="btn btn-danger" style="padding:5px 10px; margin:0; font-size:0.8em;">{{ t('ban') }}</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
  </div>
  <script>
    function confirmBan(userId, username) {
        let reason = prompt("Raison du bannissement pour " + username + " ?");
        if (reason) {
            document.getElementById('reason-' + userId).value = reason;
            document.getElementById('action-' + userId).value = 'ban';
            document.getElementById('form-' + userId).submit();
        }
    }
  </script>
</body>
</html>
"""

SETTINGS_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ t('system_settings') }}</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container" style="max-width: 600px;">
    {% with messages = get_flashed_messages() %}
      {% if messages %}<div class="alert">{% for message in messages %}{{ message }}<br>{% endfor %}</div>{% endif %}
    {% endwith %}
    <div class="glass-panel">
        <h2>{{ t('system_settings') }}</h2>
        """ + ADMIN_NAV + """
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>💾 Sauvegardes de Données (Format Excel)</h3>
        <p style="font-size:0.85em; opacity:0.8;">Exportez les profils ou effectuez une restauration en cas d'anomalie système.</p>
        <a href="{{ url_for('admin.backup_export') }}" class="btn btn-action" style="margin-left:0;">📥 Exporter la base (CSV)</a>
        <hr style="border-color:rgba(255,255,255,0.1); margin:15px 0;">
        <form action="{{ url_for('admin.backup_import') }}" method="POST" enctype="multipart/form-data">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="file" name="backup_file" accept=".csv" required><br><br>
            <button type="submit" class="btn btn-danger" style="margin:0;">📤 Restaurer le fichier</button>
        </form>
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>🧹 Gestion et Nettoyage des Logs</h3>

        <form action="{{ url_for('admin.clean_logs_manual') }}" method="POST" style="margin-bottom: 20px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <p style="font-size:0.85em; opacity:0.8;"><b>Nettoyage ciblé :</b> Supprimer définitivement les logs plus anciens que X jours.</p>
            <div style="display: flex; gap: 10px; align-items: center;">
                <input type="number" name="days" min="0" placeholder="Ex: 7" required style="width: 100px;">
                <span>jours</span>
                <button type="submit" class="btn btn-danger" style="margin:0;">Supprimer par ancienneté</button>
            </div>
        </form>

        <hr style="border-color:rgba(255,255,255,0.1); margin:15px 0;">

        <form action="{{ url_for('admin.delete_all_logs') }}" method="POST"
              onsubmit="return confirm('Supprimer DÉFINITIVEMENT tous les logs ? Cette action est irréversible.');">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <p style="font-size:0.85em; opacity:0.8;"><b>Nettoyage total :</b> Supprime immédiatement l'intégralité des logs ({{ total_logs }} entrée(s) actuellement).</p>
            <button type="submit" class="btn btn-danger" style="margin:0;">🗑️ Supprimer TOUS les logs</button>
        </form>
    </div>

    <div class="glass-panel" style="text-align: left;">
        <h3>{{ t('security') }}</h3>
        <form action="{{ url_for('admin.update_settings') }}" method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <label style="display: flex; align-items: center; margin-bottom:15px;">
                <input type="checkbox" name="lock_launch" value="1" {% if locked == '1' %}checked{% endif %} style="width: 20px; height: 20px; margin-right: 10px;">
                <span>{{ t('lock_option') }}</span>
            </label>
            <label style="display: flex; align-items: center; margin-bottom:15px;">
                <input type="checkbox" name="captcha_enabled" value="1" {% if captcha_enabled == '1' %}checked{% endif %} style="width: 20px; height: 20px; margin-right: 10px;">
                <span>Activer le portail reCAPTCHA Google</span>
            </label>
            <button class="btn btn-action" type="submit">{{ t('save') }}</button>
        </form>
    </div>
  </div>
</body>
</html>
"""
HISTORY_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ t('history') }}</title>
  {{ glass_css|safe }}
</head>
<body>
  <div class="container" style="max-width: 1100px;">
    <div class="glass-panel" style="text-align: left;">
        <div class="flex-row">
            <h2 style="margin:0;">📂 Logs</h2>
            <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                <a href="{{ url_for('dashboard.export_logs_excel') }}{% if request.args.get('search') %}?search={{ request.args.get('search') }}{% endif %}" class="btn btn-action" style="margin:0; padding:8px 16px; font-size:0.85em;">📊 Export Excel</a>
                <a href="{{ url_for('dashboard.export_logs_csv') }}{% if request.args.get('search') %}?search={{ request.args.get('search') }}{% endif %}" class="btn btn-nav" style="margin:0; padding:8px 16px; font-size:0.85em;">📄 Export CSV</a>
                <a href="{{ url_for('dashboard.index') }}" class="btn btn-nav" style="margin:0;">← {{ t('back') }}</a>
            </div>
        </div>
        <form id="filter-form" action="{{ url_for('dashboard.history') }}" method="GET" style="margin-top:15px;">
            <input type="text" name="search" placeholder="Rechercher un message..." value="{{ request.args.get('search', '') }}">
            <button type="submit" class="btn btn-nav">🔍</button>
        </form>
        <p style="font-size:0.8em; opacity:0.6; margin:8px 0 0 0;">{{ total_count }} entrée(s) trouvée(s) — affichage des 500 plus récentes</p>
        <div class="table-responsive">
            <table>
                <tr><th>Date</th><th>Script</th><th>Message</th></tr>
                {% for row in rows %}
                <tr>
                    <td style="color: #a8dadc; white-space:nowrap;">{{ row[1] }}</td>
                    <td>{{ row[2] }}</td>
                    <td>{{ row[3] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
  </div>
</body>
</html>
"""