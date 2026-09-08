"""so với cùng kỳ for LN TDPS lũy kế. Same logic and source table as
y1_ln_hdls_nhom_diaban_pkkh.py's HĐLS version — Full + Partial × ProrationRatio approximation
against bronze_baocaotudong.pvkh_pstc — just filtered to sanpham = "TDPS" (a single value,
unlike HĐLS's {CCS, IRS, AIRS} set) instead of "TDPS" being one of the HĐLS members.
"""

from data_connect.db_connect import _df_cache
import calendar
import pandas as pd
from data_connect.db_connect import pvkh_pstc
from calculations.ln_tdps_luy_ke_by_nhom import ln_tdps_luy_ke_by_nhom
from calculations.date_table import same_day_last_year

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def _y1_ln_tdps(date_str: str) -> pd.Series:
    """Full + Partial x ProrationRatio approximation, pvkh_pstc[loinhuan], sanpham = "TDPS".
    date_str is already the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_pstc(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df = df[df["sanpham"] == "TDPS"]

    full = df.loc[df["monthyear"] < ref_month].groupby("nhomphutrach")["loinhuan"].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby("nhomphutrach")["loinhuan"].sum() * proration_ratio
    return full.add(partial, fill_value=0)


@_df_cache()
def y1_ln_tdps_by_nhom(date_str: str) -> pd.Series:
    by_group = _y1_ln_tdps(date_str)
    total = by_group.sum()  # includes every group present (e.g. TSC), not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def ln_tdps_pct_change_by_nhom(selected_date: str) -> pd.Series:
    """so với cùng kỳ: (LN_Y - LN_Y1) / ABS(LN_Y1) * 100. LN_Y's TOTAL = sum(PTKD1+PTKD2+VPV),
    not the table's native TOTAL row that ln_tdps_luy_ke_by_nhom's own TOTAL uses."""
    date_2025 = same_day_last_year(selected_date)
    current = ln_tdps_luy_ke_by_nhom(selected_date).copy()
    current["TOTAL"] = current.reindex(GROUPS).sum()
    baseline = y1_ln_tdps_by_nhom(date_2025)
    return (current - baseline) / baseline.abs().replace(0, pd.NA) * 100


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    d2025 = same_day_last_year(d)
    print(f"ref date (Y-1): {d2025}")
    print("Baseline by nhom:\n", y1_ln_tdps_by_nhom(d2025))
    print(f"\nso với cùng kỳ (selected_date={d}):\n", ln_tdps_pct_change_by_nhom(d))
