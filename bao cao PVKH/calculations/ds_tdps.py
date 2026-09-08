"""Doanh số TDPS. The two years come from two different tables, by design:

  - **2026 (current)** — pvkh_dsdaily_temp[doanhsotdps]. Non-accumulative by nature: one row is
    one day's business for a (bds, cif), so lũy kế is a plain SUM accumulated from the start of
    2026 through the selected date, and a single day's figure needs no differencing.
  - **2025 (Y-1 baseline)** — pvkh_pstc[doanhso] where sanpham = 'TDPS', via the usual
    Full + Partial × ProrationRatio approximation. pvkh_pstc is monthly, so a part-month figure
    has to be approximated; pvkh_dsdaily_temp is not used here because it only covers 2026.

Replaces pvkh_pstc_nhom_phu_trach[sum_ds_tdps_ngay_bc] / [sum_ds_tdps_luy_ke] for the 2026
side — both of those columns are empty in the source (every row 0), which is why the Doanh số
lũy kế card read 0.00M and the daily TDPS row had no DS counterpart at all.

TOTAL on the 2026 side is the sum of every nhóm present (TSC included, though it is 0 here) —
unlike ln_tdps_luy_ke_by_nhom, whose source carries its own pre-aggregated TOTAL row to read.
"""

from data_connect.db_connect import _df_cache
import calendar

import pandas as pd

from data_connect.db_connect import pvkh_dsdaily_temp, pvkh_pstc
from calculations.date_table import same_day_last_year, latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def _by_nhom(start_date: str, end_date: str) -> pd.Series:
    df = pvkh_dsdaily_temp(start_date, end_date)
    by_group = df.groupby("nhomphutrach")["doanhsotdps"].sum()
    total = by_group.sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def _year_start(date_str: str) -> str:
    return pd.to_datetime(date_str).replace(month=1, day=1).strftime("%Y-%m-%d")


@_df_cache()
def ds_tdps_ngay_by_nhom(date_str: str) -> pd.Series:
    """That day's own doanh số — the rows are already non-accumulative, so no differencing."""
    return _by_nhom(date_str, date_str)


@_df_cache()
def ds_tdps_luy_ke_by_nhom(date_str: str) -> pd.Series:
    """Accumulated from the start of date_str's year through date_str inclusive. Intended for
    2026 dates only — see the module docstring for why 2025 takes a different route."""
    return _by_nhom(_year_start(date_str), date_str)


@_df_cache()
def y1_ds_tdps_by_nhom(date_str: str) -> pd.Series:
    """Y-1 baseline: Full + Partial × ProrationRatio over pvkh_pstc[doanhso], sanpham = 'TDPS'.
    Same shape as y1_ln_tdps_by_nhom. date_str is already the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_pstc(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df = df[df["sanpham"] == "TDPS"]

    full = df.loc[df["monthyear"] < ref_month].groupby("nhomphutrach")["doanhso"].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby("nhomphutrach")["doanhso"].sum() * proration_ratio
    by_group = full.add(partial, fill_value=0)

    total = by_group.sum()  # includes every group present (e.g. TSC), not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def ds_tdps_pct_change_by_nhom(selected_date: str) -> pd.Series:
    """so với cùng kỳ: (DS_Y - DS_Y1) / ABS(DS_Y1) * 100. DS_Y's TOTAL is forced to
    sum(PTKD1+PTKD2+VPV), matching the %_Change_..._THT convention used by the HĐLS/MBNT
    versions rather than _by_nhom's own all-groups total."""
    current = ds_tdps_luy_ke_by_nhom(selected_date).copy()
    current["TOTAL"] = current.reindex(GROUPS).sum()
    baseline = y1_ds_tdps_by_nhom(same_day_last_year(selected_date))
    return (current - baseline) / baseline.abs().replace(0, pd.NA) * 100


if __name__ == "__main__":
    d = latest_date()
    d2025 = same_day_last_year(d)
    print(f"date: {d}   (Y-1: {d2025})")
    print("\nDS TDPS trong ngày:\n", ds_tdps_ngay_by_nhom(d).map(lambda x: f"{x:,.2f}"))
    print("\nDS TDPS lũy kế 2026:\n", ds_tdps_luy_ke_by_nhom(d).map(lambda x: f"{x:,.2f}"))
    print("\nDS TDPS Y-1 (pvkh_pstc, prorated):\n", y1_ds_tdps_by_nhom(d2025).map(lambda x: f"{x:,.2f}"))
    print("\nso với cùng kỳ:\n", ds_tdps_pct_change_by_nhom(d).round(1))
