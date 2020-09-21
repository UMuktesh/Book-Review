import os

from flask import Flask, session, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
import requests
import json

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return apology("must provide username", 403)
        elif not password:
            return apology("must provide password", 403)
        rows = db.execute("SELECT * FROM users WHERE username = :user", {"user":username}).fetchall()
        print(rows)
        if len(rows) != 1 or not check_password_hash(rows[0][2], password):
            return apology("invalid username and/or password", 403)
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password1"):
            return apology("must provide password", 403)

        elif not request.form.get("password2"):
            return apology("must retype password", 403)

        elif not request.form.get("password1") == request.form.get("password2"):
            return apology("passwords dont match", 403)

        username = request.form.get("username")
        password = request.form.get("password2")
        rows = db.execute("SELECT * FROM users WHERE username = :user", {"user":username}).fetchall()
        if len(rows) != 0:
            return apology("username is unavailable", 403)

        db.execute("INSERT INTO users (username, password) VALUES (:user, :pass)", {"user":username, "pass":generate_password_hash(password)})
        db.commit()
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        return render_template("search.html")

    else:
        search = request.form.get("search")
        result = db.execute("SELECT title, isbn FROM books WHERE CAST(isbn AS TEXT) LIKE :s OR title ILIKE :s OR author ILIKE :s ORDER BY title", {"s":"%" + search + "%"}).fetchall()
        if not result:
            return apology("No match found", 403)
        return render_template("search.html", result=result)

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    if request.method == "POST":
        review = request.form.get("review")
        rating = request.form.get("rating")
        info = db.execute("SELECT id FROM books WHERE isbn = :i", {"i":isbn}).fetchone()
        print(info)
        db.execute("INSERT INTO review (user_id, book_id, review, rating) VALUES (:u, :b, :r, :ra)", {"u":session["user_id"], "b":info[0], "r":review, "ra":rating})
        db.commit()
        return redirect(f"/book/{isbn}")

    else:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "mfHx01V4xOyrUwHgxVAtFw", "isbns": isbn})
        res = res.json()
        wrc = res['books'][0]['work_ratings_count']
        ar = res['books'][0]['average_rating']
        info = db.execute("SELECT * FROM books WHERE isbn = :i", {"i":isbn}).fetchone()
        nreviewed = db.execute("SELECT COUNT(*) FROM review WHERE user_id = :u AND book_id = :b", {"u":session["user_id"], "b":info[0]}).fetchone()
        if nreviewed[0] != 1:
            nreviewed = True
        else:
            nreviewed = False
        reviews = db.execute("SELECT review FROM review WHERE book_id = :b", {"b":info[0]}).fetchall()
        val = list(db.execute("SELECT AVG(rating), COUNT(rating) FROM review WHERE book_id = :b", {"b":info[0]}).fetchone())
        print(val)
        if val[1] == 0:
            val[0] = 0
        val[0] = float("{:.1f}".format(val[0]))
        return render_template("book.html", info=info, wrc=wrc, ar=ar, reviews=reviews, nreviewed=nreviewed, val=val)

@app.route("/api/<string:isbn>")
def api(isbn):
    info = db.execute("SELECT * FROM books WHERE isbn = :i", {"i":isbn}).fetchone()
    if info is None:
          return jsonify({"error": "Invalid isbn"}), 404
    val = list(db.execute("SELECT AVG(rating), COUNT(rating) FROM review WHERE book_id = :b", {"b":info[0]}).fetchone())
    if val[1] == 0:
        val[0] = 0
    val[0] = float("{:.1f}".format(val[0]))
    api = {
        "title": info[2],
        "author": info[3],
        "year": info[4],
        "isbn": info[1],
        "review_count": val[1],
        "average_score": val[0]
    }
    return jsonify(api)
