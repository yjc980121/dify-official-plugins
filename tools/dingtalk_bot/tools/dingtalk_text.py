from collections.abc import Generator
from typing import Any
import httpx
import time
import hmac
import hashlib
import base64
import urllib
import logging
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class DingtalkBotTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        invoke tools
        Dingtalk custom group robot API docs:
        https://open.dingtalk.com/document/orgapp/custom-robot-access
        """
        content = tool_parameters.get("content")
        if not content:
            yield self.create_text_message("Invalid parameter content")
        at_mobiles: str = tool_parameters.get("atMobiles")
        atMobiles: list[str] = []
        if at_mobiles:
            atMobiles = at_mobiles.strip().split(",")
        isAtAll: bool = tool_parameters.get("isAtAll")
        access_token = tool_parameters.get("access_token")
        if not access_token:
            yield self.create_text_message(
                "Invalid parameter access_token. Regarding information about security details,please refer to the DingTalk docs:https://open.dingtalk.com/document/robots/customize-robot-security-settings"
            )
        sign_secret = tool_parameters.get("sign_secret")
        if not sign_secret:
            yield self.create_text_message(
                "Invalid parameter sign_secret. Regarding information about security details,please refer to the DingTalk docs:https://open.dingtalk.com/document/robots/customize-robot-security-settings"
            )
        msgtype = "text"
        api_url = "https://oapi.dingtalk.com/robot/send"
        headers = {"Content-Type": "application/json"}
        params = {"access_token": access_token}
        self._apply_security_mechanism(params, sign_secret)
        payload = {"msgtype": msgtype, "text": {"content": content}, "at": {}}
        if atMobiles:
            payload["at"]["atMobiles"] = atMobiles
        if isAtAll:
            payload["at"]["isAtAll"] = isAtAll
        try:
            res = httpx.post(api_url, headers=headers, params=params, json=payload)
            if res.is_success:
                yield self.create_text_message("Text message sent successfully")
            else:
                yield self.create_text_message(
                    f"Failed to send the text message, status code: {res.status_code}, response: {res.text}"
                )
        except Exception as e:
            yield self.create_text_message(
                "Failed to send message to group chat bot. {}".format(e)
            )

    @staticmethod
    def _apply_security_mechanism(params: dict[str, Any], sign_secret: str):
        try:
            timestamp = str(round(time.time() * 1000))
            secret_enc = sign_secret.encode("utf-8")
            string_to_sign = f"{timestamp}\n{sign_secret}"
            string_to_sign_enc = string_to_sign.encode("utf-8")
            hmac_code = hmac.new(
                secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
            ).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            params["timestamp"] = timestamp
            params["sign"] = sign
        except Exception:
            msg = "Failed to apply security mechanism to the request."
            logging.exception(msg)
