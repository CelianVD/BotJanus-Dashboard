import os
import io
import csv
from datetime import datetime, timedelta

from flask import Blueprint, render_template_string, redirect, url_for, request, session, flash, Response

from flask_app import ROLE_NONE, ROLE_COLLAB, ROLE_ADMIN, BOTS_DIR, get_db, check_role, get_all_bots, launch_script_core
from templates import (GLASS_CSS, ADMIN_SCRIPTS_HTML, SCRIPT_EDITOR_HTML, SCHEDULES_HTML,
                        STATS_HTML, ADMIN_USERS_HTML, SETTINGS_HTML)

admin_bp = Blueprint("admin", __name__)


# ============ UTILISATEURS & RÔLES ============

@admin_bp.route("/admin/users")
@check_role([ROLE_ADMIN])
def admin_users():
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY is_banned ASC, role DESC").fetchall()
    return render_template_string(ADMIN_USERS_HTML, users=users, glass_css=GLASS_CSS, active='users')


@admin_bp.route("/admin/update_user", methods=['POST'])
@check_role([ROLE_ADMIN])
def admin_update_user():
    target_id = request.form.get('github_id')
    new_role = request.form.get('new_role')
    action = request.form.get('action')
    reason = request.form.get('reason')

    if target_id == session['user_id']:
        return redirect(url_for('admin.admin_users'))
    db = get_db()
    if action == 'ban':
        db.execute("UPDATE users SET is_banned = 1, ban_reason = ? WHERE github_id = ?", (reason, target_id))
    elif action == 'update' and new_role in [ROLE_NONE, ROLE_COLLAB, ROLE_ADMIN]:
        db.execute("UPDATE users SET role = ? WHERE github_id = ?", (new_role, target_id,))
    db.commit()
    return redirect(url_for('admin.admin_users'))


# ============ SAUVEGARDE / RESTAURATION ============

@admin_bp.route("/admin/backup/export")
@check_role([ROLE_ADMIN])
def backup_export():
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['github_id', 'username', 'avatar', 'role', 'is_banned', 'lang', 'ban_reason'])
    for u in users:
        cw.writerow([u['github_id'], u['username'], u['avatar'], u['role'], u['is_banned'], u['lang'], u['ban_reason']])
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=backup_users_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@admin_bp.route("/admin/backup/import", methods=["POST"])
@check_role([ROLE_ADMIN])
def backup_import():
    if 'backup_file' not in request.files:
        flash("Fichier manquant.")
        return redirect(url_for('admin.settings'))
    file = request.files['backup_file']
    if file.filename == '':
        return redirect(url_for('admin.settings'))
    try:
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        reader = csv.reader(stream, delimiter=';')
        next(reader)  # Sauter l'entête
        db = get_db()
        count = 0
        for row in reader:
            if len(row) >= 6:
                db.execute("""INSERT OR REPLACE INTO users (github_id, username, avatar, role, is_banned, lang, ban_reason)
                              VALUES (?, ?, ?, ?, ?, ?, ?)""",
                           (row[0], row[1], row[2], row[3], int(row[4]), row[5], row[6] if len(row) > 6 else ""))
                count += 1
        db.commit()
        flash(f"Restauration terminée : {count} profils importés.")
    except Exception as e:
        flash(f"Erreur d'importation : {str(e)}")
    return redirect(url_for('admin.settings'))


# ============ GESTION DES SCRIPTS ============

@admin_bp.route("/admin/scripts")
@check_role([ROLE_ADMIN])
def admin_scripts():
    scripts = get_all_bots()
    configs = {}
    db = get_db()
    rows = db.execute("SELECT filename, is_active FROM script_config").fetchall()
    for r in rows:
        configs[r['filename']] = r['is_active']
    return render_template_string(ADMIN_SCRIPTS_HTML, scripts=scripts, configs=configs, glass_css=GLASS_CSS, active='scripts')


@admin_bp.route("/admin/scripts/create", methods=["POST"])
@check_role([ROLE_ADMIN])
def admin_create_script():
    filename = request.form.get("filename", "").strip()
    if not filename.endswith(".py"):
        filename += ".py"
    if len(filename) > 4:
        p = os.path.join(BOTS_DIR, filename)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write("#!/usr/bin/env python3\nprint('Nouveau script bot.')\n")
            flash("Fichier script créé.")
    return redirect(url_for('admin.admin_scripts'))


@admin_bp.route("/admin/scripts/edit/<filename>")
@check_role([ROLE_ADMIN])
def admin_edit_script_page(filename):
    p = os.path.join(BOTS_DIR, filename)
    content = ""
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
    return render_template_string(SCRIPT_EDITOR_HTML, filename=filename, content=content, glass_css=GLASS_CSS)


@admin_bp.route("/admin/scripts/save", methods=["POST"])
@check_role([ROLE_ADMIN])
def admin_save_script():
    filename = request.form.get("filename")
    content = request.form.get("content")
    p = os.path.join(BOTS_DIR, filename)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    flash("Fichier modifié avec succès.")
    return redirect(url_for('admin.admin_edit_script_page', filename=filename))


@admin_bp.route("/admin/scripts/toggle", methods=["POST"])
@check_role([ROLE_ADMIN])
def admin_toggle_script():
    filename = request.form.get("filename")
    current_val = int(request.form.get("current_val", 1))
    new_val = 0 if current_val == 1 else 1
    db = get_db()
    db.execute("INSERT OR REPLACE INTO script_config (filename, is_active) VALUES (?, ?)", (filename, new_val))
    db.commit()
    return redirect(url_for('admin.admin_scripts'))


@admin_bp.route("/admin/scripts/run", methods=["POST"])
@check_role([ROLE_ADMIN])
def admin_run_script_direct():
    filename = request.form.get("filename")
    p = os.path.join(BOTS_DIR, filename)
    if os.path.exists(p):
        if launch_script_core(filename, p, user_name=f"{session.get('username')} (Zone Admin)"):
            flash("Script initié en arrière-plan.")
        else:
            flash("Erreur : Un processus est déjà actif.")
    return redirect(url_for('dashboard.index'))


# ============ PLANIFICATION ============

@admin_bp.route("/admin/schedules", methods=["GET", "POST"])
@check_role([ROLE_ADMIN])
def admin_schedules():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = request.form.get("script_name")
            freq = request.form.get("frequency")
            val = int(request.form.get("time_value", 30))
            next_time = datetime.now() + timedelta(minutes=1)
            db.execute("INSERT INTO schedules (script_name, frequency, time_value, last_run, next_run) VALUES (?, ?, ?, 'Jamais', ?)",
                       (name, freq, val, next_time.strftime("%Y-%m-%d %H:%M:%S")))
            db.commit()
        elif action == "delete":
            db.execute("DELETE FROM schedules WHERE id = ?", (request.form.get("id"),))
            db.commit()
        return redirect(url_for('admin.admin_schedules'))

    schedules = db.execute("SELECT * FROM schedules").fetchall()
    return render_template_string(SCHEDULES_HTML, schedules=schedules, scripts=get_all_bots(), glass_css=GLASS_CSS, active='schedules')


# ============ STATISTIQUES ============

@admin_bp.route("/admin/stats")
@check_role([ROLE_ADMIN])
def admin_stats():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_logs = db.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    script_counts = db.execute("SELECT script, COUNT(*) as cnt FROM logs GROUP BY script ORDER BY cnt DESC").fetchall()
    return render_template_string(STATS_HTML, total_users=total_users, total_logs=total_logs,
                                   script_counts=script_counts, glass_css=GLASS_CSS, active='stats')


# ============ PARAMÈTRES SYSTÈME & LOGS ============

@admin_bp.route("/settings")
@check_role([ROLE_ADMIN])
def settings():
    db = get_db()
    row_lock = db.execute("SELECT value FROM settings WHERE key='lock_launch'").fetchone()
    locked = row_lock['value'] if row_lock else '0'
    row_cap = db.execute("SELECT value FROM settings WHERE key='captcha_enabled'").fetchone()
    captcha_enabled = row_cap['value'] if row_cap else '0'
    total_logs = db.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    return render_template_string(SETTINGS_HTML, locked=locked, captcha_enabled=captcha_enabled,
                                   total_logs=total_logs, glass_css=GLASS_CSS, active='settings')


@admin_bp.route('/update_settings', methods=['POST'])
@check_role([ROLE_ADMIN])
def update_settings():
    db = get_db()
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('lock_launch', request.form.get('lock_launch', '0')))
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('captcha_enabled', request.form.get('captcha_enabled', '0')))
    db.commit()
    flash("Paramètres enregistrés.")
    return redirect(url_for('admin.settings'))


@admin_bp.route('/admin/clean_logs_manual', methods=['POST'])
@check_role([ROLE_ADMIN])
def clean_logs_manual():
    """Supprime les logs plus anciens que X jours (nettoyage ciblé)."""
    try:
        days = request.form.get('days', type=int)
        if days is not None and days >= 0:
            limit_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            db = get_db()
            db.execute("DELETE FROM logs WHERE date < ?", (limit_date,))
            db.commit()
            flash(f"Logs plus anciens que {days} jours supprimés avec succès.")
        else:
            flash("Veuillez entrer un nombre de jours valide.")
    except Exception as e:
        flash(f"Erreur lors de la suppression : {str(e)}")
    return redirect(url_for('admin.settings'))


@admin_bp.route('/admin/logs/delete_all', methods=['POST'])
@check_role([ROLE_ADMIN])
def delete_all_logs():
    """Supprime TOUS les logs immédiatement. Remplace l'ancienne suppression automatique."""
    try:
        db = get_db()
        db.execute("DELETE FROM logs")
        db.commit()
        flash("Tous les logs ont été supprimés avec succès.")
    except Exception as e:
        flash(f"Erreur lors de la suppression des logs : {str(e)}")
    return redirect(url_for('admin.settings'))
