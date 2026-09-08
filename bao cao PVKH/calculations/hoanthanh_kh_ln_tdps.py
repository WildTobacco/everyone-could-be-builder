"""LN TDPS actual-vs-plan gap, same shape as hoanthanh_kh_ln_mbnt.py / _hdls.py.

No source DAX was supplied for TDPS, so there's no existing Power BI number to stay
bug-compatible with: this uses the dynamic WorkingDays_YTD like the MBNT measures, not the
HĐLS ones' hardcoded 79 (that literal only exists to reproduce the other dashboard exactly).

    Gap = LN_TDPS_ngay - (KH LN TDPS of the selected month / WorkingDays_YTD)
"""

from data_connect.db_connect import _df_cache

import pandas as pd

from data_connect.excel_connect import ke_hoach_theo_ptkd
from calculations.tdps_ngay_by_nhom import ln_tdps_ngay_by_nhom
from calculations.working_days_ytd import working_days_ytd
from calculations.hoanthanh_kh_ds_mbnt import _fmt_gap_value

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
SAN_PHAM = "LN TDPS"


@_df_cache()
def ke_hoach_ln_tdps_thang(month_value: str) -> pd.Series:
    """Cumulative/lũy kế LN TDPS plan through the given month, by nhóm + TOTAL. TOTAL comes
    from the sheet's own Tổng row rather than being recomputed, matching the HĐLS lookups."""
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == month_value)
    by_group = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = by_group.get("Tổng", 0.0)
    return result


@_df_cache()
def ke_hoach_ln_tdps_nam() -> pd.Series:
    """Annual (month='total') LN TDPS plan by nhóm + TOTAL. TOTAL comes from the sheet's own
    Tổng row, matching ke_hoach_ln_tdps_thang."""
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == "total")
    by_group = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = by_group.get("Tổng", 0.0)
    return result


@_df_cache()
def _ln_current_and_kh_per_day(date_str: str, group: str):
    """Shared by hoanthanh_kh_ln_tdps (absolute gap) and ht_thang_ln_tdps_pct (% completion) —
    same role as the private helpers of the same name in hoanthanh_kh_ds_mbnt.py etc."""
    ln_current = ln_tdps_ngay_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ln_tdps_thang(month_value).get(group)
    if pd.isna(ln_current) or pd.isna(kh_thang):
        return None, None
    return ln_current, kh_thang / working_days_ytd(date_str)


@_df_cache()
def hoanthanh_kh_ln_tdps(date_str: str, group: str) -> str | None:
    ln_current, kh_per_day = _ln_current_and_kh_per_day(date_str, group)
    if ln_current is None:
        return None
    gap = ln_current - kh_per_day
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def ht_thang_ln_tdps_pct(date_str: str, group: str) -> float | None:
    """LN_Current as a % of that day's pace target (this month's KH_Thang / WorkingDays_YTD)
    — same shape as ht_thang_ln_mbnt_pct/ht_thang_ln_hdls_pct, for TDPS's Trong ngày HT ring."""
    ln_current, kh_per_day = _ln_current_and_kh_per_day(date_str, group)
    if ln_current is None or not kh_per_day:
        return None
    return ln_current / kh_per_day * 100


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    for g in GROUPS + ["TOTAL"]:
        print(g, hoanthanh_kh_ln_tdps(d, g))
