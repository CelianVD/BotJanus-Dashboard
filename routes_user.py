import os
import io
import csv
from datetime import datetime

import requests
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from flask import (Blueprint, render_template_string, redirect, url_for, request,
                    session, flash, jsonify, Response)

from flask_app import (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI, GITHUB_API_BASE_URL,
                  MANUAL_ADMIN_ID, MANUAL_ADMIN_USERNAME, MANUAL_LOGIN_ID, MANUAL_LOGIN_PASS,
                  ROLE_NONE, ROLE_COLLAB, ROLE_ADMIN, RECAPTCHA_SITE_KEY, BOTS_DIR,
                  get_db, get_text, verify_recaptcha, get_all_bots, get_script_status,
                  login_required, check_role, require_api_key, csrf, status,
                  launch_script_core, stop_current_script)
from templates import (GLASS_CSS, GATE_HTML, LOGIN_MANUAL_HTML, ACCOUNT_HTML,
                        DASHBOARD_HTML, HISTORY_HTML)

auth_bp = Blueprint("auth", __name__)
dashboard_bp = Blueprint("dashboard", __name__)
api_bp = Blueprint("api", __name__)


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
            db.execute("UPDATE users SET lang = ? WHERE github_id = ?", (code, session['user_id']))
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
        existing_lang = db.execute("SELECT lang FROM users WHERE github_id = ?", (MANUAL_ADMIN_ID,)).fetchone()
        current_lang = existing_lang['lang'] if existing_lang else 'fr'
        db.execute("""INSERT OR REPLACE INTO users (github_id, username, avatar, role, is_banned, lang)
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
def login_github():
    github_auth_url = (f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}"
                        f"&redirect_uri={GITHUB_REDIRECT_URI}&scope=user:email")
    return redirect(github_auth_url)


@auth_bp.route("/callback")
@csrf.exempt
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('dashboard.index'))
    data = {'client_id': GITHUB_CLIENT_ID, 'client_secret': GITHUB_CLIENT_SECRET, 'code': code}
    try:
        r = requests.post('https://github.com/login/oauth/access_token', data=data, headers={'Accept': 'application/json'})
        token_data = r.json()
        if 'access_token' not in token_data:
            return redirect(url_for('dashboard.index'))

        r_user = requests.get(f"{GITHUB_API_BASE_URL}/user", headers={'Authorization': f"Bearer {token_data['access_token']}"})
        user_info = r_user.json()
        github_id, username = str(user_info['id']), user_info['login']
        avatar_url = user_info.get('avatar_url', 'https://avatars.githubusercontent.com/u/0?v=4')

        db = get_db()
        existing_user = db.execute("SELECT * FROM users WHERE github_id = ?", (github_id,)).fetchone()
        role, lang = ROLE_NONE, 'fr'
        if username == "janus":
            role = ROLE_ADMIN

        if existing_user:
            role, lang = existing_user['role'], existing_user['lang'] or 'fr'
            if existing_user['is_banned']:
                return redirect(url_for('dashboard.index'))

        db.execute("""INSERT OR REPLACE INTO users (github_id, username, avatar, role, is_banned, lang, ban_reason)
                      VALUES (?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE github_id=?), 0), ?,
                              (SELECT ban_reason FROM users WHERE github_id=?))""",
                   (github_id, username, avatar_url, role, github_id, lang, github_id))
        db.commit()

        session['user_id'], session['username'], session['lang'] = github_id, username, lang
        return redirect(url_for('dashboard.index'))
    except Exception:
        return redirect(url_for('dashboard.index'))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('dashboard.index'))


@auth_bp.route("/account")
@login_required
def account():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE github_id = ?", (session['user_id'],)).fetchone()
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
        u = db.execute("SELECT role FROM users WHERE github_id=?", (session['user_id'],)).fetchone()
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
@check_role([ROLE_COLLAB, ROLE_ADMIN])
def start_script():
    db = get_db()
    locked_val = db.execute("SELECT value FROM settings WHERE key='lock_launch'").fetchone()['value']
    user = db.execute("SELECT role FROM users WHERE github_id=?", (session['user_id'],)).fetchone()

    if locked_val == '1' and user['role'] != ROLE_ADMIN:
        flash("Verrouillé par l'Admin.")
        return redirect(url_for('dashboard.index'))

    if not status["running"]:
        choice = request.form.get("choice")
        p = os.path.join(BOTS_DIR, choice)

        if user['role'] != ROLE_ADMIN and get_script_status(choice) == 0:
            flash("Ce script a été désactivé par l'administrateur.")
            return redirect(url_for('dashboard.index'))

        if os.path.exists(p):
            cmd_args = []
            if "portal.py" in choice or choice == "Portail":
                arg_lang = request.form.get("arg_lang")
                arg_cat = request.form.get("arg_cat")
                arg_portal = request.form.get("arg_portal")
                if not (arg_lang and arg_cat and arg_portal):
                    return redirect(url_for('dashboard.index'))
                cmd_args = ["--lang", arg_lang, "--cat", arg_cat, "--portal", arg_portal]

            launch_script_core(choice, p, args=cmd_args, user_name=session.get('username'))
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
        u = db.execute("SELECT role FROM users WHERE github_id=?", (session['user_id'],)).fetchone()
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
