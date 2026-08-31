---
name: postgresql-python-bridge
description: Generates a lightweight Python script that connects to PostgreSQL, runs a .sql file exactly as written, and returns the result in a form an AI agent or another Python process can consume. Use this whenever the task is to wire finished SQL up to Python/an agent — "run this query from Python", "build a script that executes my .sql file", "load DB credentials from .env and return the rows as JSON" — not for writing the SQL itself (that's mindful-sql-builder/table-discovery/bgdlot) and not for one-off ad-hoc queries where a plain psql call would do. Keeps a strict separation: SQL owns every bit of business logic (dates, filters, joins, calculations, ranking); Python only loads credentials, connects, executes, and returns results — never re-derives logic that already lives in the query.
---

# PostgreSQL Python Bridge

Generate a small Python script that connects to PostgreSQL, executes a
`.sql` file exactly as written, and returns the result in a form usable by
an AI agent or another Python process.

## The core separation

SQL owns all business logic — dates, filters, joins, calculations,
aggregations, ranking, business rules. Never rewrite SQL logic into Python.
Python's job is strictly: load credentials, connect, load the SQL text,
execute it, return results or errors. If a query needs to change, that
change happens in the `.sql` file, not by adding logic in Python around the
call.

> Python executes. PostgreSQL calculates. SQL defines the logic.

## Default stack

- `python-dotenv` — load credentials from `.env`
- `SQLAlchemy` — connection/engine layer
- `psycopg` — the actual PostgreSQL driver (via SQLAlchemy's `postgresql+psycopg` dialect)
- `pathlib` — read the `.sql` file

Assume `.env` holds:

```
host=localhost
database=db
user=usr
password=pwd
```

## Default project structure

```
project/
├── .env
├── run_sql.py
└── sql/
    └── query.sql
```

## Default behavior

Absent other instructions, generate something equivalent to:

```python
from pathlib import Path
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

sql = Path("sql/query.sql").read_text(encoding="utf-8")

with engine.connect() as connection:
    result = connection.execute(text(sql))
    rows = result.fetchall()

for row in rows:
    print(row)
```

## AI-readable output

When the script is meant to hand results to an AI agent (rather than a
human reading stdout), prefer structured, JSON-compatible output:

```python
columns = list(result.keys())
rows = [list(row) for row in result.fetchall()]
output = {
    "columns": columns,
    "rows": rows,
    "row_count": len(rows),
}
```

## Questions to ask first

Only what's necessary to generate the right script — don't interrogate
business logic that already lives in the SQL:

- Which `.sql` file should be executed?
- Should results be printed, returned as Python data, or JSON?
- Is the query read-only, or can it modify data?
- Is this a one-off script, or a reusable `run_sql()` function?

Never ask about the calculations, filters, or business rules inside the
query itself — that's the SQL's job to define, and this skill's job to
leave alone.

## Safety

For a bridge an AI agent will call, prefer read-only database credentials
where possible. When the bridge is meant to be read-only:

- don't generate write operations (INSERT/UPDATE/DELETE/DDL)
- don't alter the SQL being executed — run it exactly as given
- surface PostgreSQL errors clearly rather than swallowing them
- consider an optional row-limit safeguard for large result sets, so a
  runaway query doesn't hand back an unbounded result to the caller
