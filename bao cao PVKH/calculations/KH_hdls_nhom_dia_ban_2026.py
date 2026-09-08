from data_connect.db_connect import _df_cache
import pandas as pd
from data_connect.excel_connect import khkdcn_hdls_nhom_phu_trach_2026, listbds

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def _kh_filtered(date_str: str) -> pd.DataFrame:
    selected_month = pd.to_datetime(date_str).month
    df = khkdcn_hdls_nhom_phu_trach_2026()
    return df[df["Month"] <= selected_month]


@_df_cache()
def kh_hdls_nhom_dia_ban_2026(date_str: str) -> pd.Series:
    """Same shape as kh_mbnt_nhom_dia_ban_2026, sourced from KHKD CN 2026.xlsx's "KHKD HĐLS"
    columns instead of "KHKD KDNT"."""
    df = _kh_filtered(date_str)
    by_group = df.groupby("Nhóm phụ trách")["KHKD HDLS"].sum()
    total = by_group.sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def kh_hdls_by_nhom_diaban(date_str: str) -> pd.Series:
    """Same measure, broken down by (nhom_phu_trach, dia_ban) via a BDS -> listbds() join,
    since the KHKD CN target sheet is branch(BDS)-level (no dia_ban column of its own).
    Indexed by (nhom_phu_trach, dia_ban) tuples."""
    df = _kh_filtered(date_str)
    df = df.merge(listbds()[["bds", "diaban"]], left_on="BDS", right_on="bds", how="left")
    result = df.groupby(["Nhóm phụ trách", "diaban"])["KHKD HDLS"].sum()
    result.index.names = ["nhom_phu_trach", "dia_ban"]
    return result


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print(kh_hdls_nhom_dia_ban_2026(d))
    print("\nBy dia_ban:")
    print(kh_hdls_by_nhom_diaban(d).to_string())
