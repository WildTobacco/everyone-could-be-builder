from data_connect.db_connect import _df_cache
import calendar
import pandas as pd
from data_connect.db_connect import pvkh_fx, pvkh_chiase


def _full_partial_sum(df: pd.DataFrame, col: str, ref_month: pd.Timestamp, proration_ratio: float,
                       group_cols) -> pd.Series:
    full = df.loc[df["monthyear"] < ref_month].groupby(group_cols)[col].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby(group_cols)[col].sum() * proration_ratio
    return full.add(partial, fill_value=0)


def _y1_ln_sau_chiase(date_str: str, group_cols) -> pd.Series:
    """(Y-1)LN_MBNT_Nhom_DiaBan_PKKH's TotalLN:
    LN_Full + LN_Partial (pvkh_fx[loinhuan], full+partial approx)
    - ChiaSe_Full (pvkh_chiase[loinhuanchiase], YTD sum through the effective month boundary).
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
    ln_full_partial = _full_partial_sum(fx_df, "loinhuan", ref_month, proration_ratio, group_cols)

    chiase_df = pvkh_chiase(date_str)
    chiase_df["monthyear"] = pd.to_datetime(chiase_df["monthyear"])
    chiase_window = chiase_df[
        (chiase_df["monthyear"] >= first_day) & (chiase_df["monthyear"] < effective_month_boundary)
    ]
    chiase_full = chiase_window.groupby(group_cols)["loinhuanchiase"].sum()

    return ln_full_partial.subtract(chiase_full, fill_value=0.0)


@_df_cache()
def y1_ln_mbnt_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """TotalLN, grouped by (nhom_phu_trach, dia_ban)."""
    return (
        _y1_ln_sau_chiase(date_str, ["nhomphutrach", "diaban"])
        .rename("loi_nhuan")
        .reset_index()
        .rename(columns={"nhomphutrach": "nhom_phu_trach", "diaban": "dia_ban"})
    )


@_df_cache()
def y1_ln_mbnt_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """TotalLN, grouped by (nhom_phu_trach, pkkh)."""
    return (
        _y1_ln_sau_chiase(date_str, ["nhomphutrach", "pkkh"])
        .rename("loi_nhuan")
        .reset_index()
        .rename(columns={"nhomphutrach": "nhom_phu_trach"})
    )


if __name__ == "__main__":
    from date_table import latest_date, same_day_last_year

    ref_2025 = same_day_last_year(latest_date())
    print(f"ref date (Y-1): {ref_2025}")
    print("LN sau chiase by dia_ban:\n", y1_ln_mbnt_by_nhom_diaban(ref_2025).to_string())
    print("LN sau chiase by pkkh:\n", y1_ln_mbnt_by_nhom_pkkh(ref_2025).to_string())
