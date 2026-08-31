---
name: python-sql-bridge-generator
description: Generates a ready-to-copy Python SQL execution bridge directly in chat, immediately, without asking questions first. Use whenever the ask is "give me the Python to run this SQL file", "how do I connect this query to Python", or similar — a small PostgreSQL-via-SQLAlchemy bridge script the user will copy, set the SQL path on, and run themselves. Not for writing the SQL (use mindful-sql-builder/table-discovery/bgdlot for that) and not for building a reusable script or module in the project — this is specifically a quick copy-paste snippet, generated on the spot even with no file path given. Never executes the code and never writes a .py file unless explicitly asked.
---

# Python SQL Execution Bridge Generator

Generate a ready-to-copy Python SQL execution bridge directly in chat. The
user copies the code, sets the SQL file path, and runs it themselves. Do
not execute the Python and do not create a `.py` file unless explicitly
requested.

## Architecture

```
Python → reads .sql file → connects to PostgreSQL → PostgreSQL executes SQL → Python prints results
```

Python only handles execution. All business logic — dates, filters, joins,
calculations, business rules — stays inside SQL.

## Environment

Assume PostgreSQL credentials exist in `.env`:

```
host=localhost
database=db
user=usr
password=pwd
```

Use: `pathlib`, `os`, `python-dotenv`, `SQLAlchemy`, `psycopg`.

## Required output

Immediately generate this complete Python code in chat:

```python
from pathlib import Path
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Load database credentials
load_dotenv()
host = os.getenv("host")
database = os.getenv("database")
user = os.getenv("user")
password = os.getenv("password")

# 2. Connect to PostgreSQL
engine = create_engine(
    f"postgresql+psycopg://{user}:{password}@{host}/{database}"
)

# 3. Read SQL script
sql = Path("PATH_TO_YOUR_SQL_FILE.sql").read_text(
    encoding="utf-8"
)

# 4. Send SQL to PostgreSQL and get results
with engine.connect() as connection:
    result = connection.execute(text(sql))
    rows = result.fetchall()

# 5. Output results
for row in rows:
    print(row)
```

## SQL path behavior

If the user provides a SQL file path, insert it automatically. If no SQL
file path is provided, use `Path("PATH_TO_YOUR_SQL_FILE.sql")` as a
placeholder. Do not ask for the SQL file path — generate immediately either
way, and let the user replace the placeholder manually if needed.

## Rules

- Generate the complete Python runner immediately.
- Output it directly in chat for copy-paste.
- Do not ask questions before generating it.
- Do not execute it.
- Do not create a `.py` file.
- Do not rewrite SQL into Python.
- Do not move dates, filters, joins, calculations, or business rules into Python.
- Do not modify the SQL.
- Do not add parameters unless explicitly requested.
- Do not add pandas, JSON, APIs, functions, or unnecessary abstractions.
- Keep the runner lightweight.

## Core rule

Generate first. The user edits the SQL path. Python executes; SQL calculates.
