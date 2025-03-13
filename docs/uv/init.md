cd ..\openai_compatible\
uv init -p 3.12
uv venv
uv add -r .\requirements.txt
uv run python -c "import os; os.remove('hello.py') if os.path.exists('hello.py') else None"

uv run python -m main

