

import requests

BASE_URL = "https://saas.jfcdt.cn"

def get_token(username, password, base_url=BASE_URL, headers=None):
    endpoint='/saas/aiReport/login'
    headers = {
        "Content-Type": "application/json"
    }
    body = {
        "username": username,
        "password": password
    }
    response = requests.post(f"{base_url}/{endpoint}", headers=headers, json=body)
    response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    return response.json()