from data_connect.db_connect import _df_cache
import calendar
import pandas as pd
from data_connect.db_connect import pvkh_fx

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
COL = "doanhsoswap2chan"


@_df_cache()
def compute_y1_tong_ds_mbnt_nhom(date_str: str) -> pd.Series:
    """date_str is already the Y-1 (same-day-last-year) target date — caller shifts, this func does not.
    Full + Partial x ProrationRatio approximation, same pattern as tong_ln_nhom."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_fx(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])

    full = df.loc[df["monthyear"] < ref_month].groupby("nhomphutrach")[COL].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby("nhomphutrach")[COL].sum() * proration_ratio

    by_group = full.add(partial, fill_value=0)
    total = by_group.sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


if __name__ == "__main__":
    from date_table import latest_date, same_day_last_year

    ref_2025 = same_day_last_year(latest_date())
    print(f"ref date (Y-1): {ref_2025}")
    print(compute_y1_tong_ds_mbnt_nhom(ref_2025).apply(lambda x: f"{x:,.2f}"))
