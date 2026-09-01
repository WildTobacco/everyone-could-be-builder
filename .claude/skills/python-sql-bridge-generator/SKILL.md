---
name: python-sql-bridge-generator
description: Generates a Python SQL execution bridge from an inline query. Invoked as `/python-sql-bridge-generator [file path] [name]`, it writes `[name].py` to `[file path]` containing the bridge code — that's the primary path. Without both a file path and a name, it falls back to printing the same code directly in chat for copy-paste instead of writing a file. Use whenever the ask is "give me the Python to run this SQL", "generate a script that connects to Postgres and runs this query", or similar. Not for writing the SQL itself (use mindful-sql-builder/table-discovery/bgdlot for that) — this only wires an already-written query to a PostgreSQL connection via SQLAlchemy. Never executes the generated script.
---

# Python SQL Execution Bridge Generator

Generate a Python SQL execution bridge. Python only handles the connection
and execution — all business logic (dates, filters, joins, calculations,
business rules) stays inside the SQL string itself.

## Architecture

```
Python → connects to PostgreSQL → PostgreSQL executes SQL → Python prints results
```

## Environment

Assume PostgreSQL credentials exist in `.env`:

```
host=localhost
database=db
user=usr
password=pwd
```

Use: `os`, `python-dotenv`, `SQLAlchemy`, `psycopg`.

## Code template

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
host = os.getenv("host")
database = os.getenv("database")
user = os.getenv("user")
password = os.getenv("password")

engine = create_engine(
    f"postgresql+psycopg://{user}:{password}@{host}/{database}"
)

sql = """
SELECT *
FROM table
LIMIT 5;
"""

with engine.connect() as connection:
    result = connection.execute(text(sql))
    rows = result.fetchall()

for row in rows:
    print(row)
```

Swap `table` in the `sql` string for whatever the user names, and adjust
the query itself (columns, filters, limit) if they specify one — but never
add logic beyond what they asked for. If the user gives an exact query to
use verbatim, use it as given even if the print loop would need adjusting
to match its actual column shape — flag the mismatch rather than silently
"fixing" it.

## Invocation and output mode

Invoked as `/python-sql-bridge-generator [file path] [name]`:

- Write the code above to `[name].py` at `[file path]`.
- Do not execute the generated script.
- Confirm what was written and where.

Invoked without both a file path and a name (e.g. just describing what's
needed in chat): don't ask for the missing arguments — instead, print the
same code directly in chat as a copy-paste snippet, same as if no file
were being created.

## Rules

- Don't rewrite SQL logic into Python — the `sql` string is the one place
  business logic lives.
- Don't modify a query the user gave verbatim.
- Don't add parameters, pandas, JSON, APIs, or other abstractions unless
  explicitly requested.
- Keep the bridge lightweight — a connect-execute-print script, not a
  framework.
- Never execute the script yourself, whether it was written to disk or
  only printed in chat.

## Core rule

Python executes; SQL calculates. Write the file when given a path and name;
otherwise print the snippet.
