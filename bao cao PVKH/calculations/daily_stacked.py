"""Daily (non-accumulative) series by nhóm phụ trách for the stacked trend charts.

Replaces the earlier ds_mbnt_ngay_bc_stacked.py / ds_hdls_ngay_bc_stacked.py, which held
one metric each — every product now needs both a DS and an LN series, so the shared shaping
lives here once instead of being copied per metric.

Each function returns one row per (ngay, nhom_phu_trach). The source's junk "0" row and its
own pre-aggregated "TOTAL"/"Sum" row are dropped (a stacked chart of the 3 real groups
already sums to the total visually), as are zero days — matching the source DAX's
IF(ISBLANK(vDS) || vDS = 0, BLANK(), vDS).
"""

import pandas as pd

from data_connect.db_connect import (
    pvkh_mbnt_nhom_phu_trach_range,
    pvkh_pstc_nhom_phu_trach_range,
    pvkh_dsdaily_temp,
)

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _stacked(fetch, value_col: str, end_date: str, days: int) -> pd.DataFrame:
    start_date = (pd.to_datetime(end_date) - pd.Timedelta(days=days - 1)).strftime("%Y-%m-%d")
    df = fetch(start_date, end_date)
    df = df[df["nhom_phu_trach"].isin(GROUPS)]
    result = df.groupby(["ngay", "nhom_phu_trach"])[value_col].max().reset_index()
    return result[result[value_col] != 0]


def ds_mbnt_stacked(end_date: str, days: int = 30) -> pd.DataFrame:
    return _stacked(pvkh_mbnt_nhom_phu_trach_range, "sum_ds_mbnt_ngay_bc", end_date, days)


def ln_mbnt_stacked(end_date: str, days: int = 30) -> pd.DataFrame:
    return _stacked(pvkh_mbnt_nhom_phu_trach_range, "sum_ln_mbnt_ngay_bao_cao", end_date, days)


def ds_hdls_stacked(end_date: str, days: int = 30) -> pd.DataFrame:
    return _stacked(pvkh_pstc_nhom_phu_trach_range, "sum_ds_hdls_ngay_bc", end_date, days)


def ln_hdls_stacked(end_date: str, days: int = 30) -> pd.DataFrame:
    return _stacked(pvkh_pstc_nhom_phu_trach_range, "sum_ln_hdls_ngay_bc", end_date, days)


def ln_tdps_stacked(end_date: str, days: int = 30) -> pd.DataFrame:
    return _stacked(pvkh_pstc_nhom_phu_trach_range, "sum_ln_tdps_ngay_bc", end_date, days)


def ds_tdps_stacked(end_date: str, days: int = 30) -> pd.DataFrame:
    """DS TDPS can't use _stacked: pvkh_pstc_nhom_phu_trach[sum_ds_tdps_ngay_bc] is empty, so
    this comes from pvkh_dsdaily_temp instead — customer-level rather than pre-aggregated by
    nhóm, and keyed on `monthyear` (which despite the name holds a real date). Rows are already
    one per day, so they are summed per (day, nhóm) rather than MAX'd like the snapshot tables."""
    start_date = (pd.to_datetime(end_date) - pd.Timedelta(days=days - 1)).strftime("%Y-%m-%d")
    df = pvkh_dsdaily_temp(start_date, end_date)
    df = df[df["nhomphutrach"].isin(GROUPS)]
    result = (
        df.groupby([df["monthyear"].dt.normalize(), "nhomphutrach"])["doanhsotdps"]
        .sum().reset_index()
    )
    result.columns = ["ngay", "nhom_phu_trach", "sum_ds_tdps_ngay_bc"]
    return result[result["sum_ds_tdps_ngay_bc"] != 0]


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    for name, fn in [
        ("DS MBNT", ds_mbnt_stacked), ("LN MBNT", ln_mbnt_stacked),
        ("DS HDLS", ds_hdls_stacked), ("LN HDLS", ln_hdls_stacked),
        ("LN TDPS", ln_tdps_stacked),
    ]:
        print(f"{name}: {len(fn(d))} rows")
