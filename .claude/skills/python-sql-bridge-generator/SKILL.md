---
name: python-sql-bridge-generator
description: Generates a Python SQL execution bridge from an inline query. Invoked as `/python-sql-bridge-generator [file path] [name]`, it writes `[name].py` to `[file path]` containing the bridge code — that's the primary path. Without both a file path and a name, it falls back to printing the same code directly in chat for copy-paste instead of writing a file. Use whenever the ask is "give me the Python to run this SQL", "generate a script that connects to Postgres and runs this query", or similar. Not for writing the SQL itself (use mindful-sql-builder/table-discovery/bgdlot for that) — this only wires an already-written query to a PostgreSQL connection via SQLAlchemy. Never executes the generated script.
---

# Python SQL Execution Bridge Generator

On invocation, before doing anything else, give one short sentence stating
what this skill is about to do — e.g. "Generating the Python bridge for
this query." This is a statement, not a question — it doesn't delay
generating the code, which still happens immediately after.

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
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db
DB_USER=usr
DB_PASSWORD=pwd
```

Use: `os`, `python-dotenv`, `SQLAlchemy`, `psycopg`.

## Code template

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()
config = {
    "DB_HOST": os.getenv("DB_HOST"),
    "DB_PORT": os.getenv("DB_PORT"),
    "DB_NAME": os.getenv("DB_NAME"),
    "DB_USER": os.getenv("DB_USER"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
}

url = URL.create(
    "postgresql+psycopg",
    username=config["DB_USER"],
    password=config["DB_PASSWORD"],
    host=config["DB_HOST"],
    port=int(config["DB_PORT"]),
    database=config["DB_NAME"],
)

engine = create_engine(url)

sql = """
SELECT *
FROM table
LIMIT 5;
"""

with engine.connect() as connection:
    result = connection.execute(text(sql))
    columns = result.keys()
    rows = result.fetchall()

for row in rows:
    print(dict(zip(columns, row)))
```

The output loop is deliberately generic — it zips each row against its
column names instead of unpacking a fixed number of values, so it works
whether the query returns 1 column or 20. Never hardcode a fixed-arity
unpack like `for schema, table in rows` in the generated script; the whole
point of this bridge is that it works for any SQL the user drops in,
without Python needing to know the query's shape ahead of time.

The connection URL is built with `URL.create()`, not an f-string. A
password containing `@`, `:`, or `/` breaks the naive
`f"...://{user}:{password}@{host}..."` interpolation silently (those
characters are URL-structural), and credentials are exactly the kind of
value that isn't guaranteed to avoid them. `URL.create()` handles the
escaping correctly — don't regress this back to string interpolation even
though it's shorter.

Swap `table` in the `sql` string for whatever the user names, and adjust
the query itself (columns, filters, limit) if they specify one — but never
add logic beyond what they asked for.

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
