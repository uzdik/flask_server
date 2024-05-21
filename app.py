from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import JavascriptException, TimeoutException
from urllib.parse import quote as url_quote
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
import time

app = Flask(__name__)

# Configure CORS
cors = CORS(app, resources={
    r"/submit": {
        "origins": ["https://uzdik.github.io"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "https://uzdik.github.io"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    app.logger.debug("Received request")
    data = request.json
    app.logger.debug(f"Request data: {data}")
    
    login = "uzdik.kz"
    parol = "codeforces2012kz"
    enter_url = "https://codeforces.com/enter"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)  
    app.logger.debug("Chrome WebDriver started")

    try:
        driver.get(enter_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "handleOrEmail")))

        username_input = driver.find_element(By.ID, "handleOrEmail")
        password_input = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.CLASS_NAME, "submit")

        username_input.send_keys(login)
        password_input.send_keys(parol)
        submit_button.click()

        WebDriverWait(driver, 10).until(EC.url_changes(enter_url))
        app.logger.debug("Logged in to Codeforces")

        user = data["user"]
        typeContest = data["typeContest"]
        contestId = data["contestId"]
        problem_id = data["problem_id"]
        language_id = int(data["language_id"])
        source_code = f'# {user}\n{data["source_code"]}'
    
        submit_url = f"https://codeforces.com/{typeContest}/{contestId}/submit"
        driver.get(submit_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "submittedProblemIndex")))
        app.logger.debug(f"Navigated to submit URL: {submit_url}")
    
        driver.execute_script(f"document.querySelector('select[name=\"submittedProblemIndex\"]').value = '{problem_id}';")
        app.logger.debug(f"Problem index selected: {problem_id}")

        driver.execute_script(f"document.querySelector('select[name=\"programTypeId\"]').value = {language_id};")
        app.logger.debug(f"Language selected: {language_id}")
    
        checkbox = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "toggleEditorCheckbox")))
        checkbox.click()
        if not checkbox.is_selected():
            checkbox.click()
        driver.execute_script("document.getElementById('sourceCodeTextarea').value = arguments[0];", source_code)
        app.logger.debug(f"Source code set: {source_code}")
    
        button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "singlePageSubmitButton")))
        button.click()
        app.logger.debug("Submitted code")
    
        system_time = driver.execute_script("return new Date().toLocaleString();")
        system_time = datetime.strptime(system_time, "%m/%d/%Y, %I:%M:%S %p")
        system_time = system_time.replace(second=0)
        app.logger.debug(f"System time in browser context: {system_time}")

	# Wait for 30 seconds before starting to process the rows
        app.logger.debug("Waiting for 30 seconds before processing rows")
        time.sleep(30)
        app.logger.debug("Wait complete, starting to process rows")

        res_url = f"https://codeforces.com/{typeContest}/{contestId}/my"
        driver.get(res_url)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        app.logger.debug("Fetched results page")
    
        rows = soup.find_all("tr")
        return_back_data = []
    	
        for row in rows:
            submission_time_elem = row.find("td", class_="status-small")
            if submission_time_elem:
                submission_time_str = submission_time_elem.text.strip()
                submission_time_str = re.search(r'\w+/\d{2}/\d{4} \d{2}:\d{2}', submission_time_str).group()
                submission_time = datetime.strptime(submission_time_str, "%b/%d/%Y %H:%M")
                if submission_time == system_time:
                    submission_id = row.find("a", class_="view-source")["submissionid"]
                    verdict_elem = row.find("span", class_="verdict-accepted")
                    verdict = verdict_elem.text.strip() if verdict_elem else "Partial"
                    points_elem = row.find("span", class_="verdict-format-points")
                    points = points_elem.text.strip() if points_elem else "Points not found"
                    
                    return_back_data = [submission_time.strftime('%a, %d %b %Y %H:%M:%S GMT'), submission_id, points, verdict]
                    app.logger.debug(f"Submission found: {return_back_data}")
                    break
    
        driver.quit()
        app.logger.debug("Chrome WebDriver closed")
        
        response_data = {"message": "Submission successful!", "data": return_back_data}
        response = jsonify(response_data)
    
        # Set CORS headers
        response.headers.add("Access-Control-Allow-Origin", "https://uzdik.github.io")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        
    except TimeoutException as e:
        app.logger.error(f"Timeout error: {e}")
        return jsonify({"error": "Timeout error"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error"}), 500
    finally:
        driver.quit()
        app.logger.debug("Chrome WebDriver closed")
    
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
