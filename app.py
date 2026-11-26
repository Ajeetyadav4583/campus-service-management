from flask import Flask, request, jsonify, render_template
from database import get_db_connection
from werkzeug.security import generate_password_hash

app = Flask(__name__)

DEMO_EMAIL = "demo.student@campus.local"
STATUS_FLOW = ["pending", "in_progress", "completed"]


# ---------------- DATABASE SETUP ----------------

def setup_database():
    db = get_db_connection()
    cursor = db.cursor()

    # Add sample services only if table is empty
    cursor.execute("SELECT COUNT(*) FROM services")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_services = [
            ("IT Support", "Computer, Wi-Fi and technical issue assistance.", "Technology"),
            ("ID Card Service", "Apply for a new or replacement college ID card.", "Student Services"),
            ("Campus Maintenance", "Report classroom, furniture or facility issues.", "Facilities"),
            ("Library Support", "Get help with library access and books.", "Academics"),
        ]
        cursor.executemany(
            """INSERT INTO services (name, description, category)
               VALUES (%s, %s, %s)""",
            sample_services,
        )

    # Create demo student if not already present
    cursor.execute("SELECT id FROM users WHERE email = %s", (DEMO_EMAIL,))
    if cursor.fetchone() is None:
        cursor.execute(
            """INSERT INTO users (name, email, password, role)
               VALUES (%s, %s, %s, %s)""",
            ("Demo Student", DEMO_EMAIL,
             generate_password_hash("DemoPassword123!"), "student"),
        )

    db.commit()
    cursor.close()
    db.close()


# ---------------- PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- API ----------------

@app.route("/api/services", methods=["GET"])
def api_services():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, name, description, category
            FROM services
            WHERE status = 'active'
            ORDER BY id
        """)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        db.close()


@app.route("/api/requests", methods=["GET"])
def api_requests():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, service_id, title, description, status, created_at
            FROM service_requests
            ORDER BY id DESC
        """)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        db.close()


@app.route("/api/requests", methods=["POST"])
def api_create_request():
    data = request.get_json(silent=True) or {}
    service_id = data.get("service_id")
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()

    if not service_id or not title:
        return jsonify(error="Service and title are required."), 400

    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (DEMO_EMAIL,))
        user = cursor.fetchone()

        cursor.execute(
            "SELECT id FROM services WHERE id = %s AND status = 'active'",
            (service_id,),
        )
        service = cursor.fetchone()

        if not user or not service:
            return jsonify(error="User or service not found."), 400

        cursor.execute(
            """INSERT INTO service_requests (user_id, service_id, title, description)
               VALUES (%s, %s, %s, %s)""",
            (user[0], service[0], title[:150], description[:2000]),
        )
        request_id = cursor.lastrowid
        db.commit()
        return jsonify(ok=True, id=request_id), 201
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


@app.route("/api/requests/<int:req_id>/advance", methods=["PATCH"])
def api_advance_request(req_id):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT status FROM service_requests WHERE id = %s", (req_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify(error="Request not found."), 404

        current = row[0]
        if current not in STATUS_FLOW or current == STATUS_FLOW[-1]:
            return jsonify(ok=True, status=current)

        new_status = STATUS_FLOW[STATUS_FLOW.index(current) + 1]
        cursor.execute(
            "UPDATE service_requests SET status = %s WHERE id = %s",
            (new_status, req_id),
        )
        db.commit()
        return jsonify(ok=True, status=new_status)
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    setup_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
