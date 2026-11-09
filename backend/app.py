import base64
from datetime import datetime, timedelta
from ipaddress import ip_address
from urllib.parse import urlsplit

import qrcode
from qrcode.image.svg import SvgPathFillImage
from pathlib import Path

from flask import Flask, request, jsonify, session, render_template, redirect
from flask_cors import CORS
from config import SECRET_KEY
from auth import verify_login, login_required
from database import get_db_connection, initialize_database


# SmartPark/frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(__name__, template_folder=str(FRONTEND_DIR))
CORS(app, supports_credentials=True)
app.secret_key = SECRET_KEY
initialize_database()

#-----------new addedd----
def entrance_qr():
    """
    Create a QR pointing to the driver page.

    Use the address that opened the entrance display.
    Do not generate a QR for localhost because phones
    cannot use localhost to reach this computer.
    """
    host = urlsplit(request.host_url).hostname or ""

    try:
        address = ip_address(host)
        local_only = address.is_loopback or address.is_unspecified
    except ValueError:
        local_only = (
            host == "localhost"
            or host.endswith(".localhost")
        )

    if local_only:
        return "", ""

    destination = request.host_url.rstrip("/") + "/driver"

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(destination)
    qr.make(fit=True)

    image = qr.make_image(image_factory=SvgPathFillImage)
    encoded = base64.b64encode(
        image.to_string()
    ).decode("ascii")

    qr_image = "data:image/svg+xml;base64," + encoded

    return destination, qr_image


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
    destination, qr_image = entrance_qr()

    return render_template(
        "entrance-display/entrance_display.html",
        driver_mode=False,
        destination=destination,
        qr_image=qr_image,
    )


@app.route("/driver")
def driver_page():
    return render_template(
        "entrance-display/entrance_display.html",
        driver_mode=True,
    )


@app.route("/dashboard")
@app.route("/dashboard/index.html")
@app.route("/dashboard/dashboard.html")
def dashboard_page():
    if "staff_id" not in session:
        return redirect("/login")
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
               sections.direction,
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

    # A slot marked occupied must no longer remain reserved for a driver.
    if data["status"] == "occupied":
        conn.execute(
            "DELETE FROM reservations WHERE slot_id = ?",
            (slot["slot_id"],)
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


# ---------- DRIVER RESERVATIONS ----------

@app.route("/api/reserve", methods=["GET"])
def reserve_slot():
    driver_id = session.get("driver_id")

    if not driver_id:
        import uuid
        driver_id = str(uuid.uuid4())
        session["driver_id"] = driver_id

    conn = get_db_connection()

    try:
        # Lock the database while assigning a slot.
        conn.execute("BEGIN IMMEDIATE")

        # Remove expired reservations.
        conn.execute("""
            DELETE FROM reservations
            WHERE expires_at <= CURRENT_TIMESTAMP
        """)

        # Check whether this driver already has a reservation.
        existing = conn.execute("""
            SELECT parking_slots.slot_code,
                   sections.name AS section,
                   sections.direction
            FROM reservations
            JOIN parking_slots
                ON reservations.slot_id = parking_slots.slot_id
            JOIN sections
                ON parking_slots.section_id = sections.section_id
            WHERE reservations.driver_id = ?
              AND parking_slots.status = 'available'
              AND reservations.expires_at > CURRENT_TIMESTAMP
        """, (driver_id,)).fetchone()

        # Clear expired or no-longer-valid reservations for this driver.
        if not existing:
            conn.execute("""
                DELETE FROM reservations
                WHERE driver_id = ?
                   OR expires_at <= CURRENT_TIMESTAMP
            """, (driver_id,))

        if existing:
            conn.commit()
            return jsonify({
                "success": True,
                "recommended_slot": existing["slot_code"],
                "section": existing["section"],
                "direction": existing["direction"],
                "reserved": True
            })

        # Find the nearest available slot that is not reserved.
        slot = conn.execute("""
            SELECT parking_slots.slot_id,
                   parking_slots.slot_code,
                   sections.name AS section,
                   sections.direction
            FROM parking_slots
            JOIN sections
                ON parking_slots.section_id = sections.section_id
            WHERE parking_slots.status = 'available'
              AND parking_slots.slot_id NOT IN (
                  SELECT slot_id FROM reservations
              )
            ORDER BY parking_slots.distance_from_entrance ASC
            LIMIT 1
        """).fetchone()

        if not slot:
            conn.commit()
            return jsonify({
                "success": False,
                "recommended_slot": None,
                "message": "No parking slots available"
            })

        # Reserve the slot for 10 minutes.
        conn.execute("""
            INSERT INTO reservations
                (slot_id, driver_id, expires_at)
            VALUES (
                ?,
                ?,
                datetime('now', '+10 minutes')
            )
        """, (slot["slot_id"], driver_id))

        conn.commit()

        return jsonify({
            "success": True,
            "recommended_slot": slot["slot_code"],
            "section": slot["section"],
            "direction": slot["direction"],
            "reserved": True
        })

    except Exception:
        conn.rollback()
        app.logger.exception("Could not reserve parking slot")
        return jsonify({
            "success": False,
            "message": "Unable to reserve a parking slot"
        }), 500

    finally:
        conn.close()


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
            AND NOT EXISTS (
                SELECT 1
                FROM reservations
                WHERE reservations.slot_id = parking_slots.slot_id
                  AND reservations.expires_at > CURRENT_TIMESTAMP
           )
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
    app.run(host="0.0.0.0", port=5000, debug=False)