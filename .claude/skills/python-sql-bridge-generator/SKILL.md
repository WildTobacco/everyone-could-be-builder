---
name: python-sql-bridge-generator
description: When the user provides or names a .sql file, generates a ready-to-copy Python runner directly in the chat — never executes it, never writes a .py file, unless explicitly asked. Use whenever the ask is "give me the Python to run this SQL file", "how do I connect this query to Python", or similar — a small PostgreSQL-via-SQLAlchemy bridge script the user will copy and run themselves. Not for writing the SQL (use mindful-sql-builder/table-discovery/bgdlot for that) and not for building a reusable script or module in the project (that's a different, more involved task) — this is specifically a quick copy-paste snippet for one named .sql file. Keeps the runner minimal: SQL owns all business logic, Python is only the bridge.
---

# Python SQL Execution Bridge Generator

When the user provides or identifies a `.sql` script, generate a
ready-to-copy Python runner directly in the chat. The user copies and runs
it themselves — do not execute the Python, and do not create a `.py` file,
unless explicitly asked to do either.

## Architecture

```
Python → reads .sql file → connects to PostgreSQL → PostgreSQL executes SQL → Python prints results
```

Python is only the bridge. All business logic — dates, filters, joins,
calculations, business rules — stays inside the `.sql` file untouched.

## Environment

Assume PostgreSQL credentials already exist in `.env`:

```
host=localhost
database=db
user=usr
password=pwd
```

Use: `pathlib`, `os`, `python-dotenv`, `SQLAlchemy`, `psycopg`.

## Output pattern

Generate this directly in the chat, adapting only the SQL file path:

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
sql = Path("sql/customer_profit.sql").read_text(
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

## Adaptation

Replace only the SQL file path as required. If the user says:

> SQL file is `sql/check_duplicates.sql`

generate:

```python
sql = Path("sql/check_duplicates.sql").read_text(
    encoding="utf-8"
)
```

If the file path is unknown, ask for it before generating the final runner
— don't guess a path.

## Rules

- Output the complete, copy-paste-ready Python code in chat.
- Don't execute it.
- Don't create a `.py` file.
- Don't rewrite SQL into Python.
- Don't move dates, filters, joins, calculations, or business rules into Python.
- Don't modify the SQL script unless explicitly requested.
- Don't add reporting-date parameters unless explicitly requested.
- Don't add pandas, JSON, APIs, functions, or other abstractions unless requested.
- Keep the runner simple — this is a quick bridge snippet, not a mini-framework.

## Explanation

When useful, explain in plain language: `.env` gives Python the login →
Python connects → Python reads the SQL file → PostgreSQL does the actual
calculation → Python prints whatever PostgreSQL returned.

## Core rule

Generate the Python runner in chat. Python executes; SQL calculates.
