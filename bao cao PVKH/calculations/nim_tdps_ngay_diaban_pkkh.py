"""NIM TDPS ngày b/c by (nhóm phụ trách, địa bàn) and (nhóm phụ trách, PKKH), same formula as
nim_tdps_ngay_nhom.py's nhóm-only version:

    NIM = LN_TDPS_ngày × 365 × 100 / (số dư TDPS ngày b/c × tỷ giá ngày b/c)

Sourced from bronze_baocaotudong.pvkh_dailyreport, same table as the lũy kế/bình quân version
(nim_tdps_diaban_pkkh.py) but reading the day's own ln_tdps_ngay_bc / so_du_tdps_ngay_bc
columns instead of the cumulative ones.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_dailyreport, usd_vnd_rate

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _nim_tdps_ngay_by(date_str: str, dim_col: str) -> pd.DataFrame:
    df = pvkh_dailyreport(date_str)
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(["nhom_phu_trach", dim_col]).agg(
        ln=("ln_tdps_ngay_bc", "sum"),
        so_du=("so_du_tdps_ngay_bc", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    if rate:
        grouped["nim"] = grouped["ln"] * 365 * 100 / (grouped["so_du"] * rate).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


@_df_cache()
def nim_tdps_ngay_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    result = _nim_tdps_ngay_by(date_str, "dia_ban")
    result.columns = ["nhom_phu_trach", "dia_ban", "nim"]
    return result


@_df_cache()
def nim_tdps_ngay_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    result = _nim_tdps_ngay_by(date_str, "pkkh")
    result.columns = ["nhom_phu_trach", "pkkh", "nim"]
    return result


def _nim_tdps_ngay_pooled(date_str: str, dim_col: str) -> pd.DataFrame:
    """NIM TDPS ngày pooled across every nhóm — see nim_hdls_diaban_pkkh.py's
    _nim_hdls_pooled for why this is a genuine combined ratio, not an averaged one."""
    df = pvkh_dailyreport(date_str)
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(dim_col).agg(
        ln=("ln_tdps_ngay_bc", "sum"),
        so_du=("so_du_tdps_ngay_bc", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    if rate:
        grouped["nim"] = grouped["ln"] * 365 * 100 / (grouped["so_du"] * rate).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    grouped["nhom_phu_trach"] = ""
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


def nim_tdps_ngay_diaban_pooled(date_str: str) -> pd.DataFrame:
    return _nim_tdps_ngay_pooled(date_str, "dia_ban")


def nim_tdps_ngay_pkkh_pooled(date_str: str) -> pd.DataFrame:
    return _nim_tdps_ngay_pooled(date_str, "pkkh")


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print("By dia_ban:\n", nim_tdps_ngay_by_nhom_diaban(d).to_string())
    print("By pkkh:\n", nim_tdps_ngay_by_nhom_pkkh(d).to_string())
