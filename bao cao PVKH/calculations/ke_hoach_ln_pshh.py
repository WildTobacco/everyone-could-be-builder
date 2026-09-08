"""LN PSHH plan (kế hoạch) lookups — same shape and source (KHKD PTKD sheet, via
ke_hoach_theo_ptkd()) as ke_hoach_ln_tdps_nam/ke_hoach_ln_tdps_thang in hoanthanh_kh_ln_tdps.py.
No Doanh số plan wired here even though "KH DS PSHH" exists in the sheet too — the Tổng quan
scorecard only tracks HT tháng/HT năm against Lợi nhuận for PSHH, matching the user's explicit
scope."""

import pandas as pd

from data_connect.db_connect import _df_cache
from data_connect.excel_connect import ke_hoach_theo_ptkd

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
SAN_PHAM = "LN PSHH"


@_df_cache()
def ke_hoach_ln_pshh_nam() -> pd.Series:
    """Annual (month='total') LN PSHH plan by nhóm + TOTAL. TOTAL comes from the sheet's own
    Tổng row, matching ke_hoach_ln_tdps_nam."""
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == "total")
    by_group = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = by_group.get("Tổng", 0.0)
    return result


@_df_cache()
def ke_hoach_ln_pshh_thang(month_value: str) -> pd.Series:
    """Cumulative/lũy kế LN PSHH plan through the given month, by nhóm + TOTAL."""
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == month_value)
    by_group = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = by_group.get("Tổng", 0.0)
    return result


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    month_value = str(pd.to_datetime(d).month)
    print(f"date: {d}")
    print("KH LN PSHH năm:\n", ke_hoach_ln_pshh_nam())
    print(f"\nKH LN PSHH tháng {month_value} (lũy kế):\n", ke_hoach_ln_pshh_thang(month_value))
