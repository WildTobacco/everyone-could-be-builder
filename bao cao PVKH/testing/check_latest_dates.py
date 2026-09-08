"""Prints the latest available date (and row count) for every Postgres table this
project reads from, so you can quickly see how fresh the underlying data is."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from data_connect.db_connect import get_connection

# (schema, table, date_column) — matches every table referenced in data_connect/db_connect.py
# and pvkh_kq_canbo.py
TABLES = [
    ("silver", "bao_cao_ket_qua_mbnt_2025_2026", '"Ngày"'),
    ("silver", "bao_cao_ket_qua_hdls_2025_2026", '"Ngày"'),
    ("silver", '"silver_pvkh_DL_KH_luy_ke"', "ngay"),
    ("bronze_baocaotudong", "pvkh_fx", "monthyear"),
    ("bronze_baocaotudong", "pvkh_pstc", "monthyear"),
    ("bronze_baocaotudong", "pvkh_pshh", "monthyear"),
    ("bronze_baocaotudong", "pvkh_chiase", "monthyear"),
    ("bronze_baocaotudong", "pvkh_listcif", "monthyear"),
    ("bronze_baocaotudong", "pvkh_kdntps_nhom_phu_trach", "ngay"),
    ("bronze_baocaotudong", "pvkh_pstc_nhom_phu_trach", "ngay"),
    ("bronze_baocaotudong", "pvkh_mbnt_nhom_phu_trach", "ngay"),
    ("bronze_baocaotudong", "pvkh_kq_chinhanh", "ngay"),
    ("bronze_baocaotudong", "pvkh_kq_canbo", "ngay"),
]


def main():
    results = []
    for schema, table, date_col in TABLES:
        display_name = f"{schema}.{table}".replace('"', "")
        conn = get_connection()
        try:
            row = pd.read_sql(
                f"SELECT MAX({date_col}) AS latest_date, COUNT(*) AS row_count FROM {schema}.{table};",
                conn,
            ).iloc[0]
            results.append({
                "table": display_name,
                "date_column": date_col.replace('"', ""),
                "latest_date": row["latest_date"],
                "row_count": int(row["row_count"]),
            })
        except Exception as e:
            results.append({
                "table": display_name,
                "date_column": date_col.replace('"', ""),
                "latest_date": f"ERROR: {e}",
                "row_count": None,
            })
        finally:
            conn.close()

    df = pd.DataFrame(results).sort_values("latest_date", ascending=False, na_position="last")

    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.width", None)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
