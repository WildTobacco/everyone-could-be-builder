# Development Log (Full)

## 2026-07-30 — Session summary

### Environment
- VS Code Python interpreter used: `C:/Users/hieupg/AppData/Local/miniconda3/envs/dashboard/python.exe` (Conda env `dashboard`, Python 3.12.13).

### Actions performed
- Inspected project files: `DB_connect.py`, `web_app.py`, `.env`.
- Read `.env` and confirmed database connection variables: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

### Package installs & verifications
- Attempted to install `psycopg2-binary`, `python-dotenv`, `pandas` using the workspace Conda interpreter.
  - Command used:
    ```powershell
    & "C:/Users/hieupg/AppData/Local/miniconda3/envs/dashboard/python.exe" -m pip install psycopg2-binary python-dotenv pandas
    ```
  - Observed network/proxy timeouts (corporate proxy at `proxy.bidv.com.vn:8080`). Guidance: set `HTTP_PROXY`/`HTTPS_PROXY` or use another network.
- Installed `Flask` and verified import/version: `Flask 3.1.3`.
  - Command used:
    ```powershell
    & "C:/Users/hieupg/AppData/Local/miniconda3/envs/dashboard/python.exe" -m pip install Flask
    & "C:/Users/hieupg/AppData/Local/miniconda3/envs/dashboard/python.exe" -c 'import flask; print(flask.__version__)'
    ```
- Installed `openpyxl` and verified import/version: `openpyxl 3.1.5`.
  - Command used:
    ```powershell
    & "C:/Users/hieupg/AppData/Local/miniconda3/envs/dashboard/python.exe" -m pip install openpyxl
    & "C:/Users/hieupg/AppData/Local/miniconda3/envs/dashboard/python.exe" -c 'import openpyxl; print(openpyxl.__version__)'
    ```

### Code debugging & fixes
- `DB_connect.py` initially raised `ModuleNotFoundError: No module named 'psycopg2'` — fixed by installing `psycopg2-binary` into the `dashboard` env.
- `pd.read_sql(...)` warning: pandas recommends SQLAlchemy engine/URI rather than raw DBAPI connection. Recommendation:
  - Use `sqlalchemy.create_engine(db_url)` and `pd.read_sql_query(..., engine)` to avoid the warning.
  - For DDL (CREATE VIEW / CREATE TABLE), use `cursor.execute(sql)` then `conn.commit()`; use pandas only for SELECT results.
- `web_app.py` served pages successfully; observed `favicon.ico 404` (normal browser request; optional to add a favicon route/static file).
- Added `pd.set_option("display.max_columns", None)` and `pd.set_option("display.width", None)` to show full pandas DataFrame columns in console; `print(df.to_string())` is an alternative.

### SQL handling
- Created `sql_create_view` (a long CREATE VIEW statement) and executed it via:
  ```python
  cur = conn.cursor()
  cur.execute(sql_create_view)
  conn.commit()
  ```
- After creating the view, queried it with `pd.read_sql("SELECT * FROM silver.bao_cao_ket_qua_mbnt_2025_2026 LIMIT 10;", conn)`.
- Note: If the object becomes a physical table in the future, remove the CREATE VIEW step and query the table directly.

### Files added/edited
- Created `DEVLOG.md` (short start) and `DEVLOG_FULL.md` (this full log).
- Inspected and tested `DB_connect.py` and `web_app.py`.

### Next recommended steps
- If you will frequently run `pip` in this environment, consider adding the environment `Scripts` folder to PATH or always use the full interpreter path as done here.
- Install `SQLAlchemy` in the `dashboard` env and update `web_app.py` and `DB_connect.py` to use `create_engine()` for pandas queries.
  ```powershell
  & "C:/Users/hieupg/AppData/Local/miniconda3/envs/dashboard/python.exe" -m pip install SQLAlchemy
  ```
- If you need reliable CI-free installs behind the corporate proxy, ask IT to allow `files.pythonhosted.org` or provide proxy credentials.
- Keep this log updated: append a short bullet for each new action (date, command, result).

---

*End of log.*
