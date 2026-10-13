from pathlib import Path

from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from config import SECRET_KEY
from auth import verify_login, login_required
from database import get_db_connection


# SmartPark/frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(__name__, template_folder=str(FRONTEND_DIR))
CORS(app, supports_credentials=True)
app.secret_key = SECRET_KEY


# ---------- PAGE ROUTES ----------

@app.route("/")
@app.route("/login")
@app.route("/login/index.html")
@app.route("/login/login.html")
def login_page():
    return render_template("login/login.html")


@app.route("/staff-panel")
@app.route("/staff-panel/index.html")
@app.route("/staff_panel/index.html")
@app.route("/staff-panel/staff-panel.html")
@login_required
def staff_panel_page():
    return render_template("staff-panel/staff-panel.html")


@app.route("/entrance-display")
@app.route("/entrance-display/index.html")
@app.route("/entrance-display/entrance_display.html")
def entrance_display_page():
    return render_template("entrance-display/entrance_display.html")


@app.route("/dashboard")
@app.route("/dashboard/index.html")
@app.route("/dashboard/dashboard.html")
def dashboard_page():
    return render_template("dashboard/dashboard.html")


# ---------- LOGIN AND LOGOUT ----------

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "username" not in data or "password" not in data:
        return jsonify({
            "success": False,
            "error": "username and password required"
        }), 400

    staff = verify_login(data["username"], data["password"])

    if not staff:
        return jsonify({
            "success": False,
            "error": "Invalid username or password"
        }), 401

    session["staff_id"] = staff["staff_id"]
    session["full_name"] = staff["full_name"]

    return jsonify({
        "success": True,
        "staff_id": staff["staff_id"],
        "full_name": staff["full_name"]
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# ---------- PARKING SLOTS ----------

@app.route("/api/slots", methods=["GET"])
def get_slots():
    conn = get_db_connection()

    slots = conn.execute("""
        SELECT parking_slots.slot_code,
               parking_slots.status,
               sections.name AS section,
               parking_slots.last_updated
        FROM parking_slots
        JOIN sections
            ON parking_slots.section_id = sections.section_id
        ORDER BY parking_slots.slot_code
    """).fetchall()

    conn.close()

    return jsonify({"slots": [dict(row) for row in slots]})


@app.route("/api/slots/<slot_code>/update", methods=["POST"])
@login_required
def update_slot(slot_code):
    data = request.get_json()

    if (
        not data
        or "status" not in data
        or data["status"] not in ("available", "occupied")
    ):
        return jsonify({
            "success": False,
            "error": "status must be 'available' or 'occupied'"
        }), 400

    conn = get_db_connection()

    slot = conn.execute(
        "SELECT * FROM parking_slots WHERE slot_code = ?",
        (slot_code,)
    ).fetchone()

    if not slot:
        conn.close()
        return jsonify({
            "success": False,
            "error": f"slot_code '{slot_code}' not found"
        }), 404

    conn.execute(
        """
        UPDATE parking_slots
        SET status = ?, last_updated = CURRENT_TIMESTAMP
        WHERE slot_code = ?
        """,
        (data["status"], slot_code)
    )

    event_type = (
        "occupied" if data["status"] == "occupied" else "vacated"
    )

    conn.execute(
        """
        INSERT INTO parking_events (slot_id, event_type, changed_by)
        VALUES (?, ?, ?)
        """,
        (slot["slot_id"], event_type, session["staff_id"])
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "slot_code": slot_code,
        "status": data["status"]
    })


# ---------- PARKING RECOMMENDATION ----------

@app.route("/api/recommendation", methods=["GET"])
def get_recommendation():
    conn = get_db_connection()

    slot = conn.execute("""
        SELECT parking_slots.slot_code,
               sections.name AS section,
               sections.direction
        FROM parking_slots
        JOIN sections
            ON parking_slots.section_id = sections.section_id
        WHERE parking_slots.status = 'available'
        ORDER BY parking_slots.distance_from_entrance ASC
        LIMIT 1
    """).fetchone()

    conn.close()

    if not slot:
        return jsonify({
            "recommended_slot": None,
            "message": "Parking full"
        })

    return jsonify({
        "recommended_slot": slot["slot_code"],
        "section": slot["section"],
        "direction": slot["direction"]
    })


# ---------- PARKING STATISTICS ----------

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db_connection()

    counts = conn.execute("""
        SELECT COUNT(*) AS total,
               SUM(
                   CASE WHEN status = 'available' THEN 1 ELSE 0 END
               ) AS available,
               SUM(
                   CASE WHEN status = 'occupied' THEN 1 ELSE 0 END
               ) AS occupied
        FROM parking_slots
    """).fetchone()

    conn.close()

    return jsonify({
        "total": counts["total"],
        "available": counts["available"],
        "occupied": counts["occupied"]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)