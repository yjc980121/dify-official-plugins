from fastapi import APIRouter, FastAPI, Query, HTTPException, Body
import httpx
import hmac
import hashlib
import base64
import time
import urllib.parse
from typing import List, Dict, Optional
import logging
import json

router = APIRouter()


def cal_sign(secret):
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(secret.encode(
        'utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


async def send_dingtalk_message(access_token: str, sign_secret: str, payload: dict):
    timestamp, sign = cal_sign(sign_secret)
    base_url = 'https://oapi.dingtalk.com/robot/send'
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        'access_token': access_token,
        'timestamp': timestamp,
        'sign': sign
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(base_url, headers=headers, params=params, json=payload)
        if response.status_code == 200:
            return {"message": "消息发送成功"}
        else:
            return {"message": f"消息发送失败，状态码: {response.status_code}"}


@router.post("/send_message", description="钉钉机器人,发送消息", summary="钉钉机器人发送消息")
async def send_message(
    access_token: str = Query(..., description="钉钉机器人访问令牌"),
    sign_secret: str = Query(..., description="钉钉机器人签名密钥"),
    msgtype: str = Body(..., description="消息类型"),
    text: str = Body(..., description="消息内容"),
    title: Optional[str] = Body("默认标题", description="消息标题"),
    atMobiles: Optional[List[str]] = Body(None, description="被@人的手机号"),
    isAtAll: Optional[bool] = Body(False, description="@所有人"),
    picUrl: Optional[str] = Body(None, description="图片URL"),
    messageUrl: Optional[str] = Body(None, description="点击消息跳转的URL"),
    singleTitle: Optional[str] = Body(None, description="单个按钮的标题"),
    singleURL: Optional[str] = Body(None, description="单个按钮的URL"),
    btns: Optional[List] = Body(None, description="按钮列表"),
    links: Optional[List] = Body(None, description="链接列表")
):
    payload = {
        "msgtype": msgtype,
    }

    if msgtype == "text":
        payload["text"] = {
            "content": text
        }
        payload["at"] = {
            "atMobiles": atMobiles,
            "isAtAll": isAtAll
        }
    elif msgtype == "link":
        payload["link"] = {
            "text": text,
            "title": title,
            "picUrl": picUrl,
            "messageUrl": messageUrl
        }
    elif msgtype == "markdown":
        payload["markdown"] = {
            "title": title,
            "text": text
        }
        payload["at"] = {
            "atMobiles": atMobiles,
            "isAtAll": isAtAll
        }
    elif msgtype == "actionCard":
        payload["actionCard"] = {
            "title": title,
            "text": text,
            "hideAvatar": "0",
            "btnOrientation": "0",
            "singleTitle": singleTitle,
            "singleURL": singleURL,
            "btns": btns
        }
    elif msgtype == "feedCard":
        payload["feedCard"] = {
            "links": links
        }
    else:
        raise HTTPException(status_code=400, detail="不支持的消息类型")

    return await send_dingtalk_message(access_token, sign_secret, payload)


@router.post("/send_text_message", description="钉钉机器人,发送text消息", summary="钉钉机器人发送text消息")
async def send_text_message(
    access_token: str = Query(..., description="钉钉机器人访问令牌"),
    sign_secret: str = Query(..., description="钉钉机器人签名密钥"),
    text: str = Body(..., description="消息内容"),
    atMobiles: Optional[List[str]] = Body(None, description="被@人的手机号"),
    isAtAll: Optional[bool] = Body(False, description="@所有人")
):
    payload = {
        "msgtype": "text",
        "text": {
            "content": text
        },
        "at": {
            "atMobiles": atMobiles,
            "isAtAll": isAtAll
        }
    }
    return await send_dingtalk_message(access_token, sign_secret, payload)


@router.post("/send_link_message", description="钉钉机器人, 发送link消息", summary="钉钉机器人发送link消息")
async def send_link_message(
    access_token: str = Query(..., description="钉钉机器人访问令牌"),
    sign_secret: str = Query(..., description="钉钉机器人签名密钥"),
    text: str = Body(..., description="消息内容"),
    title: Optional[str] = Body("默认标题", description="消息标题"),
    picUrl: Optional[str] = Body(None, description="图片URL"),
    messageUrl: Optional[str] = Body(None, description="消息URL"),
):
    payload = {
        "msgtype": "link",
        "link": {
            "text": text,
            "title": title,
            "picUrl": picUrl,
            "messageUrl": messageUrl
        }
    }
    return await send_dingtalk_message(access_token, sign_secret, payload)


@router.post("/send_markdown_message", description="钉钉机器人, 发送markdown消息", summary="钉钉机器人发送markdown消息")
async def send_markdown_message(
    access_token: str = Query(..., description="钉钉机器人访问令牌"),
    sign_secret: str = Query(..., description="钉钉机器人签名密钥"),
    text: str = Body(..., description="消息内容"),
    title: Optional[str] = Body("默认标题", description="消息标题"),
    atMobiles: Optional[List[str]] = Body(None, description="被@人的手机号"),
    isAtAll: Optional[bool] = Body(False, description="@所有人")
):
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        },
        "at": {
            "atMobiles": atMobiles,
            "isAtAll": isAtAll
        }
    }
    return await send_dingtalk_message(access_token, sign_secret, payload)


@router.post("/send_action_card_message", description="钉钉机器人, 发送actionCard消息", summary="钉钉机器人发送actionCard消息")
async def send_action_card_message(
    access_token: str = Query(..., description="钉钉机器人访问令牌"),
    sign_secret: str = Query(..., description="钉钉机器人签名密钥"),
    text: str = Body(..., description="消息内容"),
    title: Optional[str] = Body("默认标题", description="消息标题"),
    singleTitle: Optional[str] = Body(None, description="单个按钮的标题"),
    singleURL: Optional[str] = Body(None, description="单个按钮的URL"),
    btns: Optional[List] = Body(None, description="按钮列表")
):
    payload = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": title,
            "text": text,
            "hideAvatar": "0",
            "btnOrientation": "0",
            "singleTitle": singleTitle,
            "singleURL": singleURL,
            "btns": btns
        }
    }
    return await send_dingtalk_message(access_token, sign_secret, payload)


@router.post("/send_feed_card_message", description="钉钉机器人, 发送feedCard消息", summary="钉钉机器人发送feedCard消息")
async def send_feed_card_message(
    access_token: str = Query(..., description="钉钉机器人访问令牌"),
    sign_secret: str = Query(..., description="钉钉机器人签名密钥"),
    links: List[Dict[str, str]] = Body(..., description="链接列表")
):
    payload = {
        "msgtype": "feedCard",
        "feedCard": {
            "links": links
        }
    }
    return await send_dingtalk_message(access_token, sign_secret, payload)


if __name__ == '__main__':
    import uvicorn
    app = FastAPI()
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8203)