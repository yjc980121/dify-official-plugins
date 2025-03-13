from collections.abc import Generator
from typing import Any
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
import re
import json
from json_repair import repair_json
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class JsonRepaireTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        text = tool_parameters.get("text")
        if not text:
            yield self.create_json_message({
                "result": {
                    "success": False,
                    "error": "No text parameter provided"
                }
            })
        convert_json = tool_parameters.get("convert_json")

        # 1.定义返回数据
        json_data = {}

        # 2.修复不完整的markdown
        fixed_markdown = self.fix_incomplete_markdown(text)

        # 3.从 Markdown 中提取代码块
        code_block = self.extract_code_block_from_markdown(fixed_markdown)
        if not code_block:
            # 如果没有找到代码块，直接尝试解析原始文本是否为 JSON
            if self.is_json(text):
                code_block = text
        
        # 4. 如果要解析json
        if convert_json:
            # 3.修复不完整的json
            fixed_json = self.fix_incomplete_json(code_block)
            # 尝试解析修复后的 JSON
            try:
                json_data = json.loads(fixed_json)
            except Exception:
                json_data = {}

        yield self.create_json_message({
            "code_blocks": code_block, "json_data": json_data
        })

    # 使用 markdown来修复markdown
    def fix_incomplete_markdown(self, text: str) -> str:
        """
        修复不完整的 Markdown 代码块。
        """
        # 如果代码块缺少闭合的反引号 ```，尝试修复
        if text.count("```") % 2 != 0:  # 如果反引号的数量不是偶数
            text += "\n```"  # 自动补全闭合的反引号

        # 使用 markdown 库解析 Markdown，确保代码块正确闭合
        md = markdown.Markdown(extensions=[FencedCodeExtension()])
        md.convert(text)  # 尝试解析 Markdown
        return text

    def extract_code_block_from_markdown(self, text: str) -> str:
        """
        从 Markdown 中提取代码块（可能是 JSON 或其他类型）。
        """
        # 优化正则表达式，匹配完整的 Markdown 代码块
        code_block_pattern = re.compile(r'```(?:.*?\n)?(.*?)\n```', re.DOTALL)

        # 查找所有匹配的代码块
        code_blocks = code_block_pattern.findall(text)

        if code_blocks:
            return code_blocks[0]  # 返回第一个匹配的代码块
        else:
            return ""  # 如果没有找到代码块，返回空字符串

    def is_json(self, text: str) -> bool:
        """
        判断字符串是否可能是 JSON（即使不完整）。
        """
        # 去除空白字符
        text = text.strip()

        # 如果字符串以 { 或 [ 开头，可能是 JSON
        if text.startswith("{") or text.startswith("["):
            return True

        # 如果字符串包含 JSON 的关键字（如 "key": "value"），可能是 JSON
        if re.search(r'"\s*:\s*"', text):
            return True

        # 如果字符串包含 JSON 的常见结构（如数组或对象），可能是 JSON
        if re.search(r'{\s*".*?"\s*:\s*".*?"\s*}', text):
            return True

        return False

    # 使用json_repair来修复json
    def fix_incomplete_json(self, text: str) -> str:
        return repair_json(text, skip_json_loads=True)

    def extract_json(self, text: str) -> dict:
        # 第一步：修复不完整的 Markdown
        fixed_markdown = self.fix_incomplete_markdown(text)

        # 第二步：从 Markdown 中提取代码块
        code_block = self.extract_code_block_from_markdown(fixed_markdown)

        if not code_block:
            # 如果没有找到代码块，直接尝试解析原始文本是否为 JSON
            if self.is_json(text):
                code_block = text
            else:
                return {"error": "No valid JSON found", "original": text}

        # 第三步：修复不完整的 JSON
        fixed_json = self.fix_incomplete_json(code_block)

        # 第四步：尝试解析修复后的 JSON
        try:
            json_data = json.loads(fixed_json)
            return {"result": json_data, "all": [fixed_json]}  # 返回解析后的 JSON
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse JSON: {e}", "original": code_block}
