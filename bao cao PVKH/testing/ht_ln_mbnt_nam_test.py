import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations.ht_ln_mbnt_nam import ke_hoach_ln_mbnt_nam

print(ke_hoach_ln_mbnt_nam())

# python ht_ln_mbnt_nam.py
