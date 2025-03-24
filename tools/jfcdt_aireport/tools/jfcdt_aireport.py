from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from src.fetch_report import fetch_report
from src.constants import CATE_TYPE

class JfcdtAireportTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        token: str = tool_parameters.get("token")
        report_no: str = tool_parameters.get("report_no")
        root_tag: str = tool_parameters.get("root_tag")
        base_url: str = tool_parameters.get("base_url")
        
        if not token or not report_no or not base_url:
            yield self.create_json_message({
                "error": "Missing required parameters"
            })
        results = []
        try:
            if not root_tag:
                for item in CATE_TYPE:
                    result = fetch_report(token, report_no, item, base_url)
                    #print(f"{item}:",result)
                    if result:
                        results.append(result)
            else:
                result = fetch_report(token, report_no, root_tag, base_url)
                #print(f"{root_tag}:",result)
                if result:
                    results.append(result)
            yield self.create_json_message({
                "result": results
            })
        except Exception as e:
            yield self.create_json_message({
                "error": str(e)
            })
        
        
