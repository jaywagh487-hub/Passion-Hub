from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "passionhub_secret_key"

DATABASE = "passionhub.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT DEFAULT '',
            city TEXT DEFAULT '',
            community TEXT DEFAULT '',
            bike_model TEXT DEFAULT '',
            riding_style TEXT DEFAULT '',
            game TEXT DEFAULT '',
            platform TEXT DEFAULT '',
            rank TEXT DEFAULT '',
            experience TEXT DEFAULT ''
        )
        
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            location TEXT,
            community TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        community = request.form["community"]

        conn = get_db()

        try:

            cursor = conn.execute(
                """
                  INSERT INTO users
                  (name, email, password, community)
                 VALUES (?, ?, ?, ?)
                 """,
                (
                    name,
                    email,
                    generate_password_hash(password)
                )
            )

            user_id = cursor.lastrowid

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "signup.html",
                error="Email already registered."
            )

        conn.close()

        session["user_id"] = user_id
        session["user_name"] = name
        session["community"] = community

        return redirect(url_for("profile"))

    selected = request.args.get("community", "")

    return render_template(
        "signup.html",
        selected=selected
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
                user["password"],
                password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    message = None
    error = None

    if request.method == "POST":

        email = request.form["email"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user:
            session["reset_user_id"] = user["id"]

            return redirect(url_for("reset_password"))

        error = "No account found with this email."

    return render_template(
        "forgot_password.html",
        error=error,
        message=message
    )


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if "reset_user_id" not in session:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            return render_template(
                "reset_password.html",
                error="Passwords do not match."
            )

        if len(password) < 6:

            return render_template(
                "reset_password.html",
                error="Password must be at least 6 characters."
            )

        conn = get_db()

        conn.execute(
            """
            UPDATE users
            SET password = ?
            WHERE id = ?
            """,
            (
                generate_password_hash(password),
                session["reset_user_id"]
            )
        )

        conn.commit()
        conn.close()

        session.pop("reset_user_id", None)

        return redirect(url_for("login"))

    return render_template("reset_password.html")


@app.route("/choose-community", methods=["GET", "POST"])
def choose_community():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        community = request.form["community"]

        session["community"] = community

        return redirect(url_for("profile"))

    return render_template("choose_community.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    community = session.get("community", "")

    if request.method == "POST":

        bio = request.form["bio"]
        city = request.form["city"]
        experience = request.form["experience"]

        conn = get_db()

        if community == "biker":

            bike_model = request.form["bike_model"]
            riding_style = request.form["riding_style"]

            conn.execute("""
                UPDATE users
                SET bio = ?,
                    city = ?,
                    community = ?,
                    bike_model = ?,
                    riding_style = ?,
                    experience = ?
                WHERE id = ?
            """, (
                bio,
                city,
                community,
                bike_model,
                riding_style,
                experience,
                session["user_id"]
            ))

        else:

            game = request.form["game"]
            platform = request.form["platform"]
            rank = request.form["rank"]

            conn.execute("""
                UPDATE users
                SET bio = ?,
                    city = ?,
                    community = ?,
                    game = ?,
                    platform = ?,
                    rank = ?,
                    experience = ?
                WHERE id = ?
            """, (
                bio,
                city,
                community,
                game,
                platform,
                rank,
                experience,
                session["user_id"]
            ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template(
        "profile.html",
        name=session["user_name"],
        community=community
    )
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    posts = conn.execute("""
        SELECT posts.*, users.name
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE users.community = ?
        ORDER BY posts.created_at DESC
    """, (user["community"],)).fetchall()

    events = conn.execute("""
        SELECT events.*, users.name
        FROM events
        JOIN users ON events.user_id = users.id
        WHERE events.community = ?
        ORDER BY events.event_date ASC
    """, (user["community"],)).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        posts=posts,
        events=events
    )
@app.route("/create-post", methods=["POST"])
def create_post():

    if "user_id" not in session:
        return redirect(url_for("login"))

    content = request.form["content"]

    if content.strip():

        conn = get_db()

        conn.execute("""
            INSERT INTO posts (user_id, content)
            VALUES (?, ?)
        """, (
            session["user_id"],
            content
        ))

        conn.commit()
        conn.close()

    return redirect(url_for("dashboard"))
@app.route("/create-event", methods=["POST"])
def create_event():

    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    description = request.form["description"]
    event_date = request.form["event_date"]
    location = request.form["location"]

    conn = get_db()

    user = conn.execute(
        "SELECT community FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.execute("""
        INSERT INTO events
        (user_id, title, description, event_date, location, community)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        title,
        description,
        event_date,
        location,
        user["community"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


if __name__ == "__main__":

    create_database()

    app.run(debug=True)