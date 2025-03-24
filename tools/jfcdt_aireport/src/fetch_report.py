import requests
from .constants import CATE_TYPE

BASE_URL = "https://saas.jfcdt.cn/saas"

def fetch_report(token: str, report_no: str, root_tag: str, base_url: str = BASE_URL) -> dict:
    endpoint='/aiReport/reportRequest'
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "reportNo": report_no,
        "rootTag": root_tag
    }
    response = requests.post(f"{base_url}{endpoint}", headers=headers, json=body, timeout=10)
    response.raise_for_status()
    result = response.json()
    if result.get("code") == "99100000":
        result_data = result.get('data', {})
        result=result_data.get('result', {})
        root_tag = result_data.get('rootTag','')
        status = result_data.get('status', '1')
        print(result_data)
        if not result:
            return []
        if status != '2':
            return []
        """
        return {
            "id": result_data.get('id'),
            "reportNo": result_data.get('reportNo'),
            "companyId": result_data.get('companyId'),
            "requestSn": result_data.get('requestSn'),
            "reqTime": result_data.get('reqTime'),
            "query": result_data.get('query'),
            "result": result_data.get('result'),
            "rootTag": root_tag,
            "rootTagName": CATE_TYPE.get(root_tag,{}).get('name'),
            "userId": result_data.get('userId'),
            "status": result_data.get('status'),  # 1是解析中,2 ，3是解析异常
        }
        """
        return {
            "reportNo": result_data.get('reportNo'),
            "companyId": result_data.get('companyId'),
            "result": result_data.get('result'),
            "rootTag": root_tag,
            "rootTagName": CATE_TYPE.get(root_tag,{}).get('name')
        }
    return []


if __name__ == "__main__":
    ret=fetch_report(token="50531faf-5af5-444a-88d7-d61f53270550", report_no="I202503201115060001", root_tag="corpAnnualAssets", base_url="https://saas.jfcdt.cn/saas")
    print(ret)

