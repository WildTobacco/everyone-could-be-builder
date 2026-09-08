import calendar
import pandas as pd

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_fx, pvkh_chiase

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
EXCLUDED_BDSCIF = "1609448630"
DS_PRODUCTS = {"FW", "SP", "SW"}


def _full_partial_sum(df: pd.DataFrame, col: str, ref_month: pd.Timestamp, proration_ratio: float,
                       group_cols, extra_filter=None) -> pd.Series:
    if extra_filter is not None:
        df = df[extra_filter]
    full = df.loc[df["monthyear"] < ref_month].groupby(group_cols)[col].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby(group_cols)[col].sum() * proration_ratio
    return full.add(partial, fill_value=0)


def _y1_doanhso(date_str: str, group_cols) -> pd.Series:
    """Full + Partial x ProrationRatio approximation, pvkh_fx[doanhsoswap2chan],
    sanpham in {FW, SP, SW}, excluding bdscif 1609448630. date_str is already the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_fx(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df["bdscif"] = df["bds"].astype(str) + df["cif"].astype(str)
    df = df[df["bdscif"] != EXCLUDED_BDSCIF]

    return _full_partial_sum(df, "doanhsoswap2chan", ref_month, proration_ratio, group_cols,
                              extra_filter=df["sanpham"].isin(DS_PRODUCTS))


def _y1_loinhuan(date_str: str, group_cols) -> pd.Series:
    """loi_nhuan_sau_chiase = loi_nhuan_truoc_chiase (pvkh_fx, full+partial approx)
    - loi_nhuan_chiase (pvkh_chiase, YTD sum through the effective month boundary).
    date_str is already the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    first_day = ref_date.replace(month=1, day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month
    # last day of the month => that month counts as fully complete, so include it
    effective_month_boundary = (
        ref_month + pd.DateOffset(months=1) if ref_date.day == days_in_month else ref_month
    )

    fx_df = pvkh_fx(date_str)
    fx_df["monthyear"] = pd.to_datetime(fx_df["monthyear"])
    truoc_chiase = _full_partial_sum(fx_df, "loinhuan", ref_month, proration_ratio, group_cols)

    chiase_df = pvkh_chiase(date_str)
    chiase_df["monthyear"] = pd.to_datetime(chiase_df["monthyear"])
    chiase_window = chiase_df[
        (chiase_df["monthyear"] >= first_day) & (chiase_df["monthyear"] < effective_month_boundary)
    ]
    chiase_by_group = chiase_window.groupby(group_cols)["loinhuanchiase"].sum()

    return truoc_chiase.subtract(chiase_by_group, fill_value=0.0)


@_df_cache()
def y1_doanhso_by_nhom(date_str: str) -> pd.Series:
    by_group = _y1_doanhso(date_str, ["nhomphutrach"])
    total = by_group.sum()  # includes every group present (e.g. TSC), not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def y1_loinhuan_by_nhom(date_str: str) -> pd.Series:
    by_group = _y1_loinhuan(date_str, ["nhomphutrach"])
    total = by_group.sum()  # includes every group present (e.g. TSC), not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def y1_nim_mbnt_nhom_diaban_pkkh(date_str: str) -> pd.Series:
    """NIM 2025 = loi_nhuan_sau_chiase / doanhso, by nhom_phu_trach + TOTAL.

    TOTAL = PTKD1+PTKD2+VPV+"TSC" (every group y1_doanhso_by_nhom/y1_loinhuan_by_nhom's own
    TOTAL already includes) — reverted from excluding "TSC" specifically for this ratio, same
    decision as y_nim_mbnt_nhom_diaban_pkkh.py's 2026 counterpart: no source table carries an
    actual nhom_phu_trach='TOTAL' row to select instead, so TOTAL here means "sum of every group
    actually present," matching the DS/LN totals' own definition."""
    doanhso = y1_doanhso_by_nhom(date_str)
    loinhuan = y1_loinhuan_by_nhom(date_str)
    return loinhuan / doanhso.replace(0, pd.NA)


@_df_cache()
def _y1_nim_by_nhom_dim(date_str: str, source_col: str, output_col: str) -> pd.DataFrame:
    group_cols = ["nhomphutrach", source_col]
    doanhso = _y1_doanhso(date_str, group_cols).rename("doanh_so")
    loinhuan = _y1_loinhuan(date_str, group_cols).rename("loi_nhuan")
    merged = pd.concat([doanhso, loinhuan], axis=1).fillna(0.0).reset_index()
    merged["nim"] = merged["loi_nhuan"] / merged["doanh_so"].replace(0, pd.NA)
    merged = merged.rename(columns={"nhomphutrach": "nhom_phu_trach", source_col: output_col})
    return merged[["nhom_phu_trach", output_col, "nim"]]


@_df_cache()
def y1_nim_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """NIM 2025, grouped by (nhom_phu_trach, dia_ban)."""
    return _y1_nim_by_nhom_dim(date_str, "diaban", "dia_ban")


@_df_cache()
def y1_nim_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """NIM 2025, grouped by (nhom_phu_trach, pkkh)."""
    return _y1_nim_by_nhom_dim(date_str, "pkkh", "pkkh")


@_df_cache()
def _y1_nim_by_dim_pooled(date_str: str, source_col: str, output_col: str) -> pd.DataFrame:
    """NIM 2025 pooled across every nhóm — see y_nim_mbnt_nhom_diaban_pkkh.py's
    _y_nim_by_dim_pooled for why this is a genuine combined ratio, not an averaged one."""
    doanhso = _y1_doanhso(date_str, [source_col]).rename("doanh_so")
    loinhuan = _y1_loinhuan(date_str, [source_col]).rename("loi_nhuan")
    merged = pd.concat([doanhso, loinhuan], axis=1).fillna(0.0).reset_index()
    merged["nim"] = merged["loi_nhuan"] / merged["doanh_so"].replace(0, pd.NA)
    merged["nhom_phu_trach"] = ""
    merged = merged.rename(columns={source_col: output_col})
    return merged[["nhom_phu_trach", output_col, "nim"]]


def y1_nim_diaban_pooled(date_str: str) -> pd.DataFrame:
    return _y1_nim_by_dim_pooled(date_str, "diaban", "dia_ban")


def y1_nim_pkkh_pooled(date_str: str) -> pd.DataFrame:
    return _y1_nim_by_dim_pooled(date_str, "pkkh", "pkkh")


if __name__ == "__main__":
    from date_table import latest_date, same_day_last_year

    ref_2025 = same_day_last_year(latest_date())
    print(f"ref date (Y-1): {ref_2025}")
    print("Doanh so:\n", y1_doanhso_by_nhom(ref_2025))
    print("Loi nhuan (sau chiase):\n", y1_loinhuan_by_nhom(ref_2025))
    print("NIM 2025:\n", y1_nim_mbnt_nhom_diaban_pkkh(ref_2025))
    print("NIM 2025 by dia_ban:\n", y1_nim_by_nhom_diaban(ref_2025).to_string())
    print("NIM 2025 by pkkh:\n", y1_nim_by_nhom_pkkh(ref_2025).to_string())
