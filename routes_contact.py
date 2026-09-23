from datetime import datetime

from flask import Blueprint, render_template_string, redirect, url_for, request, session, flash

from flask_app import ROLE_ADMIN, get_db, login_required, check_role
from templates import GLASS_CSS, CONTACT_HTML, ADMIN_MESSAGES_HTML

contact_bp = Blueprint("contact", __name__)


@contact_bp.route("/contact", methods=["GET", "POST"])
@login_required
def contact_form():
    if request.method == "POST":
        content = (request.form.get("content") or "").strip()
        if not content:
            flash("Le message ne peut pas être vide.")
            return redirect(url_for('contact.contact_form'))

        db = get_db()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO messages (wiki_id, username, content, date, is_read) VALUES (?, ?, ?, ?, 0)",
            (session.get('user_id'), session.get('username'), content, timestamp)
        )
        db.commit()
        flash("Votre message a bien été envoyé à l'administrateur. Merci !")
        return redirect(url_for('dashboard.index'))

    return render_template_string(CONTACT_HTML, glass_css=GLASS_CSS)


@contact_bp.route("/admin/messages")
@check_role([ROLE_ADMIN])
def admin_messages():
    db = get_db()
    msgs = db.execute("SELECT * FROM messages ORDER BY is_read ASC, id DESC").fetchall()
    return render_template_string(ADMIN_MESSAGES_HTML, msgs=msgs, glass_css=GLASS_CSS, active='messages')


@contact_bp.route("/admin/messages/<int:message_id>/read", methods=["POST"])
@check_role([ROLE_ADMIN])
def mark_read(message_id):
    db = get_db()
    db.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (message_id,))
    db.commit()
    return redirect(url_for('contact.admin_messages'))


@contact_bp.route("/admin/messages/<int:message_id>/delete", methods=["POST"])
@check_role([ROLE_ADMIN])
def delete_message(message_id):
    db = get_db()
    db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    db.commit()
    flash("Message supprimé.")
    return redirect(url_for('contact.admin_messages'))
