import calendar
import pandas as pd
from data_connect.db_connect import _df_cache, get_connection
from data_connect.excel_connect import listbds
from calculations.date_table import latest_date, same_day_last_year

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def _fetch_ytd(table: str, ref_date: pd.Timestamp) -> pd.DataFrame:
    """Fetch rows from Jan 1 of ref_date's year through the reference month (inclusive)."""
    start_date = ref_date.replace(month=1, day=1).strftime("%Y-%m-%d")
    ref_month_str = ref_date.replace(day=1).strftime("%Y-%m-%d")
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT * FROM bronze_baocaotudong.{table}
        WHERE monthyear >= DATE '{start_date}'
          AND monthyear <= DATE '{ref_month_str}';
        """,
        conn
    )
    conn.close()
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df["bdscif"] = df["bds"].astype(str) + df["cif"].astype(str)
    return df.merge(listbds()[["bds", "nhomphutrach"]], on="bds", how="left")


def _sum_full_and_partial_by_group(df: pd.DataFrame, ref_month: pd.Timestamp, proration_ratio: float,
                                    extra_filter=None) -> pd.Series:
    if extra_filter is not None:
        df = df[extra_filter]
    full = df.loc[df["monthyear"] < ref_month].groupby("nhomphutrach")["loinhuan"].sum()
    partial = df.loc[df["monthyear"] == ref_month].groupby("nhomphutrach")["loinhuan"].sum() * proration_ratio
    return full.add(partial, fill_value=0)


@_df_cache()
def fetch_tong_ln_nhom_data(date_str: str) -> dict:
    """Fetch pvkh_fx/pvkh_pstc/pvkh_pshh once, scoped to Jan-1-through-reference-month,
    each enriched with nhomphutrach via listbds().

    date_str is a 2025 date (this calc is always for 2025 numbers — see date_table.same_day_last_year
    to derive it from a current-year selected date)."""
    ref_date = pd.to_datetime(date_str)
    return {
        "ref_date": ref_date,
        "fx": _fetch_ytd("pvkh_fx", ref_date),
        "pstc": _fetch_ytd("pvkh_pstc", ref_date),
        "pshh": _fetch_ytd("pvkh_pshh", ref_date),
    }


def compute_tong_ln_nhom(data: dict) -> pd.Series:
    """tong_ln_nhom per Nhóm phụ trách (PTKD 1, PTKD 2, VPV) + TOTAL row,
    same Full+Partial*ProrationRatio approximation as the DAX measure."""
    ref_date = data["ref_date"]
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    fx_by_group = _sum_full_and_partial_by_group(data["fx"], ref_month, proration_ratio)

    pstc_df = data["pstc"]
    pstc_products = {"IRS", "CCS", "AIRS", "TDPS"}
    pstc_by_group = _sum_full_and_partial_by_group(
        pstc_df, ref_month, proration_ratio,
        extra_filter=pstc_df["sanpham"].isin(pstc_products)
    )

    pshh_by_group = _sum_full_and_partial_by_group(data["pshh"], ref_month, proration_ratio)

    result = pd.Series(0.0, index=GROUPS)
    for series in (fx_by_group, pstc_by_group, pshh_by_group):
        result = result.add(series.reindex(GROUPS, fill_value=0.0), fill_value=0.0)

    result["TOTAL"] = result.sum()
    return result


@_df_cache()
def tong_ln_nhom(date_str: str) -> pd.Series:
    """One-shot: PTKD 1 / PTKD 2 / VPV / TOTAL for the given (2025) date."""
    data = fetch_tong_ln_nhom_data(date_str)
    return compute_tong_ln_nhom(data)


if __name__ == "__main__":
    ref_2025 = same_day_last_year(latest_date())
    result = tong_ln_nhom(ref_2025)
    print(f"ref date (2025): {ref_2025}")
    print(result.apply(lambda x: f"{x:,.2f}"))