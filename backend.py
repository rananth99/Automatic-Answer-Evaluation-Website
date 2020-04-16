import flask
from flask import *
from flask_sqlalchemy import SQLAlchemy

from nlp import Ngrams, common

import requests
import os
import sys

from datetime import datetime
import csv
import threading
import socket

basedir = os.path.abspath(os.path.dirname(__file__))

application = Flask(__name__)
application.config["DEBUG"] = True
application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + \
    os.path.join(basedir, "db.sqlite")
application.secret_key = 'not_so_secret'

db = SQLAlchemy(application)

# Database #


class User(db.Model):
    email = db.Column(db.Text(), primary_key=True)
    username = db.Column(db.Text(), primary_key=True)
    password = db.Column(db.Text())
    name = db.Column(db.Text())
    number = db.Column(db.Integer())


# class Test(db.Model):
#     test_id = db.Column(db.Integer, primary_key=True)
#     test_name = db.Column(db.Text())
#     creator = db.Column(db.Text, db.ForeignKey("user.username"))


# class Question(db.Model):
#     question_id = db.Column(db.Integer(), primary_key=True)
#     # test_id = db.Column(db.Integer, db.ForeignKey(
#     #     "test.test_id"), primary_key=True)
#     question = db.Column(db.Integer(), primary_key=True)
#     answer = db.Column(db.Text())
#     marks = db.Column(db.Float())


class Answer(db.Model):
    answer_id = db.Column(db.Integer(), primary_key=True)
    # test_id = db.Column(db.Integer, db.ForeignKey(
    #     "test.test_id"), primary_key=True)
    # question_id = db.Column(db.Integer, db.ForeignKey(
    #     "question.question_id"), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(
        "student.student_id"))
    user = db.Column(db.Text, db.ForeignKey("user.username"))
    model = db.Column(db.Text())
    answer = db.Column(db.Text())
    total = db.Column(db.Float())
    marks = db.Column(db.Float())


class Student(db.Model):
    student_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Text)
    srn = db.Column(db.Text, unique=True)

# Application #


@application.route("/")
def home():
    return redirect('/login.html/')


@application.route('/dashboard.html/', methods=["GET"])
def dashboard():
    return render_template("dashboard.html", user=session["username"])


@application.route("/login.html/", methods=["GET", "POST"])
def login():
    if(request.method == "POST"):
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if(user is None):
            flash("Username not available. Sign up first", "danger")
        elif(user.password != password):
            flash("Username and password does not match.", "danger")
        else:
            session["username"] = user.username
            return redirect("/dashboard.html/")

    return render_template('login.html')


@application.route("/signup.html/", methods=["GET", "POST"])
def signup():

    if(request.method == "POST"):
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        name = request.form["name"]
        number = request.form["number"]

        test = email.endswith("@gmail.com") and len(
            number) == 10 and number.isdigit()
        if(not test):
            flash("Wrong input format", "danger")

        user1 = User.query.filter_by(email=email).first()
        user2 = User.query.filter_by(username=username).first()

        if(user1 is None and user2 is None):
            user = User(email=email, username=username,
                        password=password, name=name, number=number)
            db.session.add(user)
            db.session.commit()
            flash("User created succesfully. Login to start evaluating", "success")
            return redirect("/login.html/")
        else:
            flash("Username or email already present.", "danger")
            return render_template("signup.html")

    else:
        return render_template("signup.html")


@application.route('/test.html/')
def test():
    return render_template("test.html", user=session["username"])


@application.route('/view_answers.html/<srn>')
def view_answer():
    return render_template("view_answer.html", user=session["username"], data=data)


@application.route('/evaluate.html/')
def eval():
    students = Student.query.all()
    data = []
    for student in students:
        s_id = student.student_id
        name = student.name
        srn = student.srn
        answers = Answer.query.filter_by(student_id=s_id).all()
        total_marks = 0
        marks_scored = 0
        for answer in answers:
            total_marks += answer.total
            marks_scored += answer.marks
        data.append([name, srn, len(answers), marks_scored, total_marks])

    return render_template("evaluate.html", user=session["username"], data=data)


@application.route('/result.html/')
def result():
 
    return render_template("result.html", user=session["username"])


@application.route('/add.html/', methods=["GET", "POST"])
def add():
    if(request.method == "POST"):
        name = request.form["name"]
        srn = request.form["srn"]
        total = int(request.form["marks"])
        model = request.form["model"]
        answer = request.form["answer"]
        user = session["username"]

        student = Student.query.filter_by(name=name, srn=srn)
        if(student is None):
            student = Student(name=name, srn=srn)
            db.session.add(student)

        student_id = Student.query.filter_by(
            name=name, srn=srn).first().student_id
        marks = evalulate_answer(model, answer)*total

        answer = Answer(student_id=student_id, total=total,
                        marks=marks, model=model, answer=answer, user=user)
        db.session.add(answer)
        db.session.commit()

    return render_template("add.html", user=session["username"])


@application.route('/logout/')
def logout():
    session.pop("username")
    return redirect("/login.html/")


def evalulate_answer(model, answer):
    alpha = 0.3
    beta = 0.25
    pattern_score = Ngrams(model)*Ngrams(answer)
    common_score = common(model, answer)

    return min(1, alpha*pattern_score+(1-alpha)*common_score+beta)


if __name__ == "__main__":
    db.create_all()
    application.run()
