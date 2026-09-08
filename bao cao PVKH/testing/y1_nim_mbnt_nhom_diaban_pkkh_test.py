import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations.y1_nim_mbnt_nhom_diaban_pkkh import y1_nim_mbnt_nhom_diaban_pkkh

print(y1_nim_mbnt_nhom_diaban_pkkh("2025-07-30"))

# python y1_nim_mbnt_nhom_diaban_pkkh.py
