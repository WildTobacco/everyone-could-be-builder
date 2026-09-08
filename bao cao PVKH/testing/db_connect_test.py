import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from data_connect.db_connect import (
    bao_cao_ket_qua_mbnt_2025_2026,
    bao_cao_ket_qua_hdls_2025_2026,
    pvkh_fx,
    pvkh_pstc,
    pvkh_pshh,
    pvkh_listcif,
)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

for name, func in [
    ("bao_cao_ket_qua_mbnt_2025_2026", bao_cao_ket_qua_mbnt_2025_2026),
    ("bao_cao_ket_qua_hdls_2025_2026", bao_cao_ket_qua_hdls_2025_2026),
    ("pvkh_fx", pvkh_fx),
    ("pvkh_pstc", pvkh_pstc),
    ("pvkh_pshh", pvkh_pshh),
    ("pvkh_listcif", pvkh_listcif),
]:
    df = func()
    print(f"\n=== {name} ({len(df)} rows) ===")
    print(df.head(10))