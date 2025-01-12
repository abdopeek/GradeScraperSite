from tools import *
import re
from helpers import apology, login_required
from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from flask_session import Session
import urllib.parse
import ast

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def get_webdriver():
    if 'webdriver' in session:
        try:
            driver = webdriver.Remote(command_executor='http://127.0.0.1:4444/wd/hub')
            driver.session_id = session['webdriver']
            return driver
        except Exception as e:
            print(f"Error occured w webdriver: {e}")
            return None
    return None

def create_webdriver():
    ser = Service(r"C:\Users\mahgo\Downloads\edgedriver_win64 (1)\msedgedriver.exe")
    op = webdriver.EdgeOptions()
    op.add_argument('headless')
    op.add_argument('--log-level=3')
    op.add_argument('--log-path=path/to/edge.log')
    op.add_experimental_option('excludeSwitches', ['enable-logging'])
    op.add_experimental_option('detach', True)
    driver = webdriver.Edge(service=ser, options=op)
    driver.minimize_window()
    driver.get("https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Registration/Schedule")
    return driver

def quit_webdriver():
    if 'webdriver' in session:
        driver = get_webdriver()
        if driver:
            driver.quit()
        session.pop('webdriver', None)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
def index():
    # if session['user_id']:
        # driver = create_webdriver()
        # session['webdriver'] = driver.session_id

        # student = session['user_id']
        # sections = get_sections(student, driver)
        # sections = [{'sectionId': f"{section_id}"} for section_id in sections]
        # jsons = get_data(sections, driver)
        # if jsons == "Error":
        #     return apology("Error", 400)
        # final = []
        # for json_data in jsons:
        #     processed = process(json_data['data'])
        #     json_data['data'] = processed
        #     final.append(print_output(json_data))

        # # return render_template("grades.html", subjects=final)
        # return redirect(url_for("grades", final=final), code=307)
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
            driver = create_webdriver()
            session['webdriver'] = driver.session_id
            enterUsername(username, driver)
            enterPassword(password, driver)
        except SyntaxError:
            quit_webdriver()
            return apology("Wrong details")
               
        student = get_student_id(driver)
        session['user_id'] = student
        sections = get_sections(student, driver)
        sections = [{'sectionId': f"{section_id}"} for section_id in sections]
        jsons = get_data(sections, driver)
        if jsons == "Error":
            return apology("Error", 400)
        final = []
        for json_data in jsons:
            processed = process(json_data['data'])
            json_data['data'] = processed
            final.append(print_output(json_data))

        # return render_template("grades.html", subjects=final)
        # print(final)
        return redirect(url_for("grades", final=final))
        
@app.route('/logout')
def logout():
    session.clear()
    quit_webdriver()
    return redirect('/')

# @login_required
@app.route('/grades', methods=["GET", "POST"])
def grades():
    final = request.args.getlist("final")
    # final = [final]
    # print(final)
    
    if final:
        subjects = []
        for encoded_data in final:
            decoded_data = urllib.parse.unquote(encoded_data)  # Decode URL-encoded string
            subject_data = ast.literal_eval(decoded_data)  # Safely parse string to a Python dict
            subjects.append(subject_data)

    # Pass the `subjects` data to the template
        return render_template('grades.html', subjects=subjects)    
    else:
        return redirect(url_for("login"))
