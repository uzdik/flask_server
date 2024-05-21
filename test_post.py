import requests

url = "http://127.0.0.1:5000/submit"
headers = {'Content-Type': 'application/json'}
data = {
    "user": "Uzdik User",
    "typeContest": "gym",
    "contestId": "515622",
    "problem_id": "A",
    "language_id": "31",
    "source_code": "# localserver \nprint(int(input())+int(input()))"
}

response = requests.post(url, json=data)
print(response.json())
