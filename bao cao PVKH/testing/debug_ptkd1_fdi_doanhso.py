import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.y1_ds_mbnt_nhom_diaban_pkkh import y1_ds_mbnt_by_nhom_pkkh
from calculations.date_table import same_day_last_year

selected_date = "2026-07-15"
date_2025 = same_day_last_year(selected_date)

df = y1_ds_mbnt_by_nhom_pkkh(date_2025)
row = df[(df["nhom_phu_trach"] == "PTKD 1") & (df["pkkh"] == "FDI")]

print(f"selected_date: {selected_date} -> date_2025: {date_2025}")
print(row.to_string())
print(f"doanh_so: {row['doanh_so'].sum():,.2f}")

# python testing/debug_ptkd1_fdi_doanhso.py
