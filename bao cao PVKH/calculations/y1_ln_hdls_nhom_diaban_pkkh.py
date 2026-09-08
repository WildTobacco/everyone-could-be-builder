import calendar
import pandas as pd

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_pstc
from calculations.tong_ln_hdls_ytd_nhom import tong_ln_hdls_ytd_by_nhom
from calculations.date_table import same_day_last_year

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
HDLS_PRODUCTS = {"CCS", "IRS", "AIRS"}


def _full_partial_sum(df: pd.DataFrame, col: str, ref_month: pd.Timestamp, proration_ratio: float,
                       group_cols) -> pd.Series:
    full = df.loc[df["monthyear"] < ref_month].groupby(group_cols)[col].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby(group_cols)[col].sum() * proration_ratio
    return full.add(partial, fill_value=0)


def _y1_ln_hdls(date_str: str, group_cols) -> pd.Series:
    """y1_LN_HDLS_Nhom_DiaBan_PKKH: Full + Partial x ProrationRatio approximation,
    pvkh_pstc[loinhuan], sanpham in {CCS, IRS, AIRS}. No bdscif exclusion (the DAX doesn't
    apply SelectedBDSCIF_Exclude here, only the DS measure does). date_str is already the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_pstc(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df = df[df["sanpham"].isin(HDLS_PRODUCTS)]

    return _full_partial_sum(df, "loinhuan", ref_month, proration_ratio, group_cols)


@_df_cache()
def y1_ln_hdls_by_nhom(date_str: str) -> pd.Series:
    by_group = _y1_ln_hdls(date_str, ["nhomphutrach"])
    total = by_group.sum()  # includes every group present (e.g. TSC), not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def y1_ln_hdls_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """y1_LN_HDLS, grouped by (nhom_phu_trach, dia_ban)."""
    result = _y1_ln_hdls(date_str, ["nhomphutrach", "diaban"]).reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "loi_nhuan"]
    return result


@_df_cache()
def y1_ln_hdls_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """y1_LN_HDLS, grouped by (nhom_phu_trach, pkkh)."""
    result = _y1_ln_hdls(date_str, ["nhomphutrach", "pkkh"]).reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "loi_nhuan"]
    return result


@_df_cache()
def ln_hdls_pct_change_by_nhom(selected_date: str) -> pd.Series:
    """so với cùng kỳ: (LN_Y - LN_Y1) / ABS(LN_Y1) * 100.
    LN_Y's TOTAL = sum(PTKD1+PTKD2+VPV) (per %_Change_..._THT's DAX), NOT the table's
    native 'TOTAL' row that tong_ln_hdls_ytd_by_nhom's own TOTAL uses."""
    date_2025 = same_day_last_year(selected_date)
    current = tong_ln_hdls_ytd_by_nhom(selected_date).copy()
    current["TOTAL"] = current.reindex(GROUPS).sum()
    baseline = y1_ln_hdls_by_nhom(date_2025)
    return (current - baseline) / baseline.abs().replace(0, pd.NA) * 100


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    d2025 = same_day_last_year(d)
    print(f"ref date (Y-1): {d2025}")
    print("By nhom:\n", y1_ln_hdls_by_nhom(d2025))
    print("By dia_ban:\n", y1_ln_hdls_by_nhom_diaban(d2025).to_string())
    print("By pkkh:\n", y1_ln_hdls_by_nhom_pkkh(d2025).to_string())
    print(f"\nso voi cung ky (selected_date={d}):\n", ln_hdls_pct_change_by_nhom(d))
