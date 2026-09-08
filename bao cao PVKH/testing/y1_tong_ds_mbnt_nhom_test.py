import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations.y1_tong_ds_mbnt_nhom import compute_y1_tong_ds_mbnt_nhom

result = compute_y1_tong_ds_mbnt_nhom("2025-07-30")
print(result.apply(lambda x: f"{x:,.2f}"))

# python y1_tong_ds_mbnt_nhom.py
