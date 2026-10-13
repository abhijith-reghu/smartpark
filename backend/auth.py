from functools import wraps
from flask import session, jsonify
from werkzeug.security import check_password_hash
from database import get_db_connection


def verify_login(username, password):
    """Returns staff row if credentials are valid, else None."""
    conn = get_db_connection()
    staff = conn.execute(
        "SELECT * FROM staff WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if staff and check_password_hash(staff["password_hash"], password):
        return staff
    return None


def login_required(f):
    """Decorator to protect staff-only routes later on."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "staff_id" not in session:
            return jsonify({"success": False, "error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated