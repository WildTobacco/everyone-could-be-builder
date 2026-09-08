import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations.tong_ln_nhom import tong_ln_nhom

result = tong_ln_nhom("2025-07-15")
print(f"Tong LN Nhom (2025-07-15): {result:,.2f}")

# python tong_ln_nhom.py