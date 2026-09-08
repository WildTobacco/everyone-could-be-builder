"""NIM HĐLS by (nhóm phụ trách, địa bàn) and (nhóm phụ trách, PKKH).

    NIM = LN_HĐLS_lũy_kế × 365 × 100 / ((số dư CCS bình quân + số dư IRS bình quân) × tỷ giá × số ngày từ 1/1 đến ngày báo cáo)

Unlike nim_hdls_binh_quan_nhom.py's nhóm-only version (a true day-by-day weighted average over
every day since 1/1 — see that module's docstring), this dimension breakdown only has a single
already-averaged bình quân balance per (nhóm, dia_ban/pkkh), with no daily granularity to
weight-average over. The "× số ngày từ 1/1 đến ngày báo cáo" term approximates the same
deflation the nhóm-level day-by-day sum produces implicitly, keeping this at a comparable scale
— same approximation used in nim_tdps_diaban_pkkh.py for the identical reason.

Sourced from silver.silver_pvkh_DL_KH_luy_ke, the one customer-level table that carries
nhom_phu_trach, dia_ban, pkkh, ln_hdls_luy_ke_den_ngay_bc and so_du_irs_bq_nam/so_du_ccs_bq_nam
all on the same row — unlike pvkh_pstc_dia_ban/_pkkh (which hold one dimension each and cannot
be crossed with nhóm). No Y-1 comparison: this table has no 2025 rows.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, silver_pvkh_dl_kh_luy_ke, usd_vnd_rate

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _nim_hdls_by(date_str: str, dim_col: str) -> pd.DataFrame:
    df = silver_pvkh_dl_kh_luy_ke(date_str)
    # matches the same defensive filter in nim_tdps_diaban_pkkh.py — "0" is a placeholder
    # nhóm/dim on unmapped junk rows, not a real nhóm.
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(["nhom_phu_trach", dim_col]).agg(
        ln=("ln_hdls_luy_ke_den_ngay_bc", "sum"),
        so_du_irs=("so_du_irs_bq_nam", "sum"),
        so_du_ccs=("so_du_ccs_bq_nam", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    so_du = grouped["so_du_irs"] + grouped["so_du_ccs"]
    if rate:
        year_start = pd.Timestamp(date_str).replace(month=1, day=1)
        so_ngay = (pd.Timestamp(date_str) - year_start).days + 1
        grouped["nim"] = grouped["ln"] * 365 * 100 / (so_du * rate * so_ngay).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


@_df_cache()
def nim_hdls_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    result = _nim_hdls_by(date_str, "dia_ban")
    result.columns = ["nhom_phu_trach", "dia_ban", "nim"]
    return result


@_df_cache()
def nim_hdls_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    result = _nim_hdls_by(date_str, "pkkh")
    result.columns = ["nhom_phu_trach", "pkkh", "nim"]
    return result


def _nim_hdls_pooled(date_str: str, dim_col: str) -> pd.DataFrame:
    """NIM HĐLS pooled across every nhóm — LN and số dư are summed by dim_col alone (not
    per-nhóm) before applying the NIM formula, so this is a genuine combined ratio, not an
    average of the per-nhóm NIMs. nhom_phu_trach is set to a constant placeholder so the result
    can still flow through _build_daily_dim_chart's usual pool_nhom shape (one row per dim_col,
    groupby(dim_col).sum() on it is then a no-op)."""
    df = silver_pvkh_dl_kh_luy_ke(date_str)
    df = df[df["nhom_phu_trach"].isin(GROUPS) & df[dim_col].notna() & (df[dim_col] != "0")]
    grouped = df.groupby(dim_col).agg(
        ln=("ln_hdls_luy_ke_den_ngay_bc", "sum"),
        so_du_irs=("so_du_irs_bq_nam", "sum"),
        so_du_ccs=("so_du_ccs_bq_nam", "sum"),
    ).reset_index()

    rate = usd_vnd_rate(date_str)
    so_du = grouped["so_du_irs"] + grouped["so_du_ccs"]
    if rate:
        year_start = pd.Timestamp(date_str).replace(month=1, day=1)
        so_ngay = (pd.Timestamp(date_str) - year_start).days + 1
        grouped["nim"] = grouped["ln"] * 365 * 100 / (so_du * rate * so_ngay).replace(0, pd.NA)
    else:
        grouped["nim"] = pd.NA
    grouped["nhom_phu_trach"] = ""
    return grouped[["nhom_phu_trach", dim_col, "nim"]]


def nim_hdls_diaban_pooled(date_str: str) -> pd.DataFrame:
    return _nim_hdls_pooled(date_str, "dia_ban")


def nim_hdls_pkkh_pooled(date_str: str) -> pd.DataFrame:
    return _nim_hdls_pooled(date_str, "pkkh")


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print("By dia_ban:\n", nim_hdls_by_nhom_diaban(d).to_string())
    print("By pkkh:\n", nim_hdls_by_nhom_pkkh(d).to_string())
