from data_connect.db_connect import _df_cache
import pandas as pd
from data_connect.excel_connect import ke_hoach_ds_mbnt_pkkh_2026, ke_hoach_ln_mbnt_pkkh_2026


def _kh_by_nhom_pkkh(df: pd.DataFrame, value_col: str, date_str: str) -> pd.Series:
    """Shared step for kh_ds_mbnt_by_nhom_pkkh/kh_mbnt_by_nhom_pkkh: SUM(value_col) *
    SelectedMonth / 12, grouped by (nhom_phu_trach, ten_pkkh). No SelectedPKKHNhomKey/
    dim_bdscif membership filter (that table isn't available outside Power BI) — the source
    table already carries nhom_phu_trach/ten_pkkh directly, so no key-join is needed anyway.
    Indexed by (nhom_phu_trach, pkkh) tuples."""
    selected_month = pd.to_datetime(date_str).month
    result = df.groupby(["nhom_phu_trach", "ten_pkkh"])[value_col].sum() * selected_month / 12
    result.index.names = ["nhom_phu_trach", "pkkh"]
    return result


@_df_cache()
def kh_ds_mbnt_by_nhom_pkkh(date_str: str) -> pd.Series:
    return _kh_by_nhom_pkkh(ke_hoach_ds_mbnt_pkkh_2026(), "ke_hoach_ds_mbnt", date_str)


@_df_cache()
def kh_mbnt_by_nhom_pkkh(date_str: str) -> pd.Series:
    return _kh_by_nhom_pkkh(ke_hoach_ln_mbnt_pkkh_2026(), "ke_hoach_ln_mbnt", date_str)


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("KH DS by (nhom, pkkh):")
    print(kh_ds_mbnt_by_nhom_pkkh(d).to_string())
    print("KH LN by (nhom, pkkh):")
    print(kh_mbnt_by_nhom_pkkh(d).to_string())
