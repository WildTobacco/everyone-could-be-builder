import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations.y_nim_mbnt_nhom_diaban_pkkh import y_nim_mbnt_nhom_diaban_pkkh

print(y_nim_mbnt_nhom_diaban_pkkh("2026-07-31"))

# python y_nim_mbnt_nhom_diaban_pkkh.py
