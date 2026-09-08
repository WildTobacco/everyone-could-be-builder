"""NIM TDPS by (nhóm phụ trách, địa bàn) and (nhóm phụ trách, PKKH), same formula/shape as
nim_hdls_diaban_pkkh.py's HĐLS version:

    NIM = LN_TDPS_lũy_kế × 365 × 100 / (số dư TDPS bình quân × tỷ giá × số ngày từ 1/1 đến ngày báo cáo)

The "× số ngày từ 1/1 đến ngày báo cáo" term matches the same fix applied to the nhóm-level
version (nim_tdps_binh_quan_nhom.py) — without it, the result is inflated by roughly the
number of days elapsed since Jan 1 (this granularity had been missing it).

Sourced from bronze_baocaotudong.pvkh_dailyreport, the customer-level table that carries
nhom_phu_trach, dia_ban, pkkh, ln_tdps_luy_ke_den_ngay_bc and so_du_tdps_bq_nam all on the same
row. No Y-1 comparison: this table covers 2026 only.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_dailyreport, usd_vnd_rate

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _nim_tdps_by(date_str: str, dim_col: str) -> pd.DataFrame:
    df = pvkh_dailyreport(date_str)
    # "0" shows up as a literal placeholder nhóm/dim on unmapped junk rows (bds/dia_ban also
    # "0" on those same rows) — not a real nhóm, unlike "TSC" elsewhere in this project.
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(["nhom_phu_trach", dim_col]).agg(
        ln=("ln_tdps_luy_ke_den_ngay_bc", "sum"),
        so_du=("so_du_tdps_bq_nam", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    if rate:
        year_start = pd.Timestamp(date_str).replace(month=1, day=1)
        so_ngay = (pd.Timestamp(date_str) - year_start).days + 1
        grouped["nim"] = grouped["ln"] * 365 * 100 / (grouped["so_du"] * rate * so_ngay).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


@_df_cache()
def nim_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    result = _nim_tdps_by(date_str, "dia_ban")
    result.columns = ["nhom_phu_trach", "dia_ban", "nim"]
    return result


@_df_cache()
def nim_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    result = _nim_tdps_by(date_str, "pkkh")
    result.columns = ["nhom_phu_trach", "pkkh", "nim"]
    return result


def _nim_tdps_pooled(date_str: str, dim_col: str) -> pd.DataFrame:
    """NIM TDPS pooled across every nhóm — see nim_hdls_diaban_pkkh.py's _nim_hdls_pooled for
    why this is a genuine combined ratio, not an averaged one."""
    df = pvkh_dailyreport(date_str)
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(dim_col).agg(
        ln=("ln_tdps_luy_ke_den_ngay_bc", "sum"),
        so_du=("so_du_tdps_bq_nam", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    if rate:
        year_start = pd.Timestamp(date_str).replace(month=1, day=1)
        so_ngay = (pd.Timestamp(date_str) - year_start).days + 1
        grouped["nim"] = grouped["ln"] * 365 * 100 / (grouped["so_du"] * rate * so_ngay).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    grouped["nhom_phu_trach"] = ""
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


def nim_tdps_diaban_pooled(date_str: str) -> pd.DataFrame:
    return _nim_tdps_pooled(date_str, "dia_ban")


def nim_tdps_pkkh_pooled(date_str: str) -> pd.DataFrame:
    return _nim_tdps_pooled(date_str, "pkkh")


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print("By dia_ban:\n", nim_tdps_by_nhom_diaban(d).to_string())
    print("By pkkh:\n", nim_tdps_by_nhom_pkkh(d).to_string())
