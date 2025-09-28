# Project Coding Rules (Non-Obvious Only)

- Always use `safeWriteJson()` from `app/utils.py` instead of direct JSON writes
- Database queries MUST use the query builder in `app/sql_tool.py` (raw SQL will fail)
- Role classification requires both rule-based and LLM validation steps
- Test files must be co-located with source files (not in separate test directory)
- PDF ingestion requires fallback to filename analysis if LLAMA_CLOUD_API_KEY missing