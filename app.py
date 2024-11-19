import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import werkzeug
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///toeflai.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show index"""
    return render_template("index.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        rows = db.execute(
            "SELECT * FROM users WHERE email = ?", request.form.get("email")
        )

        # Ensure email exists and password is correct
        # If two users have the same "email", it will also return an error
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("Invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure name was submitted
        if not request.form.get("name"):
            return apology("must provide name", 403)
        
        # Ensure surname was submitted
        elif not request.form.get("last_name"):
            return apology("must provide surname", 403)

        # Ensure email was submitted
        elif not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        # Check if email already exists
        rows_three = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))
        
        if len(rows_three) != 0:
            return apology("User has already been registered", 400)
        
        # Insert user into database
        result = db.execute(
            "INSERT INTO users (name, last_name, email, hash) VALUES (?, ?, ?, ?)",
            request.form.get("name"),
            request.form.get("last_name"),
            request.form.get("email"),
            generate_password_hash(request.form.get("password")),
        )

        # Check if email already exists
        if not result:
            return apology("email already exists", 403)

        # Remember which user has logged in
        session["user_id"] = rows_three[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
    
@app.route("/grades")
@login_required
def grades():
    """Show index"""
    points1 = db.execute("SELECT sum(points) as avg_points FROM grades where user_id = ? and exam_id = 1;", session["user_id"])[0]["avg_points"]
    points2 = db.execute("SELECT sum(points) as avg_points FROM grades where user_id = ? and exam_id = 2;", session["user_id"])[0]["avg_points"]
    points3 = db.execute("SELECT sum(points) as avg_points FROM grades where user_id = ? and exam_id = 3;", session["user_id"])[0]["avg_points"]
    points4 = db.execute("SELECT sum(points) as avg_points FROM grades where user_id = ? and exam_id = 4;", session["user_id"])[0]["avg_points"]
    return render_template("grades.html", points1=points1, points2=points2, points3=points3, points4=points4)

@app.route("/reading")
@login_required
def reading():
    """Show reading"""
    reading1 = db.execute("SELECT lecture FROM readings where id = 1;") [0]["lecture"]
    return render_template("reading.html", reading1=reading1)
    #return render_template("reading.html")

@app.route("/reading-qs", methods=["GET", "POST"])
@login_required
def reading_qs():
    """Show reading questions"""
    if request.method == "POST":
        # Ensure all questions have been answered
        # if not request.form.get("1") or not request.form.get("2") or not request.form.get("3") or not request.form.get("4") or not request.form.get("5") or not request.form.get("6") or not request.form.get("7") or not request.form.get("8") or not request.form.get("9") or not request.form.get("10"):
        #    return apology("Please answer all questions", 403)
    
        for i in range(1, 2):
            # get answer for quetion i
            for user_answer_id in range(1, 5):
                user_answer_id = request.form.get("usr_ans")
                
                # Ensure all questions have been answered
                if not user_answer_id:
                    return apology("Please answer all questions", 403)

                # Get points for question i
                q_points = db.execute("SELECT (points * (SELECT correct FROM reading_ans WHERE id = ?)) AS points FROM reading_qs WHERE reading_id=1 AND id = ?;", user_answer_id, i)[0]["points"]
                # Check if the question has already been answered
                q_a = db.execute("select points from grades where user_id = ? and exam_id = 1 and answer_id = ? and subject_id = 1;", session["user_id"], i)
                # if the question has already been answered, update the answer
                if q_a:
                   db.execute("update grades set points = ? where exam_id = 1 and subject_id =1 and user_id = ? and answer_id = ?;", q_points, session["user_id"], user_answer_id)
            
                # if the question has not been answered, insert the answer
                else:
                   db.execute("insert into grades (exam_id, subject_id, user_id, points, answer_id) values (1,1,?,?,?);", session["user_id"], q_points, user_answer_id)

        return redirect("/grades")

    # Fetch all questions in a single query
    questions = db.execute("SELECT id, question FROM reading_qs;")
    # Store answers in a dictionary
    questions_dict = {question["id"]: question["question"] for question in questions}

    # Fetch all answers in a single query
    answers = db.execute("SELECT id, answer FROM reading_ans;")
    # Store answers in a dictionary
    answers_dict = {answer["id"]: answer["answer"] for answer in answers}
        
    return render_template("reading-qs.html", questions=questions_dict, answers=answers_dict)


# ---------------------------- OLD CODE --------------------------------

# @app.route("/reading-qs", methods=["GET", "POST"])
# @login_required
# def reading_qs():
#    """Show reading questions"""
#    if request.method == "POST":
#        # Ensure all questions have been answered
#        # if not request.form.get("1") or not request.form.get("2") or not request.form.get("3") or not request.form.get("4") or not request.form.get("5") or not request.form.get("6") or not request.form.get("7") or not request.form.get("8") or not request.form.get("9") or not request.form.get("10"):
#        #    return apology("Please answer all questions", 403)
#        
        # Calculate points
#        points = 0
#        for i in range(1, 14):
            # if request.form.get(str(i)) == db.execute("SELECT answer FROM reading_ans WHERE id = ?", i)[0]["answer"]:
            #    points += 1

            # initialize loop for answers and add 4 each time
#            start_index = (i - 1) * 4 + 1
#            answer_a = request.form.get("start_index")
#            answer_b = request.form.get("start_index +1")
#           answer_c = request.form.get("start_index +2")
#            answer_d = request.form.get("start_index +3")

            # Get points for each question
#            points_a = db.execute("SELECT (points * (SELECT correct FROM reading_ans WHERE id = ?, i)) AS points FROM reading_qs WHERE id = ?;", start_index)[0]["points"]
#            points_b = db.execute("SELECT (points * (SELECT correct FROM reading_ans WHERE id = ?, i)) AS points FROM reading_qs WHERE id = ?;", start_index + 1)[0]["points"]
#            points_c = db.execute("SELECT (points * (SELECT correct FROM reading_ans WHERE id = ?, i)) AS points FROM reading_qs WHERE id = ?;", start_index + 2)[0]["points"]
#            db_a = db.execute("SELECT points as points FROM grades WHERE exam_id = 1 AND subject_id = 1 and user_id = ? and answer_id =?;", session["user_id"], start_index)[0]["points"]    
#            if not db_a:
#                record_a = db.execute("INSERT INTO grades (exam_id, subject_id, user_id, points) VALUES (1, 1, ?, ?);", session["user_id"], start_index)
#            else:
#                record_a = db.execute("UPDATE grades SET points = ? WHERE exam_id = 1 AND subject_id = 1 and user_id = ? and answer_id =?;", session["user_id"], start_index)
        
        # Insert grade into database
#        db.execute("INSERT INTO grades (user_id, exam_id, points) VALUES (?, 1, ?);", session["user_id"], points)
        
#        return redirect("/grades")

    # Fetch all questions in a single query
#    questions = db.execute("SELECT id, question FROM reading_qs;")
    # Store answers in a dictionary
#    questions_dict = {question["id"]: question["question"] for question in questions}

    # Fetch all answers in a single query
#    answers = db.execute("SELECT id, answer FROM reading_ans;")
    # Store answers in a dictionary
#    answers_dict = {answer["id"]: answer["answer"] for answer in answers}
        
#    return render_template("reading-qs.html", questions=questions_dict, answers=answers_dict)

# ---------------------------- OLD CODE --------------------------------