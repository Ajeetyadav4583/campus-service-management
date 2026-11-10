

from flask import Flask, request, redirect, url_for, render_template_string
from database import get_db_connection
from werkzeug.security import generate_password_hash

app = Flask(__name__)


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
            ("Library Support", "Get help with library access and books.", "Academics")
        ]

        cursor.executemany(
            """INSERT INTO services (name, description, category)
               VALUES (%s, %s, %s)""",
            sample_services
        )

    # Create demo student if not already present
    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        ("demo.student@campus.local",)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            """INSERT INTO users (name, email, password, role)
               VALUES (%s, %s, %s, %s)""",
            (
                "Demo Student",
                "demo.student@campus.local",
                generate_password_hash("DemoPassword123!"),
                "student"
            )
        )

    db.commit()
    cursor.close()
    db.close()


# ---------------- GET DASHBOARD DATA ----------------

def get_dashboard_data():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, description, category
        FROM services
        WHERE status = 'active'
        ORDER BY id
    """)
    services = cursor.fetchall()

    cursor.execute("""
        SELECT
            sr.id,
            u.name AS student,
            s.name AS service,
            sr.title,
            CASE
                WHEN sr.status = 'pending' THEN 'Pending'
                WHEN sr.status = 'in_progress' THEN 'In Progress'
                WHEN sr.status = 'completed' THEN 'Completed'
                WHEN sr.status = 'rejected' THEN 'Rejected'
                ELSE sr.status
            END AS status,
            sr.created_at
        FROM service_requests sr
        JOIN users u ON sr.user_id = u.id
        JOIN services s ON sr.service_id = s.id
        ORDER BY sr.id DESC
    """)

    requests_data = cursor.fetchall()

    cursor.close()
    db.close()

    return services, requests_data


# ---------------- WEBSITE DESIGN ----------------

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CampusCare | Service Management</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Segoe UI", Arial, sans-serif;
    background: #f4f6fb;
    color: #202b40;
}

.layout { display: flex; min-height: 100vh; }

aside {
    width: 235px;
    background: #14213d;
    color: white;
    padding: 28px 18px;
    flex-shrink: 0;
}

.brand { font-size: 23px; font-weight: 800; }
.brand span { color: #91b4ff; }

.tagline {
    font-size: 12px;
    color: #bac6dd;
    margin-top: 8px;
    margin-bottom: 38px;
}

.navtitle {
    font-size: 10px;
    letter-spacing: 2px;
    color: #9aa9c6;
    margin: 22px 10px 12px;
}

.nav {
    padding: 13px 12px;
    border-radius: 10px;
    margin: 6px 0;
    color: #dce4f4;
    font-size: 14px;
}

.nav.active { background: #3157d5; }

.aside-note {
    font-size: 12px;
    color: #bac6dd;
    line-height: 1.7;
    margin-top: 50px;
    border-top: 1px solid #35415a;
    padding-top: 20px;
}

main {
    flex: 1;
    min-width: 0;
    padding: 28px 34px 45px;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}

.eyebrow { color: #758198; font-size: 12px; }
h1 { font-size: 27px; margin: 6px 0; }
.subtitle { color: #758198; font-size: 14px; }

.profile {
    background: white;
    padding: 10px 14px;
    border-radius: 12px;
    border: 1px solid #e8ebf3;
    font-size: 13px;
}

.hero {
    padding: 27px 30px;
    border-radius: 18px;
    color: white;
    background: linear-gradient(120deg,#243e8e,#4777ec);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 24px;
}

.hero h2 { margin: 7px 0; font-size: 25px; }
.hero p { color: #e1eaff; font-size: 14px; line-height: 1.6; }
.hero .symbol { font-size: 55px; }

.hero a {
    display: inline-block;
    padding: 11px 16px;
    border-radius: 9px;
    background: white;
    color: #2345ac;
    font-size: 13px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 6px;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3,minmax(0,1fr));
    gap: 15px;
    margin-bottom: 29px;
}

.stat, .panel, .service {
    background: white;
    border: 1px solid #e8ebf3;
    border-radius: 15px;
}

.stat { padding: 19px; }
.stat-label { color: #758198; font-size: 12px; }
.stat-number { font-size: 28px; font-weight: 750; margin-top: 10px; }

.sectionhead {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 27px 0 15px;
}

h3 { margin: 0; font-size: 18px; }
.sectionhead small { color: #758198; }

.services {
    display: grid;
    grid-template-columns: repeat(2,minmax(0,1fr));
    gap: 15px;
}

.service { padding: 19px; }
.service-icon { font-size: 27px; }
.service h4 { margin: 12px 0 8px; font-size: 16px; }

.service p {
    color: #758198;
    font-size: 13px;
    line-height: 1.6;
    min-height: 40px;
}

.category {
    display: inline-block;
    background: #eef2ff;
    color: #3157d5;
    padding: 5px 9px;
    border-radius: 6px;
    font-size: 11px;
}

.panel { padding: 20px; margin-top: 18px; }

.formgrid {
    display: grid;
    grid-template-columns: repeat(2,minmax(0,1fr));
    gap: 14px;
}

label {
    display: block;
    font-size: 12px;
    font-weight: 650;
    margin-bottom: 7px;
}

input, select, textarea {
    width: 100%;
    padding: 11px 12px;
    border: 1px solid #dfe4ee;
    border-radius: 9px;
    font: inherit;
    font-size: 13px;
    background: white;
}

textarea { min-height: 85px; resize: vertical; }
.full { grid-column: 1 / -1; }

.btn {
    background: #3157d5;
    color: white;
    border: 0;
    padding: 12px 17px;
    border-radius: 9px;
    font-weight: 650;
    cursor: pointer;
}

table { width: 100%; border-collapse: collapse; font-size: 13px; }

th {
    text-align: left;
    font-size: 11px;
    color: #758198;
    padding: 12px 8px;
    border-bottom: 1px solid #e8ebf3;
}

td {
    padding: 14px 8px;
    border-bottom: 1px solid #e8ebf3;
}

.status {
    display: inline-block;
    padding: 6px 9px;
    border-radius: 20px;
    font-size: 11px;
    background: #fff4d9;
    color: #946200;
}

.status.done { background: #dcfce7; color: #166534; }
.status.progress { background: #e5edff; color: #244cc4; }

.flash {
    background: #dcfce7;
    color: #166534;
    padding: 12px;
    border-radius: 9px;
    margin-bottom: 18px;
    font-size: 13px;
}

footer {
    text-align: center;
    padding: 28px 0 0;
    font-size: 11px;
    color: #758198;
}

@media(max-width:850px) {
    aside { width: 180px; }
    main { padding: 22px 18px; }
}

@media(max-width:620px) {
    .layout { display: block; }
    aside { width: 100%; padding: 18px; }
    .tagline, .navtitle, .aside-note { display: none; }
    .nav { display: inline-block; margin: 10px 3px 0 0; }
    .stats { grid-template-columns: 1fr; }
    .services, .formgrid { grid-template-columns: 1fr; }
    .full { grid-column: auto; }
    .hero .symbol { display: none; }
    table { min-width: 530px; }
    .panel { overflow-x: auto; }
}
</style>
</head>

<body>
<div class="layout">

<aside>
    <div class="brand">Campus<span>Care</span></div>
    <div class="tagline">CAMPUS SERVICE PORTAL</div>

    <div class="navtitle">WORKSPACE</div>
    <div class="nav active">▦ &nbsp; Dashboard</div>
    <div class="nav">▤ &nbsp; Campus Services</div>
    <div class="nav">◷ &nbsp; My Requests</div>

    <div class="navtitle">INFORMATION</div>
    <div class="nav">ⓘ &nbsp; Help & Support</div>

    <div class="aside-note">
        One portal for campus needs.<br>
        Simple. Transparent. Efficient.
    </div>
</aside>

<main>

    <div class="topbar">
        <div>
            <div class="eyebrow">CAMPUS SERVICE MANAGEMENT SYSTEM</div>
            <h1>Dashboard</h1>
            <div class="subtitle">
                Manage campus services and track requests in one place.
            </div>
        </div>
        <div class="profile">👤 &nbsp; Student Portal</div>
    </div>

    {% if message %}
        <div class="flash">{{ message }}</div>
    {% endif %}

    <section class="hero">
        <div>
            <div style="font-size:12px;color:#dce7ff">
                WELCOME TO CAMPUSCARE
            </div>
            <h2>Your campus, made easier.</h2>
            <p>
                Access student services, submit a request and track its progress
                through a single, easy-to-use portal.
            </p>
            <a href="#new-request">＋ Submit a Request</a>
        </div>
        <div class="symbol">🎓</div>
    </section>

    <section class="stats">
        <div class="stat">
            <div class="stat-label">AVAILABLE SERVICES</div>
            <div class="stat-number">{{ services|length }}</div>
        </div>

        <div class="stat">
            <div class="stat-label">TOTAL REQUESTS</div>
            <div class="stat-number">{{ requests|length }}</div>
        </div>

        <div class="stat">
            <div class="stat-label">COMPLETED REQUESTS</div>
            <div class="stat-number">
                {{ requests|selectattr('status','equalto','Completed')|list|length }}
            </div>
        </div>
    </section>

    <div class="sectionhead">
        <h3>Explore Campus Services</h3>
        <small>Services directory</small>
    </div>

    <section class="services">
        {% for service in services %}
        <article class="service">
            <div class="service-icon">
                {% if service.category == 'Technology' %}💻
                {% elif service.category == 'Student Services' %}🪪
                {% elif service.category == 'Facilities' %}🛠️
                {% else %}📚{% endif %}
            </div>

            <h4>{{ service.name }}</h4>
            <span class="category">{{ service.category }}</span>
            <p>{{ service.description }}</p>

            <a href="#new-request"
               style="color:#3157d5;text-decoration:none;font-size:13px;font-weight:700">
                Request service →
            </a>
        </article>
        {% else %}
        <p>No active services available.</p>
        {% endfor %}
    </section>

    <section class="panel" id="new-request">
        <div class="sectionhead" style="margin-top:0">
            <h3>Submit a Service Request</h3>
            <small>New request form</small>
        </div>

        <form method="POST" action="{{ url_for('create_request') }}">
            <div class="formgrid">

                <div>
                    <label for="student">Student Name</label>
                    <input id="student" name="student" required maxlength="80"
                           placeholder="Enter your name">
                </div>

                <div>
                    <label for="service">Select Service</label>
                    <select id="service" name="service" required>
                        {% for s in services %}
                        <option value="{{ s.name }}">{{ s.name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="full">
                    <label for="title">Request Title</label>
                    <input id="title" name="title" required maxlength="150"
                           placeholder="Briefly describe your issue">
                </div>

                <div class="full">
                    <label for="description">Description</label>
                    <textarea id="description" name="description" maxlength="2000"
                              placeholder="Provide details about your request"></textarea>
                </div>

                <div class="full">
                    <button class="btn" type="submit">
                        Submit Request →
                    </button>
                </div>

            </div>
        </form>
    </section>

    <section class="panel">
        <div class="sectionhead" style="margin-top:0">
            <h3>Recent Service Requests</h3>
            <small>Database records</small>
        </div>

        <table>
            <thead>
                <tr>
                    <th>REQUEST ID</th>
                    <th>STUDENT</th>
                    <th>SERVICE</th>
                    <th>TITLE</th>
                    <th>STATUS</th>
                </tr>
            </thead>

            <tbody>
                {% for r in requests %}
                <tr>
                    <td>#{{ r.id }}</td>
                    <td>{{ r.student }}</td>
                    <td>{{ r.service }}</td>
                    <td>{{ r.title }}</td>
                    <td>
                        <span class="status
                            {% if r.status == 'Completed' %}done
                            {% elif r.status == 'In Progress' %}progress
                            {% endif %}">
                            {{ r.status }}
                        </span>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5">No requests yet.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </section>

    <footer>
        CampusCare · Campus Service Management System · Academic Project
    </footer>

</main>
</div>
</body>
</html>
"""


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    try:
        setup_database()
        services, requests_data = get_dashboard_data()

        return render_template_string(
            PAGE,
            services=services,
            requests=requests_data,
            message=request.args.get("message", "")
        )

    except Exception as error:
        return f"Database error: {error}", 500


# ---------------- CREATE REQUEST ----------------

@app.route("/request", methods=["POST"])
def create_request():

    student = request.form.get("student", "").strip()
    service = request.form.get("service", "").strip()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not student or not service or not title:
        return "Please fill all required fields.", 400

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            ("demo.student@campus.local",)
        )
        user = cursor.fetchone()

        cursor.execute(
            "SELECT id FROM services WHERE name = %s AND status = 'active'",
            (service,)
        )
        selected_service = cursor.fetchone()

        if not user or not selected_service:
            return "User or service not found.", 400

        cursor.execute("""
            INSERT INTO service_requests
            (user_id, service_id, title, description)
            VALUES (%s, %s, %s, %s)
        """, (user[0], selected_service[0], title, description))

        request_id = cursor.lastrowid
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()
        db.close()

    return redirect(url_for(
        "home",
        message=f"Request #{request_id} submitted successfully!"
    ))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
