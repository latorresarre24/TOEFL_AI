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
    points1 = db.execute("SELECT sum(points) as avg_points FROM new_grades where user_id = ? and exam_id = 1;", session["user_id"])[0]["avg_points"]
    points2 = db.execute("SELECT sum(points) as avg_points FROM new_grades where user_id = ? and exam_id = 2;", session["user_id"])[0]["avg_points"]
    points3 = db.execute("SELECT sum(points) as avg_points FROM new_grades where user_id = ? and exam_id = 3;", session["user_id"])[0]["avg_points"]
    points4 = db.execute("SELECT sum(points) as avg_points FROM new_grades where user_id = ? and exam_id = 4;", session["user_id"])[0]["avg_points"]
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
    usr_id = session["user_id"]

    if request.method == "POST":
        # Initialize a dictionary to store user answers
        user_answers = {}

        for i in range(1, 14):
            # Construct the form field name
            #field_name = f"usr_ans{i}"
            
            # Get the answer for question i
            user_answer_id = request.form.get(f"{i}")

            # Ensure all questions have been answered
            #if not user_answer_id:
            #    return apology("Please answer all questions", 403)

            # Store the answer in the dictionary
            # but currently it is not used
            user_answers[i] = user_answer_id

            # Get points for question i
            q_points = db.execute("SELECT (points * (SELECT correct FROM reading_ans WHERE id = ?)) AS points FROM reading_qs WHERE reading_id=1 AND id = ?;", user_answer_id, i)[0]["points"]
            
            # Check if the question has already been answered
            q_a_result = db.execute("select id as id from new_grades where user_id = ? and exam_id = 1 and subject_id = 1 and reading_qs_id = ?;", session["user_id"], i)
            q_a = q_a_result[0]["id"] if q_a_result else None
            
            # if the question has already been answered, update the answer
            if q_a is not None:
                db.execute("update new_grades set points = ? where id = ?;", q_points, q_a)
            # if the question has not been answered, insert the answer
            else:
                db.execute("insert into new_grades (exam_id, subject_id, user_id, points, answer_id, reading_qs_id) values (?,?,?,?,?,?);", 1, 1, usr_id, q_points, user_answer_id,i)

        ans_53 = request.form.get("53") # 53 or None
        ans_54 = request.form.get("54")
        ans_55 = request.form.get("55")
        ans_56 = request.form.get("56")
        ans_57 = request.form.get("57")
        ans_58 = request.form.get("58")

        # /// TO DO ///
        # ans_14 = int(ans_53 + ans_54 + ans_55 + ans_56 + ans_57 + ans_58) # TODO fix answer_id to ans_14 (not working because it doesn´t accept "None") for example for not selected answers

        # mult = (ans_53 is not None) * (ans_54 is not None) * (ans_55 is not None) * (ans_56 is not None) * (ans_57 is not None) * (ans_58 is not None)
        # Check if specific answers are provided to calculate total points for question 14
        if ans_53 is not None and ans_54 is not None and ans_58 is not None and ans_55 is None and ans_56 is None and ans_57 is None:
            total_q_points_14 = 2
        else:
            total_q_points_14 = 0
        
        q_a_result_14 = db.execute("select id as id from new_grades where user_id = ? and exam_id = 1 and subject_id = 1 and reading_qs_id = 14;", session["user_id"])
        q_a_14 = q_a_result_14[0]["id"] if q_a_result_14 else None

        if q_a_14 is not None:
            db.execute("update new_grades set points = ?, answer_id = ? where id = ?;", total_q_points_14, 1, q_a_14) # TODO fix answer_id to ans_14 (not working because it doesn´t accept "None")
        else:
            db.execute("insert into new_grades (exam_id, subject_id, user_id, points, answer_id, reading_qs_id) values (?,?,?,?,?,?);", 1, 1, usr_id, total_q_points_14, 1,14) # TODO fix answer_id to ans_14 (not working because it doesn´t accept "None")

        

        #user_answers_14 = {}
        
        #user_answers_id_14 = request.form.getlist("qs14")

        #q_points_14 = 0
        #for i in range (1, len(user_answers_id_14)+1):
        #    q_points_14 *= db.execute("SELECT (points * (SELECT correct FROM reading_ans WHERE id = ?)) AS points FROM reading_qs WHERE reading_id=1 AND id = 14;", user_answers_id_14[i])[0]["points"]
        #    # Add all user answers
            # Multiply all user answers
        
        ## Check if the entry with id = 14 exists
        #entry_14 = db.execute("SELECT id FROM new_grades WHERE id = 14;")
        
        # If the entry exists, update it
        #if entry_14:
        #    db.execute("update new_grades set points = ? where id = 14;", q_points_14)
        # If the entry does not exist, insert a new entry
        #else:
        #    db.execute("insert into new_grades (exam_id, subject_id, user_id, points, answer_id, reading_qs_id) values (?,?,?,?,?,?);", 1, 1, usr_id, q_points_14, 1, 14)
            

        return redirect("/grades")

    # Fetch all questions in a single query
    questions = db.execute("SELECT id, question FROM reading_qs;")
    # Store questions in a dictionary
    questions_dict = {question["id"]: question["question"] for question in questions}

    # Fetch all answers in a single query
    answers = db.execute("SELECT id, answer FROM reading_ans;")
    # Store answers in a dictionary
    answers_dict = {answer["id"]: answer["answer"] for answer in answers}
        
    return render_template("reading-qs.html", questions=questions_dict, answers=answers_dict)