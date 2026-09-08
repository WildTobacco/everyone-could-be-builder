from data_connect.db_connect import _df_cache
import calendar
import pandas as pd
from data_connect.db_connect import pvkh_fx

EXCLUDED_BDSCIF = "1609448630"
DS_PRODUCTS = {"FW", "SP", "SW"}


@_df_cache()
def _y1_ds_mbnt_by_nhom(date_str: str, source_col: str, output_col: str) -> pd.DataFrame:
    """Full + Partial x ProrationRatio approximation, pvkh_fx[doanhsoswap2chan],
    sanpham in {FW, SP, SW}, excluding bdscif 1609448630, grouped by (nhom_phu_trach, source_col).
    source_col: 'diaban' or 'pkkh' (already present on pvkh_fx()). date_str is already the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_fx(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df["bdscif"] = df["bds"].astype(str) + df["cif"].astype(str)
    df = df[(df["bdscif"] != EXCLUDED_BDSCIF) & (df["sanpham"].isin(DS_PRODUCTS))]

    full = df.loc[df["monthyear"] < ref_month].groupby(["nhomphutrach", source_col])["doanhsoswap2chan"].sum()
    partial = (
        df.loc[df["monthyear"] == ref_month].groupby(["nhomphutrach", source_col])["doanhsoswap2chan"].sum()
        * proration_ratio
    )
    result = full.add(partial, fill_value=0.0).reset_index()
    result.columns = ["nhom_phu_trach", output_col, "doanh_so"]
    return result


@_df_cache()
def y1_ds_mbnt_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _y1_ds_mbnt_by_nhom(date_str, "diaban", "dia_ban")


@_df_cache()
def y1_ds_mbnt_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _y1_ds_mbnt_by_nhom(date_str, "pkkh", "pkkh")


if __name__ == "__main__":
    from date_table import latest_date, same_day_last_year

    ref_2025 = same_day_last_year(latest_date())
    print(f"ref date (Y-1): {ref_2025}")
    print("By dia_ban:")
    print(y1_ds_mbnt_by_nhom_diaban(ref_2025).to_string())
    print("By pkkh:")
    print(y1_ds_mbnt_by_nhom_pkkh(ref_2025).to_string())
