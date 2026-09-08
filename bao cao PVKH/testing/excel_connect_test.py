import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from data_connect.excel_connect import ke_hoach_theo_ptkd, listbds

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

ptkd = ke_hoach_theo_ptkd()
print(ptkd)
print(f"ke_hoach_theo_ptkd rows: {len(ptkd)}\n")

cn = listbds()
print(cn)
print(f"listbds rows: {len(cn)}")
# python excel_connect.py