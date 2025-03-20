```json
{
  "query": "请给我推荐几本关于机器学习的书籍。",
  "instruction": "根据用户的需求调用推荐书籍的工具。",
  "model": {
    "name": "GPT-3",
    "version": "3.5",
    "completion_params": {
      "stop": ["\n"]
    }
  },
  "tools": [
    {
      "name": "book_recommender",
      "action": {
        "action_input": {
          "genre": "机器学习",
          "limit": 5
        }
      }
    }
  ],
  "maximum_iterations": 3
}


{
  "output": "推荐的书籍包括《深度学习》、《机器学习》、《统计学习方法》。",
  "tool_name": "book_recommender",
  "tool_input": {
    "genre": "机器学习",
    "limit": 5
  }
}

```