import requests
from .constants import CATE_TYPE

BASE_URL = "https://saas.jfcdt.cn"

def fetch_report(token: str, report_no: str, root_tag: str, base_url: str = BASE_URL) -> dict:
    endpoint='/saas/aiReport/reportRequest'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "reportNo": report_no,
        "rootTag": root_tag
    }
    response = requests.post(f"{base_url}/{endpoint}", headers=headers, json=body)
    response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    result = response.json()
    if result.get("code") == "99100000":
        result_data = result.get('data', {})
        return {
            "id": result_data.get('id'),
            "reportNo": result_data.get('reportNo'),
            "companyId": result_data.get('companyId'),
            "requestSn": result_data.get('requestSn'),
            "reqTime": result_data.get('reqTime'),
            "query": result_data.get('query'),
            "result": result_data.get('result'),
            "rootTag": result_data.get('rootTag'),
            "rootTagName": CATE_TYPE.get(result_data.get('rootTag')),
            "userId": result_data.get('userId'),
            "status": result_data.get('status'),  # 1是解析中,2 ，3是解析异常
        }
    return result

