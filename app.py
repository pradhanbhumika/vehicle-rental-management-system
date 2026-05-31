from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "rental_secret_key_2024"

# ─────────────────────────────────────
#  DATABASE CONNECTION
# ─────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # change if needed
        password="whatsup03",        # change to your MySQL password
        database="rental_db"
    )

def is_admin():
    return session.get("admin") is True

def parse_date(s):
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except Exception:
        return None

# ─────────────────────────────────────
#  HOME PAGE  (public, no login)
# ─────────────────────────────────────
@app.route("/")
def home():
    try:
        conn   = get_db()
        cur    = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM vehicles ORDER BY type, price_per_day")
        vehicles = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Database error: {e}", "error")
        vehicles = []

    return render_template("index.html",
                           vehicles=vehicles,
                           today=date.today().isoformat(),
                           is_admin=is_admin())

# ─────────────────────────────────────
#  BOOKING (form submit → save → payment)
# ─────────────────────────────────────
@app.route("/book", methods=["POST"])
def book():
    name       = request.form.get("name", "").strip()
    phone      = request.form.get("phone", "").strip()
    vehicle_id = request.form.get("vehicle_id", "").strip()
    from_str   = request.form.get("from_date", "").strip()
    to_str     = request.form.get("to_date", "").strip()

    # Validate
    errors = []
    if not name:
        errors.append("Name is required.")
    if not phone or not phone.isdigit() or len(phone) != 10:
        errors.append("Enter a valid 10-digit phone number.")
    if not vehicle_id:
        errors.append("No vehicle selected.")

    from_date = parse_date(from_str)
    to_date   = parse_date(to_str)

    if not from_date or not to_date:
        errors.append("Please enter valid dates.")
    elif from_date < date.today():
        errors.append("Start date cannot be in the past.")
    elif to_date <= from_date:
        errors.append("End date must be after start date.")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("home"))

    num_days = max((to_date - from_date).days, 1)

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        # Get vehicle
        cur.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
        vehicle = cur.fetchone()
        if not vehicle:
            flash("Vehicle not found.", "error")
            return redirect(url_for("home"))

        total_cost = float(vehicle["price_per_day"]) * num_days

        # Save customer
        cur.execute("INSERT INTO customers (name, phone) VALUES (%s, %s)", (name, phone))
        customer_id = cur.lastrowid

        # Save booking
        cur.execute("""
            INSERT INTO bookings (customer_id, vehicle_id, from_date, to_date, num_days, total_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (customer_id, vehicle_id, from_str, to_str, num_days, total_cost))
        conn.commit()
        booking_id = cur.lastrowid
        cur.close()
        conn.close()

        # Store in session for payment page
        session["pending"] = {
            "booking_id":   booking_id,
            "name":         name,
            "phone":        phone,
            "vehicle_name": vehicle["name"],
            "vehicle_type": vehicle["type"],
            "vehicle_img":  vehicle["image_url"],
            "from_date":    from_str,
            "to_date":      to_str,
            "num_days":     num_days,
            "total_cost":   total_cost,
        }
        return redirect(url_for("payment"))

    except Exception as e:
        flash(f"Booking error: {e}", "error")
        return redirect(url_for("home"))

# ─────────────────────────────────────
#  PAYMENT PAGE
# ─────────────────────────────────────
@app.route("/payment", methods=["GET", "POST"])
def payment():
    pending = session.get("pending")
    if not pending:
        flash("No pending booking. Please book a vehicle first.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        data = dict(pending)
        session.pop("pending", None)
        return render_template("success.html",
                               booking=data,
                               is_admin=is_admin())

    return render_template("payment.html",
                           pending=pending,
                           is_admin=is_admin())

# ─────────────────────────────────────
#  BOOKINGS PAGE  (all bookings)
# ─────────────────────────────────────
@app.route("/bookings")
def bookings():
    search = request.args.get("search", "").strip()
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        if search:
            cur.execute("""
                SELECT b.id, c.name, c.phone,
                       v.name AS vehicle_name, v.type AS vehicle_type, v.image_url,
                       b.from_date, b.to_date, b.num_days, b.total_cost
                FROM bookings b
                JOIN customers c ON b.customer_id = c.id
                JOIN vehicles  v ON b.vehicle_id  = v.id
                WHERE c.name LIKE %s OR c.phone LIKE %s OR v.name LIKE %s
                ORDER BY b.id DESC
            """, (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            cur.execute("""
                SELECT b.id, c.name, c.phone,
                       v.name AS vehicle_name, v.type AS vehicle_type, v.image_url,
                       b.from_date, b.to_date, b.num_days, b.total_cost
                FROM bookings b
                JOIN customers c ON b.customer_id = c.id
                JOIN vehicles  v ON b.vehicle_id  = v.id
                ORDER BY b.id DESC
            """)

        all_bookings = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Database error: {e}", "error")
        all_bookings = []

    return render_template("bookings.html",
                           bookings=all_bookings,
                           search=search,
                           is_admin=is_admin())

# ─────────────────────────────────────
#  DELETE BOOKING
# ─────────────────────────────────────
# ─────────────────────────────────────
#  DELETE BOOKING
# ─────────────────────────────────────
# ─────────────────────────────────────
#  DELETE BOOKING  (no admin check)
# ─────────────────────────────────────
@app.route("/delete/<int:id>")
def delete_booking(id):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM bookings WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Booking deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting booking: {e}", "error")
    return redirect(url_for("bookings"))
# ─────────────────────────────────────
#  DASHBOARD PAGE
# ─────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS total, COALESCE(SUM(total_cost),0) AS revenue FROM bookings")
        stats = cur.fetchone()

        cur.execute("""
            SELECT v.name, v.type, COUNT(b.id) AS cnt,
                   COALESCE(SUM(b.total_cost), 0) AS revenue
            FROM vehicles v
            LEFT JOIN bookings b ON b.vehicle_id = v.id
            GROUP BY v.id, v.name, v.type
            ORDER BY cnt DESC
        """)
        vstats = cur.fetchall()

        cur.execute("""
            SELECT b.id, c.name, v.name AS vehicle_name, b.total_cost
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN vehicles  v ON b.vehicle_id  = v.id
            ORDER BY b.id DESC LIMIT 5
        """)
        recent = cur.fetchall()

        cur.execute("SELECT COUNT(*) AS fleet FROM vehicles")
        fleet = cur.fetchone()

        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Dashboard error: {e}", "error")
        stats  = {"total": 0, "revenue": 0}
        vstats = []
        recent = []
        fleet  = {"fleet": 0}

    return render_template("dashboard.html",
                           stats=stats,
                           vstats=vstats,
                           recent=recent,
                           fleet=fleet,
                           is_admin=is_admin())

# ─────────────────────────────────────
#  ADMIN LOGIN / LOGOUT
# ─────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if is_admin():
        return redirect(url_for("add_vehicle"))
    if request.method == "POST":
        if (request.form.get("username") == "admin" and
                request.form.get("password") == "admin123"):
            session["admin"] = True
            flash("Welcome, Admin!", "success")
            return redirect(url_for("add_vehicle"))
        flash("Wrong credentials. Use admin / admin123", "error")
    return render_template("login.html", is_admin=False)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

# ─────────────────────────────────────
#  ADMIN — ADD VEHICLE
# ─────────────────────────────────────
@app.route("/add-vehicle", methods=["GET", "POST"])
def add_vehicle():
    if not is_admin():
        flash("Admin access required.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        name      = request.form.get("name", "").strip()
        vtype     = request.form.get("type", "Car").strip()
        price     = request.form.get("price_per_day", "").strip()
        image_url = request.form.get("image_url", "").strip()
        seats     = request.form.get("seats", "4").strip()
        tag       = request.form.get("tag", "").strip()

        errors = []
        if not name:
            errors.append("Vehicle name is required.")
        if not price or not price.replace(".", "").isdigit():
            errors.append("Valid price is required.")
        if not image_url:
            errors.append("Image URL is required.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("add_vehicle.html", is_admin=True, form=request.form)

        try:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO vehicles (name, type, price_per_day, image_url, seats, tag)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, vtype, float(price), image_url,
                  int(seats) if seats.isdigit() else 4, tag))
            conn.commit()
            cur.close()
            conn.close()
            flash(f'Vehicle "{name}" added successfully!', "success")
            return redirect(url_for("home"))
        except Exception as e:
            flash(f"Error: {e}", "error")

    return render_template("add_vehicle.html", is_admin=True, form={})

# ─────────────────────────────────────
#  ADMIN — DELETE VEHICLE
# ─────────────────────────────────────
@app.route("/delete-vehicle/<int:vid>")
def delete_vehicle(vid):
    if not is_admin():
        flash("Admin access required.", "error")
        return redirect(url_for("login"))
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM vehicles WHERE id = %s", (vid,))
        conn.commit()
        cur.close()
        conn.close()
        flash("Vehicle removed.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("home"))

# ─────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)