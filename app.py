from tools import *
import re
from helpers import apology, login_required
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
def index():
    return render_template('index.html')
    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            return apology("Must enter both username and password", 403)
        
        try:
            # enterUsername(username)
            enterPassword(username, password)
        except SyntaxError:
            return apology("Wrong details")
                
        student = get_student_id()
        session['user_id'] = student
        sections = get_sections(student)
        sections = [{'sectionId': f"{section_id}"} for section_id in sections]
        jsons = get_data(sections)
        if jsons == "Error":
            return apology("Error", 400)
        final = []
        for json_data in jsons:
            processed = process(json_data['data'])
            json_data['data'] = processed
            final.append(print_output(json_data))
        # print(final)

        return render_template("grades.html", subjects=final)
        # return jsonify(final)
        
@app.route('/logout')
def logout():
    session.clear()
    
    return redirect('/')