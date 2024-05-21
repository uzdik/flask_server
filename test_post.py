import requests

url = "http://127.0.0.1:5000/submit"
headers = {'Content-Type': 'application/json'}
data = {
    "user": "Uzdik User",
    "typeContest": "gym",
    "contestId": "515622",
    "problem_id": "A3",
    "language_id": "31",
    "source_code": "# local-server-user \nn = int(input())\nprint(abs(n)%100//10)"
}

response = requests.post(url, json=data)
print(response.json())
