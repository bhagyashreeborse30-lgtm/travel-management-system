import os
import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "travelmate.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    );
    CREATE TABLE IF NOT EXISTS destinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL DEFAULT 0,
        duration TEXT NOT NULL DEFAULT '1 day',
        image_url TEXT NOT NULL DEFAULT '',
        map_url TEXT NOT NULL DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        destination_id INTEGER NOT NULL,
        visit_date TEXT NOT NULL,
        people INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(destination_id) REFERENCES destinations(id)
    );
    """)
    admin = db.execute("SELECT id FROM users WHERE email=?", ("admin@travelmate.com",)).fetchone()
    if not admin:
        db.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                   ("TravelMate Admin", "admin@travelmate.com",
                    generate_password_hash("Admin@12345"), "admin"))
    count = db.execute("SELECT COUNT(*) FROM destinations").fetchone()[0]
    if count == 0:
        sample = [
            ("Gateway of India", "Mumbai", "Maharashtra", "Heritage",
             "An iconic waterfront monument and a popular starting point for exploring Mumbai.",
             500, "Half day", "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=1200",
             "https://www.openstreetmap.org/search?query=Gateway%20of%20India%20Mumbai"),
            ("Ajanta Caves", "Chhatrapati Sambhajinagar", "Maharashtra", "History",
             "Explore ancient rock-cut Buddhist caves known for murals, sculpture and architecture.",
             1200, "Full day", "https://images.unsplash.com/photo-1606293926075-69a00dbjed21?w=1200",
             "https://www.openstreetmap.org/search?query=Ajanta%20Caves"),
            ("Shaniwar Wada", "Pune", "Maharashtra", "Heritage",
             "Visit the historic Peshwa fortification in the heart of Pune.",
             350, "2-3 hours", "https://images.unsplash.com/photo-1595658658481-d53d3f999875?w=1200",
             "https://www.openstreetmap.org/search?query=Shaniwar%20Wada%20Pune"),
            ("Bhandardara", "Ahmednagar", "Maharashtra", "Nature",
             "Enjoy lakes, waterfalls, mountain views and peaceful nature trails.",
             1800, "1-2 days", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1200",
             "https://www.openstreetmap.org/search?query=Bhandardara%20Maharashtra"),
            ("Trimbakeshwar Temple", "Nashik", "Maharashtra", "Spiritual",
             "A well-known Jyotirlinga temple located near the Brahmagiri hills.",
             700, "Half day", "https://images.unsplash.com/photo-1604608672516-6e3e5c3f4b5a?w=1200",
             "https://www.openstreetmap.org/search?query=Trimbakeshwar%20Temple")
        ]
        db.executemany("""INSERT INTO destinations
            (name,city,state,category,description,price,duration,image_url,map_url)
            VALUES(?,?,?,?,?,?,?,?,?)""", sample)
    db.commit()
    db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access is required.", "danger")
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_today():
    return {"today": datetime.now().strftime("%Y-%m-%d")}

@app.route("/")
def home():
    db = get_db()
    destinations = db.execute("SELECT * FROM destinations ORDER BY id DESC LIMIT 6").fetchall()
    return render_template("home.html", destinations=destinations)

@app.route("/destinations")
def destinations():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql = "SELECT * FROM destinations WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR city LIKE ? OR state LIKE ?)"
        params.extend([f"%{q}%"] * 3)
    if category:
        sql += " AND category=?"
        params.append(category)
    sql += " ORDER BY name"
    rows = get_db().execute(sql, params).fetchall()
    categories = get_db().execute("SELECT DISTINCT category FROM destinations ORDER BY category").fetchall()
    return render_template("destinations.html", destinations=rows, categories=categories, q=q, selected=category)

@app.route("/destination/<int:destination_id>")
def destination_detail(destination_id):
    item = get_db().execute("SELECT * FROM destinations WHERE id=?", (destination_id,)).fetchone()
    if not item:
        flash("Destination not found.", "danger")
        return redirect(url_for("destinations"))
    return render_template("destination.html", item=item)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter all details. Password must contain at least 6 characters.", "danger")
            return render_template("register.html")
        try:
            db = get_db()
            cur = db.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                             (name, email, generate_password_hash(password)))
            db.commit()
            session.update(user_id=cur.lastrowid, name=name, role="user")
            flash("Your account has been created successfully.", "success")
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            flash("This email is already registered. Please log in.", "warning")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("admin_dashboard") if user["role"] == "admin" else url_for("home"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/book/<int:destination_id>", methods=["POST"])
@login_required
def book(destination_id):
    db = get_db()
    item = db.execute("SELECT * FROM destinations WHERE id=?", (destination_id,)).fetchone()
    if not item:
        flash("Destination not found.", "danger")
        return redirect(url_for("destinations"))
    visit_date = request.form.get("visit_date", "")
    try:
        datetime.strptime(visit_date, "%Y-%m-%d")
        people = int(request.form.get("people", "1"))
        if people < 1 or people > 30:
            raise ValueError()
    except ValueError:
        flash("Please select a valid date and number of visitors (1–30).", "danger")
        return redirect(url_for("destination_detail", destination_id=destination_id))
    total = float(item["price"]) * people
    db.execute("""INSERT INTO bookings(user_id,destination_id,visit_date,people,total_amount,status,created_at)
                  VALUES(?,?,?,?,?,?,?)""",
               (session["user_id"], destination_id, visit_date, people, total, "Pending",
                datetime.now().strftime("%Y-%m-%d %H:%M")))
    db.commit()
    flash("Booking request submitted! Check My Bookings for its status.", "success")
    return redirect(url_for("my_bookings"))

@app.route("/my-bookings")
@login_required
def my_bookings():
    rows = get_db().execute("""SELECT b.*, d.name AS destination, d.city
        FROM bookings b JOIN destinations d ON b.destination_id=d.id
        WHERE b.user_id=? ORDER BY b.id DESC""", (session["user_id"],)).fetchall()
    return render_template("my_bookings.html", bookings=rows)

@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        "users": db.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0],
        "destinations": db.execute("SELECT COUNT(*) FROM destinations").fetchone()[0],
        "bookings": db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
        "pending": db.execute("SELECT COUNT(*) FROM bookings WHERE status='Pending'").fetchone()[0]
    }
    bookings = db.execute("""SELECT b.*, u.name AS customer, d.name AS destination
        FROM bookings b JOIN users u ON b.user_id=u.id
        JOIN destinations d ON b.destination_id=d.id ORDER BY b.id DESC""").fetchall()
    return render_template("admin.html", stats=stats, bookings=bookings)

@app.route("/admin/destination/add", methods=["GET", "POST"])
@admin_required
def add_destination():
    if request.method == "POST":
        fields = [request.form.get(k, "").strip() for k in
                  ("name", "city", "state", "category", "description", "duration", "image_url", "map_url")]
        try:
            price = float(request.form.get("price", "0"))
            if price < 0 or not all(fields[:6]):
                raise ValueError()
        except ValueError:
            flash("Please complete required fields and enter a valid price.", "danger")
            return render_template("add_destination.html")
        get_db().execute("""INSERT INTO destinations
            (name,city,state,category,description,duration,image_url,map_url,price)
            VALUES(?,?,?,?,?,?,?,?,?)""", (*fields, price))
        get_db().commit()
        flash("Destination added successfully.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("add_destination.html")

@app.route("/admin/booking/<int:booking_id>/<status>", methods=["POST"])
@admin_required
def update_booking(booking_id, status):
    if status not in ("Confirmed", "Cancelled"):
        flash("Invalid booking status.", "danger")
    else:
        db = get_db()
        db.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
        db.commit()
        flash(f"Booking #{booking_id} updated to {status}.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
