import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations.y1_ds_mbnt_nhom_diaban_pkkh import y1_ds_mbnt_by_nhom_diaban, y1_ds_mbnt_by_nhom_pkkh

print("By dia_ban:")
print(y1_ds_mbnt_by_nhom_diaban("2025-07-31").to_string())
print("By pkkh:")
print(y1_ds_mbnt_by_nhom_pkkh("2025-07-31").to_string())

# python y1_ds_mbnt_nhom_diaban_pkkh.py
