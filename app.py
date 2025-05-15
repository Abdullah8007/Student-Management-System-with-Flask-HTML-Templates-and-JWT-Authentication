from flask import Flask, render_template, request, redirect, url_for, make_response, g
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
app.config["UPLOAD_FOLDER"] = "static/upload"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "Abdullah_Jagrala"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(256), nullable = False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), nullable = False)
    email = db.Column(db.String(30), nullable = False, unique = True)
    dob = db.Column(db.Date, nullable = False)
    gender = db.Column(db.String(5), nullable = False)
    roll_no = db.Column(db.String(10), nullable = False)
    addmission_date = db.Column(db.Date, nullable = False)
    course = db.Column(db.String(30), nullable = False)
    photo = db.Column(db.String(300), nullable = False)

with app.app_context():
    db.create_all()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")

        if not token:
            return render_template("login.html")

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms = ["HS256"])
            g.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"Message" : "Token has Expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"Message" : "Invalid Token!"}), 401

        return f(*args, **kwargs)

    return decorated

@app.route("/", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        exist_user = User.query.filter_by(username = username).first()
        if exist_user:
            return jsonify({"Message" : "User Already Registered!"})

        password = str(password)
        password_hash = generate_password_hash(password)

        new_user = User(username = username, password = password_hash)
        db.session.add(new_user)
        db.session.commit()
        # return jsonify({"Message" : "User Registered Succssfully!"}), 201

        return render_template("login.html")

    return render_template("register.html")
    
@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username = username).first()

        if not user:
            return jsonify({"Message" : "Invalid Username!"}), 401

        password = str(password)
        if not check_password_hash(user.password,  password):
            return jsonify({"Message" : "Invalid Password!"}), 401

        expire_at = datetime.utcnow() + timedelta(minutes = 5)

        token = jwt.encode(
            {
                "user_id" : user.id,
                "username" : user.username,
                "exp" : expire_at
            },
            app.config["SECRET_KEY"],
            algorithm = "HS256"
        )

        response = make_response(render_template("index.html"))
        response.set_cookie("token", token, expires = expire_at, httponly = True)

        return response
        
    return render_template("login.html")

@app.route("/logout", methods = ["GET"])
@token_required
def logout():
    response = make_response(render_template("login.html"))
    response.delete_cookie("token")
    return response

# @app.route('/')
# def home():
#     students = Student.query.all()
#     return render_template("index.html", students = students)

@app.route('/add_student', methods = ["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        dob = request.form.get("dob")
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
        gender = request.form.get("gender")
        rollnumber = request.form.get("rollnumber")
        addmission_date = request.form.get("addmission_date")
        addmission_date = datetime.strptime(addmission_date, "%Y-%m-%d").date()
        course = request.form.get("course")
        photo = request.files["photo"]
        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], photo.filename)

        photo.save(photo_path)

        # print({"name" : name, "email" : email, "dob" : dob, "gender" : gender, "roll_no" : rollnumber, "addmission_date" : addmission_date, "course" : course, "photo" : photo})

        student = Student(name = name, email = email, dob = dob, gender = gender, roll_no = rollnumber, addmission_date = addmission_date, course = course, photo = photo.filename)

        db.session.add(student)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("add_student.html")

@app.route('/student_details/<int:student_id>', methods = ["GET"])
def student_details(student_id):

    student = Student.query.get(student_id)

    return render_template("student_details.html", student = student)

@app.route('/update_student/<int:student_id>', methods = ["GET", "POST"])
def update_student(student_id):
    student = Student.query.get(student_id)

    if request.method == "POST":
        student.name = request.form.get("name")
        student.email = request.form.get("email")
        dob = request.form.get("dob")
        student.dob = datetime.strptime(dob, "%Y-%m-%d").date()
        student.gender = request.form.get("gender")
        student.rollnumber = request.form.get("rollnumber")
        addmission_date = request.form.get("addmission_date")
        student.addmission_date = datetime.strptime(addmission_date, "%Y-%m-%d").date()
        student.course = request.form.get("course")
        photo = request.files["photo"]
        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], photo.filename)

        photo.save(photo_path)

        student.photo = photo.filename

        db.session.commit()

        return redirect(url_for('home'))

    return render_template("update_student.html", student = student)

@app.route('/delete_student/<int:student_id>')
def delete_student(student_id):

    student = Student.query.get(student_id)

    db.session.delete(student)
    db.session.commit()

    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug = True)