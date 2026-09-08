"""NIM HĐLS ngày b/c by (nhóm phụ trách, địa bàn) and (nhóm phụ trách, PKKH), same formula as
nim_hdls_ngay_nhom.py's nhóm-only version:

    NIM = LN_HĐLS_ngày × 365 × 100 / ((số dư CCS ngày b/c + số dư IRS ngày b/c) × tỷ giá ngày b/c)

Sourced from bronze_baocaotudong.pvkh_dailyreport — the same customer-level table used for
TDPS's daily figures (nim_tdps_ngay_diaban_pkkh.py), which also carries HĐLS's own
ln_hdls_ngay_bc / so_du_ccs_ngay_bc / so_du_irs_ngay_bc columns alongside
nhom_phu_trach/dia_ban/pkkh — unlike silver_pvkh_dl_kh_luy_ke (used for the lũy kế/bình quân
version, nim_hdls_diaban_pkkh.py), which only carries cumulative figures.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_dailyreport, usd_vnd_rate

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _nim_hdls_ngay_by(date_str: str, dim_col: str) -> pd.DataFrame:
    df = pvkh_dailyreport(date_str)
    # "0" is a placeholder nhóm/dim on unmapped junk rows, not a real nhóm — same filter as
    # nim_tdps_diaban_pkkh.py.
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(["nhom_phu_trach", dim_col]).agg(
        ln=("ln_hdls_ngay_bc", "sum"),
        so_du_irs=("so_du_irs_ngay_bc", "sum"),
        so_du_ccs=("so_du_ccs_ngay_bc", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    so_du = grouped["so_du_irs"] + grouped["so_du_ccs"]
    if rate:
        grouped["nim"] = grouped["ln"] * 365 * 100 / (so_du * rate).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


@_df_cache()
def nim_hdls_ngay_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    result = _nim_hdls_ngay_by(date_str, "dia_ban")
    result.columns = ["nhom_phu_trach", "dia_ban", "nim"]
    return result


@_df_cache()
def nim_hdls_ngay_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    result = _nim_hdls_ngay_by(date_str, "pkkh")
    result.columns = ["nhom_phu_trach", "pkkh", "nim"]
    return result


def _nim_hdls_ngay_pooled(date_str: str, dim_col: str) -> pd.DataFrame:
    """NIM HĐLS ngày pooled across every nhóm — see nim_hdls_diaban_pkkh.py's
    _nim_hdls_pooled for why this is a genuine combined ratio, not an averaged one."""
    df = pvkh_dailyreport(date_str)
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(dim_col).agg(
        ln=("ln_hdls_ngay_bc", "sum"),
        so_du_irs=("so_du_irs_ngay_bc", "sum"),
        so_du_ccs=("so_du_ccs_ngay_bc", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    so_du = grouped["so_du_irs"] + grouped["so_du_ccs"]
    if rate:
        grouped["nim"] = grouped["ln"] * 365 * 100 / (so_du * rate).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    grouped["nhom_phu_trach"] = ""
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


def nim_hdls_ngay_diaban_pooled(date_str: str) -> pd.DataFrame:
    return _nim_hdls_ngay_pooled(date_str, "dia_ban")


def nim_hdls_ngay_pkkh_pooled(date_str: str) -> pd.DataFrame:
    return _nim_hdls_ngay_pooled(date_str, "pkkh")


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print("By dia_ban:\n", nim_hdls_ngay_by_nhom_diaban(d).to_string())
    print("By pkkh:\n", nim_hdls_ngay_by_nhom_pkkh(d).to_string())
