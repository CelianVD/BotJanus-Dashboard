import os
import io
import csv
import secrets
from datetime import datetime, timedelta
from urllib.parse import quote

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from flask import (Blueprint, render_template_string, redirect, url_for, request,
                    session, flash, jsonify, Response)

import wiki_auth
from flask_app import (MANUAL_ADMIN_ID, MANUAL_ADMIN_USERNAME, MANUAL_LOGIN_ID, MANUAL_LOGIN_PASS,
                  WIKI_ROOT_ADMIN_USERNAME,
                  ROLE_NONE, ROLE_COLLAB, ROLE_ADMIN, RECAPTCHA_SITE_KEY, BOTS_DIR,
                  get_db, get_text, log_to_db, verify_recaptcha, get_all_bots, get_script_status,
                  login_required, check_role, require_api_key, csrf, status,
                  launch_script_core, stop_current_script)
from templates import (GLASS_CSS, GATE_HTML, LOGIN_MANUAL_HTML, ACCOUNT_HTML,
                        DASHBOARD_HTML, HISTORY_HTML)

_alog = wiki_auth.log_auth  # journal logs_vikidia_auth.txt

auth_bp = Blueprint("auth", __name__)
dashboard_bp = Blueprint("dashboard", __name__)
api_bp = Blueprint("api", __name__)


# ============================================================
# PROMOTION AUTOMATIQUE (None -> Collaborateur via statut autopatrol)
# ============================================================

def _try_auto_promote(db, user):
    """Appelée quand un compte de rôle "None" tente de LANCER un script (web ou Discord).

    Interroge les wikis Vikidia (arrêt dès le premier wiki qualifiant). Si le statut
    autopatrolled (ou supérieur) est trouvé, le rôle est passé à Collaborateur EN BASE :
    la promotion est définitive (un admin peut ensuite la retirer à la main).

    Renvoie : 'already' | 'promoted' | 'denied' | 'unverifiable'
    """
    if user['role'] in (ROLE_COLLAB, ROLE_ADMIN):
        return 'already'
    _alog(f"PROMOTION : vérification demandée pour {user['username']!r} (id={user['wiki_id']}, rôle actuel={user['role']})")
    wiki_code, incomplete = wiki_auth.find_autopatrol_wiki(user['username'])
    if wiki_code:
        db.execute("UPDATE users SET role = ? WHERE wiki_id = ? AND role NOT IN (?, ?)",
                   (ROLE_COLLAB, user['wiki_id'], ROLE_COLLAB, ROLE_ADMIN))
        db.commit()
        log_to_db("SYSTEM", f"{user['username']} promu {ROLE_COLLAB} automatiquement "
                            f"(autopatrol sur {wiki_code}.vikidia.org)")
        _alog(f"PROMOTION : {user['username']!r} -> {ROLE_COLLAB} ENREGISTRÉ en base (via {wiki_code}.vikidia.org)")
        return 'promoted'
    outcome = 'unverifiable' if incomplete else 'denied'
    _alog(f"PROMOTION : {user['username']!r} NON promu -> {outcome}")
    return outcome


# ============================================================
# AUTH
# ============================================================

@auth_bp.route("/security-gate")
def security_gate():
    return render_template_string(GATE_HTML, site_key=RECAPTCHA_SITE_KEY, glass_css=GLASS_CSS)


@auth_bp.route("/verify-gate", methods=["POST"])
def verify_gate():
    captcha_response = request.form.get('g-recaptcha-response')
    if verify_recaptcha(captcha_response):
        session['captcha_passed'] = True
        return redirect(url_for('dashboard.index'))
    flash("Veuillez valider le captcha correctement.")
    return redirect(url_for('auth.security_gate'))


@auth_bp.route("/set_lang/<code>")
def set_language(code):
    if code not in ['fr', 'en']:
        code = 'fr'
    session['lang'] = code
    if 'user_id' in session:
        try:
            db = get_db()
            db.execute("UPDATE users SET lang = ? WHERE wiki_id = ?", (code, session['user_id']))
            db.commit()
        except Exception:
            pass
    return redirect(request.referrer or url_for('dashboard.index'))


@auth_bp.route("/admin/login")
def manual_login_page():
    return render_template_string(LOGIN_MANUAL_HTML, glass_css=GLASS_CSS)


@auth_bp.route("/admin/login_post", methods=['POST'])
def manual_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == MANUAL_LOGIN_ID and password == MANUAL_LOGIN_PASS:
        db = get_db()
        existing_lang = db.execute("SELECT lang FROM users WHERE wiki_id = ?", (MANUAL_ADMIN_ID,)).fetchone()
        current_lang = existing_lang['lang'] if existing_lang else 'fr'
        db.execute("""INSERT OR REPLACE INTO users (wiki_id, username, avatar, role, is_banned, lang)
                        VALUES (?, ?, ?, ?, 0, ?)""",
                   (MANUAL_ADMIN_ID, MANUAL_ADMIN_USERNAME,
                    "https://ui-avatars.com/api/?name=Admin+Bot&background=ff0000&color=fff", ROLE_ADMIN, current_lang))
        db.commit()
        session.permanent = True
        session['user_id'] = MANUAL_ADMIN_ID
        session['username'] = MANUAL_ADMIN_USERNAME
        session['lang'] = current_lang
        flash("Connexion Admin Manuelle Réussie.")
        return redirect(url_for('dashboard.index'))
    flash(get_text('error_manual_login'))
    return redirect(url_for('auth.manual_login_page'))


@auth_bp.route("/login")
def login_wiki():
    # (Une éventuelle liaison Discord en cours reste dans la session pendant le
    # round-trip OAuth : voir callback_wiki.)
    verifier, challenge = wiki_auth.generate_pkce_pair()
    state = secrets.token_urlsafe(24)
    session['wiki_oauth_state'] = state
    session['wiki_oauth_verifier'] = verifier
    _alog("LOGIN : redirection vers Vikidia OAuth")
    return redirect(wiki_auth.build_authorize_url(state, challenge))


@auth_bp.route("/oauth/wiki/callback")
@csrf.exempt
def callback_wiki():
    expected_state = session.pop('wiki_oauth_state', None)
    verifier = session.pop('wiki_oauth_verifier', None)

    # L'utilisateur a refusé l'autorisation (ou le wiki a renvoyé une erreur).
    if request.args.get('error'):
        _alog(f"CALLBACK : erreur renvoyée par Vikidia | error={request.args.get('error')!r} "
              f"| description={request.args.get('error_description')!r}")
        flash("Connexion Vikidia annulée ou refusée.")
        return redirect(url_for('dashboard.index'))

    code = request.args.get('code')
    state = request.args.get('state')
    if not code or not state or not verifier or state != expected_state:
        _alog(f"CALLBACK : état invalide | code_présent={bool(code)} state_présent={bool(state)} "
              f"verifier_en_session={bool(verifier)} state_identique={state == expected_state} "
              "(cookie de session perdu ? SESSION_COOKIE_SECURE / domaine ?)")
        flash("Échec de la connexion Vikidia (état invalide).")
        return redirect(url_for('dashboard.index'))

    token_data = wiki_auth.exchange_code_for_token(code, verifier)
    if not token_data:
        _alog("CALLBACK : échange du code impossible (voir ligne OAUTH token ci-dessus)")
        flash("Échec de la connexion Vikidia (échange du code impossible).")
        return redirect(url_for('dashboard.index'))

    profile = wiki_auth.fetch_profile(token_data['access_token'])
    if not profile:
        _alog("CALLBACK : profil introuvable (voir ligne OAUTH profil ci-dessus)")
        flash("Échec de la connexion Vikidia (profil introuvable).")
        return redirect(url_for('dashboard.index'))

    wiki_id = str(profile.get('sub') or profile.get('id') or profile['username'])
    username = profile['username']
    avatar_url = f"https://ui-avatars.com/api/?name={quote(username)}&background=0093E9&color=fff"
    is_root_admin = (username == WIKI_ROOT_ADMIN_USERNAME)

    db = get_db()
    existing = db.execute("SELECT * FROM users WHERE wiki_id = ?", (wiki_id,)).fetchone()

    if existing:
        if existing['is_banned']:
            _alog(f"CALLBACK : connexion REFUSÉE, compte banni | {username!r} (id={wiki_id})")
            flash(f"Compte banni. Raison : {existing['ban_reason'] or 'Non spécifiée'}")
            return redirect(url_for('dashboard.index'))
        # Le rôle existant est CONSERVÉ (y compris une promotion automatique passée).
        # Seul l'admin racine est toujours ré-imposé Admin. UPDATE plutôt que
        # INSERT OR REPLACE : on ne touche ni à ban_reason ni à discord_id.
        role = ROLE_ADMIN if is_root_admin else existing['role']
        lang = existing['lang'] or 'fr'
        db.execute("UPDATE users SET username = ?, avatar = ?, role = ? WHERE wiki_id = ?",
                   (username, avatar_url, role, wiki_id))
    else:
        # Première connexion : "None" (la promotion se fera au premier lancement).
        role = ROLE_ADMIN if is_root_admin else ROLE_NONE
        lang = 'fr'
        db.execute("""INSERT INTO users (wiki_id, username, avatar, role, is_banned, lang)
                      VALUES (?, ?, ?, ?, 0, ?)""",
                   (wiki_id, username, avatar_url, role, lang))
    db.commit()
    _alog(f"CALLBACK : connexion RÉUSSIE | {username!r} (id={wiki_id}) | rôle={role} "
          f"| {'nouveau compte' if not existing else 'compte existant'}{' | admin racine' if is_root_admin else ''}")

    # Nouvelle session (anti-fixation), en gardant ce qui doit survivre au login.
    keep = {k: session[k] for k in ('captcha_passed', 'pending_discord_link') if k in session}
    session.clear()
    session.update(keep)
    session.permanent = True  # applique PERMANENT_SESSION_LIFETIME (60 min)
    session['user_id'], session['username'], session['lang'] = wiki_id, username, lang

    # Reprise d'une liaison Discord démarrée avant la connexion (/discord/link/<token>).
    pending_token = session.pop('pending_discord_link', None)
    if pending_token:
        return redirect(url_for('auth.discord_link_confirm', token=pending_token))

    return redirect(url_for('dashboard.index'))


# ============================================================
# LIAISON DE COMPTE DISCORD <-> VIKIDIA
# ============================================================
# Le robot Discord appelle POST /api/discord/link/start pour obtenir une URL à usage
# unique. L'utilisateur l'ouvre, se connecte via Vikidia OAuth si besoin, puis confirme
# la liaison ici. Ensuite, GET /api/discord/permissions?discord_id=... permet au robot
# de vérifier les droits (voir auth_check.py côté bot).

DISCORD_LINK_TOKEN_TTL_MINUTES = 15


@auth_bp.route("/discord/link/<token>")
def discord_link_confirm(token):
    db = get_db()
    link = db.execute("SELECT * FROM discord_links WHERE token = ?", (token,)).fetchone()
    if not link or link['used']:
        flash("Ce lien de liaison Discord est invalide ou a déjà été utilisé.")
        return redirect(url_for('dashboard.index'))

    created_at = datetime.strptime(link['created_at'], "%Y-%m-%d %H:%M:%S")
    if datetime.now() - created_at > timedelta(minutes=DISCORD_LINK_TOKEN_TTL_MINUTES):
        flash("Ce lien de liaison Discord a expiré, relance /auth sur Discord.")
        return redirect(url_for('dashboard.index'))

    if 'user_id' not in session:
        # On garde le token en session pour reprendre la liaison juste après le login.
        session['pending_discord_link'] = token
        return redirect(url_for('auth.login_wiki'))

    db.execute("UPDATE users SET discord_id = ? WHERE wiki_id = ?", (link['discord_id'], session['user_id']))
    db.execute("UPDATE discord_links SET used = 1 WHERE token = ?", (token,))
    db.commit()
    flash(f"Compte Discord ({link['discord_username']}) lié avec succès à votre compte Vikidia.")
    return redirect(url_for('auth.account'))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('dashboard.index'))


@auth_bp.route("/account")
@login_required
def account():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE wiki_id = ?", (session['user_id'],)).fetchone()
    return render_template_string(ACCOUNT_HTML, user=user, glass_css=GLASS_CSS)


# ============================================================
# DASHBOARD
# ============================================================

@dashboard_bp.route("/")
def index():
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key='lock_launch'").fetchone()
    locked = row['value'] if row else '0'
    user_role = ROLE_NONE
    if 'user_id' in session:
        u = db.execute("SELECT role FROM users WHERE wiki_id=?", (session['user_id'],)).fetchone()
        if u:
            user_role = u['role']

    all_files = get_all_bots()
    available_scripts = []
    for f in all_files:
        is_act = get_script_status(f)
        if user_role == ROLE_ADMIN or is_act == 1:
            available_scripts.append({"filename": f, "is_active": is_act})

    return render_template_string(
        DASHBOARD_HTML, running=status["running"], script_name=status.get("script_name") or "Inactif",
        logs=status["live_output"][-50:], locked=locked, role=user_role, glass_css=GLASS_CSS,
        available_scripts=available_scripts
    )


@dashboard_bp.route("/start", methods=["POST"])
@login_required
def start_script():
    """Lancement d'un script.

    Seuls Collaborateur/Admin peuvent lancer. Un compte "None" voit l'interface, mais
    c'est ICI, au clic sur DÉMARRER, que l'on vérifie son statut autopatrol sur les
    wikis : trouvé -> promu Collaborateur (persisté) ET lancement accepté.
    Les contrôles peu coûteux passent d'abord, la vérification réseau en dernier.
    """
    db = get_db()
    lock_row = db.execute("SELECT value FROM settings WHERE key='lock_launch'").fetchone()
    locked_val = lock_row['value'] if lock_row else '0'
    user = db.execute("SELECT * FROM users WHERE wiki_id=?", (session['user_id'],)).fetchone()

    # 1. Compte
    if not user or user['is_banned']:
        _alog(f"START : refusé, compte introuvable ou banni | session user_id={session.get('user_id')!r}")
        session.clear()
        flash("Compte banni.")
        return redirect(url_for('dashboard.index'))
    is_admin = user['role'] == ROLE_ADMIN
    choice = request.form.get("choice") or ""
    _alog(f"START : demande de {user['username']!r} (id={user['wiki_id']}, rôle={user['role']}) "
          f"| script={choice!r} | verrou={locked_val}")

    # 2. Verrou global (admins seulement) : avant toute vérification wiki, pour qu'un
    #    lancement bloqué ne provoque aucune promotion.
    if locked_val == '1' and not is_admin:
        _alog("START : refusé, lancement verrouillé par l'admin (aucune vérification wiki)")
        flash("Verrouillé par l'Admin.")
        return redirect(url_for('dashboard.index'))

    # 3. Un script tourne déjà ?
    if status["running"]:
        _alog("START : refusé, un script est déjà en cours")
        flash("Un script est déjà en cours d'exécution.")
        return redirect(url_for('dashboard.index'))

    # 4. Script demandé : doit exister dans BOTS_DIR (bloque le path traversal / None)
    if choice not in get_all_bots():
        _alog(f"START : refusé, script introuvable dans BOTS_DIR : {choice!r}")
        flash("Script introuvable.")
        return redirect(url_for('dashboard.index'))
    if not is_admin and get_script_status(choice) == 0:
        _alog(f"START : refusé, script désactivé par l'admin : {choice!r}")
        flash("Ce script a été désactivé par l'administrateur.")
        return redirect(url_for('dashboard.index'))

    # 5. Arguments du script Portail
    cmd_args = []
    if "portal.py" in choice or choice == "Portail":
        arg_lang = request.form.get("arg_lang")
        arg_cat = request.form.get("arg_cat")
        arg_portal = request.form.get("arg_portal")
        if not (arg_lang and arg_cat and arg_portal):
            _alog("START : refusé, paramètres du portail manquants")
            flash("Paramètres du portail manquants.")
            return redirect(url_for('dashboard.index'))
        cmd_args = ["--lang", arg_lang, "--cat", arg_cat, "--portal", arg_portal]

    # 6. Droit de lancer : rôle "None" -> vérification wiki + promotion automatique
    promoted = False
    if user['role'] not in (ROLE_COLLAB, ROLE_ADMIN):
        outcome = _try_auto_promote(db, user)
        if outcome == 'promoted':
            promoted = True
        elif outcome == 'unverifiable':
            _alog("START : refusé, vérification wiki incomplète (message 'réessayez' affiché)")
            flash(get_text('error_wiki_check_failed'))
            return redirect(url_for('dashboard.index'))
        else:
            _alog("START : refusé, aucun statut autopatrol trouvé")
            flash(get_text('error_not_autopatrolled'))
            return redirect(url_for('dashboard.index'))

    # 7. Lancement
    p = os.path.join(BOTS_DIR, choice)
    if launch_script_core(choice, p, args=cmd_args, user_name=session.get('username')):
        _alog(f"START : script {choice!r} LANCÉ pour {user['username']!r}{' (après promotion auto)' if promoted else ''}")
        if promoted:
            flash(get_text('promoted_msg'))
    else:
        _alog(f"START : échec du lancement de {choice!r}")
        flash("Impossible de lancer le script (un processus est déjà actif ou erreur de démarrage).")
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/stop", methods=["POST"])
@check_role([ROLE_COLLAB, ROLE_ADMIN])
def stop_script():
    stop_current_script(user_name=session.get('username'))
    return redirect(url_for("dashboard.index"))


# ============================================================
# HISTORIQUE DES LOGS + EXPORTS
# ============================================================

def _get_logs_for_export(f_search=None):
    query = "SELECT id, date, script, message FROM logs WHERE 1=1"
    params = []
    if f_search:
        query += " AND message LIKE ?"
        params.append("%" + f_search + "%")
    query += " ORDER BY id DESC"
    db = get_db()
    return db.execute(query, params).fetchall()


@dashboard_bp.route("/history")
def history():
    f_search = request.args.get('search')
    query = "SELECT * FROM logs WHERE 1=1"
    params = []
    if f_search:
        query += " AND message LIKE ?"
        params.append(f"%{f_search}%")
    query += " ORDER BY id DESC LIMIT 500"
    db = get_db()
    rows = db.execute(query, params).fetchall()

    count_query = "SELECT COUNT(*) FROM logs WHERE 1=1"
    if f_search:
        count_query += " AND message LIKE ?"
    total_count = db.execute(count_query, params).fetchone()[0]

    return render_template_string(HISTORY_HTML, rows=rows, request=request, glass_css=GLASS_CSS, total_count=total_count)


@dashboard_bp.route("/history/export/excel")
def export_logs_excel():
    f_search = request.args.get('search')
    rows = _get_logs_for_export(f_search)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Logs BotJanus"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="0B132B", end_color="0B132B", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    headers = ["ID", "Date", "Script", "Message"]
    col_widths = [8, 22, 25, 80]
    for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width
    ws.row_dimensions[1].height = 22

    fill_light = PatternFill(start_color="EAF4FB", end_color="EAF4FB", fill_type="solid")
    fill_dark = PatternFill(start_color="D0E8F2", end_color="D0E8F2", fill_type="solid")

    for row_idx, row in enumerate(rows, start=2):
        fill = fill_light if row_idx % 2 == 0 else fill_dark
        values = [row[0], row[1], row[2], row[3]]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.fill = fill
            cell.alignment = Alignment(vertical="top", wrap_text=(col_idx == 4))

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = "A1:D1"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = "logs_botjanus_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=" + filename}
    )


@dashboard_bp.route("/history/export/csv")
def export_logs_csv():
    f_search = request.args.get('search')
    rows = _get_logs_for_export(f_search)

    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['ID', 'Date', 'Script', 'Message'])
    for row in rows:
        cw.writerow([row[0], row[1], row[2], row[3]])

    filename = "logs_botjanus_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=" + filename}
    )


# ============================================================
# API DISCORD
# ============================================================

# ============================================================
# API DISCORD
# ============================================================

@api_bp.route('/api/status', methods=['GET'])
@csrf.exempt
@require_api_key
def api_status():
    return jsonify({
        "running": status["running"],
        "script_name": status.get("script_name") or "Inactif",
        "last_activity": status["last_activity"].isoformat() if status["last_activity"] else None
    })


@api_bp.route('/api/status_json')
def status_json():
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key='lock_launch'").fetchone()
    locked = row['value'] if row else '0'
    user_role = ROLE_NONE
    if 'user_id' in session:
        u = db.execute("SELECT role FROM users WHERE wiki_id=?", (session['user_id'],)).fetchone()
        if u:
            user_role = u['role']
    return jsonify({
        "running": status["running"],
        "script_name": status.get("script_name") or "Inactif",
        "locked": locked,
        "role": user_role
    })


@api_bp.route('/api/start', methods=['POST'])
@csrf.exempt
@require_api_key
def api_start():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400
    choice = data.get('choice')
    discord_username = data.get('username', 'Discord')
    if not choice:
        return jsonify({"error": "Paramètre 'choice' manquant"}), 400
    if status["running"]:
        return jsonify({"error": "Un script est déjà en cours"}), 409

    p = os.path.join(BOTS_DIR, choice)
    if os.path.exists(p):
        cmd_args = []
        if choice == "portal.py" or choice == "Portail":
            cmd_args = ["--lang", data.get("arg_lang", "fr"), "--cat", data.get("arg_cat", ""), "--portal", data.get("arg_portal", "")]
        success = launch_script_core(choice, p, args=cmd_args, user_name=f"Discord ({discord_username})")
        if success:
            return jsonify({"success": True, "message": f"Script {choice} lancé."}), 200
    return jsonify({"error": "Fichier introuvable"}), 404


@api_bp.route('/api/stop', methods=['POST'])
@csrf.exempt
@require_api_key
def api_stop():
    if not status["running"] or not status["process"]:
        return jsonify({"error": "Aucun script en cours"}), 400
    try:
        stop_current_script(user_name="Discord")
        return jsonify({"success": True, "message": "Script arrêté."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/api/logs', methods=['GET'])
@csrf.exempt
@require_api_key
def api_logs():
    limit = request.args.get('limit', 50, type=int)
    return jsonify({"logs": status["live_output"][-limit:]})


@api_bp.route('/api/scripts', methods=['GET'])
@csrf.exempt
@require_api_key
def api_scripts():
    scripts = []
    for filename in get_all_bots():
        scripts.append({"filename": filename, "is_active": bool(get_script_status(filename))})
    return jsonify({"scripts": scripts})


@api_bp.route("/api/live_logs")
def live_logs():
    return "\n".join([f"<div>{line}</div>" for line in status["live_output"][-100:]])


# ============================================================
# API DISCORD — LIAISON DE COMPTE & PERMISSIONS (utilisées par auth_check.py côté bot)
# ============================================================

@api_bp.route('/api/discord/link/start', methods=['POST'])
@csrf.exempt
@require_api_key
def api_discord_link_start():
    data = request.get_json(silent=True) or {}
    discord_id = data.get('discord_id')
    discord_username = data.get('discord_username', 'Discord')
    if not discord_id:
        return jsonify({"error": "Paramètre 'discord_id' manquant"}), 400

    token = secrets.token_urlsafe(24)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    db.execute(
        "INSERT INTO discord_links (token, discord_id, discord_username, created_at, used) VALUES (?, ?, ?, ?, 0)",
        (token, str(discord_id), discord_username, created_at)
    )
    db.commit()
    return jsonify({"url": url_for('auth.discord_link_confirm', token=token, _external=True)}), 200


@api_bp.route('/api/discord/permissions', methods=['GET'])
@csrf.exempt
@require_api_key
def api_discord_permissions():
    discord_id = request.args.get('discord_id')
    if not discord_id:
        return jsonify({"error": "Paramètre 'discord_id' manquant"}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE discord_id = ?", (str(discord_id),)).fetchone()
    if not user:
        return jsonify({"linked": False, "authorized": False, "reason": "not_linked"})

    if user['is_banned']:
        return jsonify({"linked": True, "authorized": False, "reason": "banned",
                         "username": user['username']})

    if user['role'] in (ROLE_COLLAB, ROLE_ADMIN):
        return jsonify({"linked": True, "authorized": True, "role": user['role'],
                         "username": user['username']})

    _alog(f"DISCORD permissions : demande pour discord_id={discord_id} -> {user['username']!r} (rôle={user['role']})")
    # Rôle "None" lié : même règle que sur le dashboard web (vérification wiki au moment
    # de la demande de lancement, arrêt au premier wiki qualifiant, promotion persistée).
    outcome = _try_auto_promote(db, user)
    if outcome == 'promoted':
        return jsonify({"linked": True, "authorized": True, "role": ROLE_COLLAB,
                         "via": "autopatrol", "username": user['username']})

    # "retry": les wikis n'ont pas tous répondu -> le bot peut proposer de réessayer.
    return jsonify({"linked": True, "authorized": False, "reason": "not_autopatrolled",
                     "retry": outcome == 'unverifiable', "username": user['username']})