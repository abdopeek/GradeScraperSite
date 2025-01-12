import re
from utils import *
from selenium import webdriver  # use it to open the actual browser for cookies
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys  # to use a keyboard
from selenium.webdriver.support.ui import WebDriverWait  # wait till site loads
from selenium.webdriver.support import expected_conditions as EC  # if conditions for selenium
from selenium.common.exceptions import NoSuchElementException, TimeoutException  # exceptions
from selenium.webdriver.common.by import By  # to locate element
import requests  # to work with requests instead of selenium
import json  # work with the return from the website
from time import sleep  # sleep

s = requests.Session()

def set_cookies(cookies, header):
    default = ['messagesUtk=50c6732c976448b3abbeadcea96c0180', '', '']
    for cookie in cookies:
        updated = f"{cookie['name']}={cookie['value']}"
        if cookie['name'] == "SelfService":
            default[2] = updated
        elif cookie['name'] == "ASP.NET_SessionId":
            default[1] = updated
        header['cookie'] = ';'.join(default)


def enterUsername(username, driver):
    try:
        search = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="txtUserName"]'))
        )
        search.send_keys(username)
        search.send_keys(Keys.RETURN)
    except NoSuchElementException:
        print("Username element not found, exiting")
        driver.quit()
    except TimeoutException:
        print("Time out")
        driver.quit()


def enterPassword(password, driver):
    try:
        search = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="txtPassword"]'))
        )
        search.send_keys(password)
        search.send_keys(Keys.RETURN)
    except NoSuchElementException:
        print("Password element not found, exiting")
        driver.quit()
    except TimeoutException:
        print("Time out")
        driver.quit()
    

def get_student_id(driver):
    url = 'https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Registration/Schedule'
    sleep(1.5)
    cookies = driver.get_cookies()
    set_cookies(cookies, section_head)
    resp = s.get(url, headers=section_head)
    pattern = r'<input\s+id="hdnPersonId"\s+type="hidden"\s+value="(\d+)"\s*/>'
    match = re.search(pattern, resp.text)
    if match:
        value = match.group(1)
        return value
    else:
        raise SyntaxError


def get_sections(id, driver):
    sections = []
    url = r'https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Schedule/Student'
    session = {"year": "2024", "term": "FALL", "session": ""}  # update this every semester
    payload = {'personId': id, "yearTermSession": session}
    sleep(1.5)
    cookies = driver.get_cookies()
    set_cookies(cookies, sched_head)
    resp = s.post(url, data=json.dumps(payload), headers=sched_head)
    if resp.status_code == 200:
        resp = resp.json()
    else:
        raise "ERROR"
    data = json.loads(resp)['data']['schedule'][0]['sections']
    for i in data:
        if i:
            data = i
    for section in data:
        if section['eventSubType'] == "Lecture":
            sections.append(section['id'])
    return sections


def get_data(param, driver):
    grade_link = 'https://upeisis.uofcanada.edu.eg/PowerCampusSelfService/Students/ActivityGrades'

    sleep(1.5)  # wait for cookies to load in
    cookies = driver.get_cookies()
    set_cookies(cookies, grades_head)
    outputs = []
    for section in param:
        resp = s.post(grade_link, data=json.dumps(section), headers=grades_head)
        if resp.status_code == 200:  # accepted
            resp = resp.json()
        else:
            return "Error"
        try:
            json_value = json.loads(resp)['data']
            output = {
                'name': json_value['sectionName'],
                'data': json_value
            }
        except:
            pass
        else:
            outputs.append(output)

    driver.quit()
    return outputs


def process(data):
    # Use list comprehensions to optimize loops
    data['finaltermAssignments'] = [
        {
            'description': item['description'],
            'studentAssignments': [
                {
                    'activityScore': assignment['activityScore'],
                    'earnedPoints': assignment['earnedPoints'],
                    'isEarned': assignment['isEarned'],
                    'title': assignment['title'],
                    'possiblePoints': assignment['possiblePoints'],
                }
                for assignment in item['studentAssignments']
            ]
        }
        for item in data['finaltermAssignments']
    ]
    
    # Prepare the final result
    return {
        'finalscore': data['finalScore'],
        'finalTermAssignments': data['finaltermAssignments'],
    }



def print_output(data):
    total_score = 0
    highest_score = 0
    bonuses = 0
    name = data['name']
    scores = data['data']
    assignments = scores['finalTermAssignments']
    final = {"name": name, "assignments": []}
    for assignment in assignments:
        main = {"name": assignment['description'], "sub_assignments": []}
        for sub_assignment in assignment['studentAssignments']:
            sub = {}
            if sub_assignment['isEarned']:
                total_score += float(sub_assignment['earnedPoints'])
                highest_score += float(sub_assignment['possiblePoints'])
                if 'bonus' in sub_assignment['title'].lower():
                    bonuses += float(sub_assignment['earnedPoints'])
                    highest_score -= float(sub_assignment['possiblePoints'])
                sub["title"] = sub_assignment['title']
                sub["total_score"]= float(sub_assignment['earnedPoints'])
                sub["highest_score"] = float(sub_assignment['possiblePoints'])
            else:
                sub["title"] = sub_assignment['title']
                sub["total_score"] = "Not earned yet"
                sub["highest_score"] = float(sub_assignment['possiblePoints'])
            main['sub_assignments'].append(sub)
        final['assignments'].append(main)
    final['highest_grade'] = highest_score
    final["total_score"] = round(total_score, 2)
    
    lost = highest_score - total_score
    lost = round(lost, 2)
    if highest_score >= 100:
        final['letter_grade'] = f"Final score: {get_letter_grade(total_score)} | %{lost} lost" 
    else:
        final['letter_grade'] = f"{get_best_scenario(highest_score, total_score)} | %{lost} lost"

    return final
    try:
        lost = (highest_score - total_score)
        if highest_score == 100:
            print(f"Final score: {total_score:.2f} | ", end="")
            if lost <= 9:
                print("A+")
                print("-------------------------------------------")
                print("-------------------------------------------")
                return
            elif 9 < lost <= 15:
                print("A")
                print("-------------------------------------------")
                print("-------------------------------------------")
                return
            elif 15 < lost <= 20:
                print("A-")
                print("-------------------------------------------")
                print("-------------------------------------------")
                return
            else:
                print("Less than A")
                print("-------------------------------------------")
                print("-------------------------------------------")
                return

        print(f"Final Score: {total_score:.2f}/{highest_score:.2f} | %{lost:.2f} lost")
        if lost <= 9:
            print("Best case scenario: A+")
        elif 9 < lost <= 15:
            print("Best case scenario: A")
        elif 15 < lost <= 20:
            print("Best case scenario: A-")
        else:
            print("Less than A")

        print("-------------------------------------------")
        print("-------------------------------------------")
    except:
        print(f"Final Score: {total_score:.2f}/{highest_score:.2f}")
        print("-------------------------------------------")
        print("-------------------------------------------")


def get_letter_grade(grade):
    grade_ranges = {
        (91, 100): 'A+',
        (85, 90): 'A',
        (80, 84): 'A-',
        (77, 79): 'B+',
        (74, 76): 'B',
        (70, 73): 'B-',
        (67, 69): 'C+',
        (64, 66): 'C',
        (60, 63): 'C-',
        (57, 59): 'D+',
        (54, 56): 'D',
        (50, 53): 'D-',
        (0, 49): 'F'
    }
    
    for range_tuple, letter in grade_ranges.items():
        if range_tuple[0] <= round(grade) <= range_tuple[1]:
            return letter
        
def get_best_scenario(highest, total):
    lost = highest - total
    if lost <= 9:
        return "Best case scenario A+"
    elif 9 < lost <= 15:
        return "Best case scenario A"
    elif 15 < lost <= 20:
        return "Best case scenario A-"
    else:
        return "Less than A"
