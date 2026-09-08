"""2025 PSHH (phái sinh hàng hóa) baseline by nhóm phụ trách + dia_ban + PKKH — Full + Partial ×
ProrationRatio over pvkh_pshh (monthly-only source), same approximation ds_ln_pshh.py's
TOTAL-only _y1_pshh() uses for the Tổng quan scorecard, just grouped by nhóm/dia_ban/pkkh here.

Doanh số stays split TLHH (lots, sanpham='TLHH') / OTC (USD, sanpham='OTC') — see
ds_ln_pshh.py's module docstring for why. Lợi nhuận sums both sanpham (sanpham=None)."""

import calendar

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_pshh

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _y1_pshh_by_group(date_str: str, value_col: str, group_cols: list,
                       sanpham: str | None = None) -> pd.Series:
    """Same Full + Partial × ProrationRatio as ds_ln_pshh.py's _y1_pshh, grouped by group_cols
    instead of collapsed to a single scalar. date_str is already the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_pshh(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    if sanpham is not None:
        df = df[df["sanpham"] == sanpham]

    full = df.loc[df["monthyear"] < ref_month].groupby(group_cols)[value_col].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby(group_cols)[value_col].sum() * proration_ratio
    return full.add(partial, fill_value=0.0)


def _y1_by_nhom(value_col: str, sanpham: str | None, date_str: str) -> pd.Series:
    by_group = _y1_pshh_by_group(date_str, value_col, ["nhomphutrach"], sanpham)
    total = by_group.sum()  # includes every group present, not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def y1_ds_pshh_tlhh_by_nhom(date_str: str) -> pd.Series:
    return _y1_by_nhom("doanhso", "TLHH", date_str)


@_df_cache()
def y1_ds_pshh_otc_by_nhom(date_str: str) -> pd.Series:
    return _y1_by_nhom("doanhso", "OTC", date_str)


@_df_cache()
def y1_ln_pshh_by_nhom(date_str: str) -> pd.Series:
    return _y1_by_nhom("loinhuan", None, date_str)


def _y1_by_nhom_dim(value_col: str, sanpham: str | None, dim_col: str, output_col: str,
                     output_value_col: str, date_str: str) -> pd.DataFrame:
    series = _y1_pshh_by_group(date_str, value_col, ["nhomphutrach", dim_col], sanpham)
    df = series.rename(output_value_col).reset_index()
    df.columns = ["nhom_phu_trach", output_col, output_value_col]
    return df


@_df_cache()
def y1_ds_pshh_tlhh_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _y1_by_nhom_dim("doanhso", "TLHH", "diaban", "dia_ban", "doanh_so", date_str)


@_df_cache()
def y1_ds_pshh_tlhh_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _y1_by_nhom_dim("doanhso", "TLHH", "pkkh", "pkkh", "doanh_so", date_str)


@_df_cache()
def y1_ds_pshh_otc_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _y1_by_nhom_dim("doanhso", "OTC", "diaban", "dia_ban", "doanh_so", date_str)


@_df_cache()
def y1_ds_pshh_otc_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _y1_by_nhom_dim("doanhso", "OTC", "pkkh", "pkkh", "doanh_so", date_str)


@_df_cache()
def y1_ln_pshh_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _y1_by_nhom_dim("loinhuan", None, "diaban", "dia_ban", "loi_nhuan", date_str)


@_df_cache()
def y1_ln_pshh_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _y1_by_nhom_dim("loinhuan", None, "pkkh", "pkkh", "loi_nhuan", date_str)


if __name__ == "__main__":
    from calculations.date_table import latest_date, same_day_last_year

    d25 = same_day_last_year(latest_date())
    print(f"Y-1 date: {d25}")
    print("Y1 DS TLHH by nhom:\n", y1_ds_pshh_tlhh_by_nhom(d25))
    print("Y1 DS OTC by nhom:\n", y1_ds_pshh_otc_by_nhom(d25))
    print("Y1 LN by nhom:\n", y1_ln_pshh_by_nhom(d25))
    print("Y1 DS TLHH by pkkh:\n", y1_ds_pshh_tlhh_by_nhom_pkkh(d25).to_string())
