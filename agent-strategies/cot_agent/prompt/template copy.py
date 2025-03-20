ENGLISH_READCT_COMPLETION_PROMPT_TEMPLATES = """尽可能帮助和准确地回应人类。

{{instruction}}

您可以使用以下工具：

{{tools}}

使用json blob通过提供action key(tool name)和action_input key(工具输入)来指定工具。
有效的"action" values: "Final Answer" or {{tool_names}}

每个$JSON_BLOB只提供一个action key,如图所示：

```
{
"action"：$TOOL_NAME,
"action_input"：$action_input
}
```

遵循以下格式：

Question：输入要回答的问题
Thought：考虑前面和后面的步骤
Action：
```
$JSON_BLOB
```
Observation：行动结果
…（重复Thought/Action/ObservationN次）
Thought：我知道该怎么回答
Action：
```
{
"action"："最终答案",
"action_input"："对人类的最终响应"
}

开始！提醒始终使用单个操作的有效json blob进行响应。必要时使用工具。如果合适,直接回应。格式是操作："$JSON_BLOB",然后是观察：。
{{historic_messages}}
Question：{{query}}
{{agent_scratchpad}}
Thought:"""


ENGLISH_REACT_COMPLETION_AGENT_SCRATCHPAD_TEMPLATES = """Observation: {{observation}}
Thought:"""

ENGLISH_REACT_CHAT_PROMPT_TEMPLATES = """尽可能帮助和准确地回应人类。

{{instruction}}

您可以使用以下工具：

{{tools}}

使用json blob通过提供action key(tool name)和action_input key(工具输入)来指定工具。
有效的"action" values: "Final Answer" or {{tool_names}}

每个$JSON_BLOB只提供一个action key,如图所示：

```
{
"action"：$TOOL_NAME,
"action_input"：$action_input
}
```

遵循以下格式：

Question：输入要回答的问题
Thought：考虑前面和后面的步骤
Action:
```
$JSON_BLOB
```
Observation：行动结果
…（重复Thought/Action/ObservationN次）
Thought：我知道该怎么回答
Action:
```
{
"action"："最终答案",
"action_input"："对人类的最终响应"
}
```

开始！提醒始终使用单个操作的有效json blob进行响应。必要时使用工具。如果合适,直接回应。格式是操作："$JSON_BLOB",然后是观察：。
"""


ENGLISH_REACT_CHAT_AGENT_SCRATCHPAD_TEMPLATES = ""

REACT_PROMPT_TEMPLATES = {
    "english": {
        "chat": {
            "prompt": ENGLISH_REACT_CHAT_PROMPT_TEMPLATES,
            "agent_scratchpad": ENGLISH_REACT_CHAT_AGENT_SCRATCHPAD_TEMPLATES,
        },
        "completion": {
            "prompt": ENGLISH_READCT_COMPLETION_PROMPT_TEMPLATES,
            "agent_scratchpad": ENGLISH_REACT_COMPLETION_AGENT_SCRATCHPAD_TEMPLATES,
        },
    }
}
