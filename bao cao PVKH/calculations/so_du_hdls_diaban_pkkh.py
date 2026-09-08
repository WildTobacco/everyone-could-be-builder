"""Số dư HĐLS (CCS+IRS combined) by (nhóm phụ trách, địa bàn | PKKH), from pvkh_dailyreport —
same customer-level source and cleanup as tdps_diaban_pkkh.py's số dư section, just summing
HĐLS's two sub-product balance columns instead of TDPS's single one.

"Ngày" uses that report day's own so_du_ccs_ngay_bc + so_du_irs_ngay_bc snapshot. "Lũy kế" uses
so_du_ccs_bq_nam + so_du_irs_bq_nam (average balance year-to-date through date_str) — balance
has no "sum since Jan 1" that would mean anything, so "lũy kế" here is the average, matching the
nhóm-level so_du_hdls_binh_quan already used elsewhere (e.g. pvkh_pstc_nhom_phu_trach /
so_du_hdls_ngay_by_nhom.py)."""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_dailyreport
from calculations.y_ln_mbnt_nhom_diaban_pkkh import _DIA_BAN_REPLACEMENTS
from calculations.date_table import latest_date


@_df_cache()
def _so_du_hdls(date_str: str) -> pd.DataFrame:
    df = pvkh_dailyreport(date_str).copy()
    for old, new in _DIA_BAN_REPLACEMENTS:
        df["dia_ban"] = df["dia_ban"].str.replace(old, new, regex=False)
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    df["so_du_hdls_ngay_bc"] = df["so_du_ccs_ngay_bc"] + df["so_du_irs_ngay_bc"]
    df["so_du_hdls_bq_nam"] = df["so_du_ccs_bq_nam"] + df["so_du_irs_bq_nam"]
    df = df.rename(columns={"nhom_phu_trach": "nhomphutrach", "dia_ban": "diaban"})
    return df[df["nhomphutrach"] != "0"]


def _shape(df: pd.DataFrame, dim_src: str, value_src: str, dim_out: str, value_out: str) -> pd.DataFrame:
    result = df.groupby(["nhomphutrach", dim_src])[value_src].sum().reset_index()
    result.columns = ["nhom_phu_trach", dim_out, value_out]
    return result


@_df_cache()
def so_du_hdls_ngay_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    df = _so_du_hdls(date_str)
    return _shape(df[df["diaban"] != "0"], "diaban", "so_du_hdls_ngay_bc", "dia_ban", "so_du")


@_df_cache()
def so_du_hdls_ngay_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    df = _so_du_hdls(date_str)
    return _shape(df[df["pkkh"] != "0"], "pkkh", "so_du_hdls_ngay_bc", "pkkh", "so_du")


@_df_cache()
def so_du_hdls_luy_ke_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    df = _so_du_hdls(date_str)
    return _shape(df[df["diaban"] != "0"], "diaban", "so_du_hdls_bq_nam", "dia_ban", "so_du")


@_df_cache()
def so_du_hdls_luy_ke_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    df = _so_du_hdls(date_str)
    return _shape(df[df["pkkh"] != "0"], "pkkh", "so_du_hdls_bq_nam", "pkkh", "so_du")


@_df_cache()
def so_du_hdls_irs_ccs_ngay_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """Same as so_du_hdls_ngay_by_nhom_diaban, but IRS and CCS kept as separate columns instead
    of summed — for the stacked IRS+CCS chart. LN has no equivalent split anywhere in the
    schema (pvkh_dailyreport only carries a combined ln_hdls_ngay_bc, no ln_irs/ln_ccs), so only
    Số dư and Doanh số get this treatment."""
    df = _so_du_hdls(date_str)
    df = df[df["diaban"] != "0"]
    result = df.groupby(["nhomphutrach", "diaban"])[["so_du_irs_ngay_bc", "so_du_ccs_ngay_bc"]].sum().reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "irs", "ccs"]
    return result


@_df_cache()
def so_du_hdls_irs_ccs_ngay_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    df = _so_du_hdls(date_str)
    df = df[df["pkkh"] != "0"]
    result = df.groupby(["nhomphutrach", "pkkh"])[["so_du_irs_ngay_bc", "so_du_ccs_ngay_bc"]].sum().reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "irs", "ccs"]
    return result


@_df_cache()
def so_du_hdls_irs_ccs_luy_ke_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    df = _so_du_hdls(date_str)
    df = df[df["diaban"] != "0"]
    result = df.groupby(["nhomphutrach", "diaban"])[["so_du_irs_bq_nam", "so_du_ccs_bq_nam"]].sum().reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "irs", "ccs"]
    return result


@_df_cache()
def so_du_hdls_irs_ccs_luy_ke_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    df = _so_du_hdls(date_str)
    df = df[df["pkkh"] != "0"]
    result = df.groupby(["nhomphutrach", "pkkh"])[["so_du_irs_bq_nam", "so_du_ccs_bq_nam"]].sum().reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "irs", "ccs"]
    return result


if __name__ == "__main__":
    d = latest_date()
    print(f"date: {d}\n")
    for name, fn in [
        ("Số dư HĐLS ngày / dia_ban", so_du_hdls_ngay_by_nhom_diaban),
        ("Số dư HĐLS lũy kế / dia_ban", so_du_hdls_luy_ke_by_nhom_diaban),
        ("Số dư HĐLS ngày / pkkh", so_du_hdls_ngay_by_nhom_pkkh),
        ("Số dư HĐLS lũy kế / pkkh", so_du_hdls_luy_ke_by_nhom_pkkh),
    ]:
        r = fn(d)
        print(f"--- {name}: {len(r)} rows, total {r.iloc[:, 2].sum():,.2f}")
        print(r.to_string(index=False, float_format=lambda x: f"{x:,.2f}"), "\n")
