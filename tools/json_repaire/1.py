from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Body, FastAPI, Form
from json_repair import repair_json
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
import re
import json

from pydantic import BaseModel
router = APIRouter()


class Res(BaseModel):
    code_blocks: str
    json_data: Optional[Union[List[Dict], Dict]] = None


# 使用 markdown来修复markdown
def fix_incomplete_markdown(text: str) -> str:
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


def extract_code_block_from_markdown(text: str) -> str:
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


def is_json(text: str) -> bool:
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


def fix_incomplete_json(text: str) -> str:
    return repair_json(text, skip_json_loads=True)


def extract_json(text: str) -> dict:
    # 第一步：修复不完整的 Markdown
    fixed_markdown = fix_incomplete_markdown(text)

    # 第二步：从 Markdown 中提取代码块
    code_block = extract_code_block_from_markdown(fixed_markdown)

    if not code_block:
        # 如果没有找到代码块，直接尝试解析原始文本是否为 JSON
        if is_json(text):
            code_block = text
        else:
            return {"error": "No valid JSON found", "original": text}

    # 第三步：修复不完整的 JSON
    fixed_json = fix_incomplete_json(code_block)

    # 第四步：尝试解析修复后的 JSON
    try:
        json_data = json.loads(fixed_json)
        return {"result": json_data, "all": [fixed_json]}  # 返回解析后的 JSON
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON: {e}", "original": code_block}


@router.post("/json_repair", description="json修复工具", summary="json修复工具")
async def repair(
    text: str = Form(..., description="消息内容"),
    convert_json: Optional[bool] = Form(True, description="是否转换json")
):
    json_data = {}
    # 修复不完整的markdown
    fixed_markdown = fix_incomplete_markdown(text)

    # 第二步：从 Markdown 中提取代码块
    code_block = extract_code_block_from_markdown(fixed_markdown)
    if not code_block:
        # 如果没有找到代码块，直接尝试解析原始文本是否为 JSON
        if is_json(text):
            code_block = text

    if convert_json:
        # 修复不完整的json
        fixed_json = fix_incomplete_json(code_block)
        # 尝试解析修复后的 JSON
        try:
            json_data = json.loads(fixed_json)
        except:
            json_data = {}

    return {"code_blocks": code_block, "json_data": json_data}  # 返回解析后的 JSON

    # from json_repair import repair_json
    # good_json_string = repair_json(text, skip_json_loads=True)
    good_json_string = extract_json(text).get('result')
    return good_json_string


# 启动 FastAPI 应用
if __name__ == "__main__":
    import uvicorn
    app = FastAPI()
    app.include_route(router)
    uvicorn.run(app, host="0.0.0.0", port=8000)
