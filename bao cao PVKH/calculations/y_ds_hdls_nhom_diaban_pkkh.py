import pandas as pd
from data_connect.db_connect import _df_cache, silver_pvkh_dl_kh_luy_ke
from calculations.y_ln_mbnt_nhom_diaban_pkkh import _DIA_BAN_REPLACEMENTS

EXCLUDED_BDSCIF = "1609448630"


def _clean_dia_ban(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for old, new in _DIA_BAN_REPLACEMENTS:
        df["dia_ban"] = df["dia_ban"].str.replace(old, new, regex=False)
    return df


@_df_cache()
def _y_ds_hdls_per_bdscif(date_str: str) -> pd.DataFrame:
    """Y_DS_HDLS_Nhom_DiaBan_PKKH: SUMX(VALUES[bdscif], CALCULATE(MAX(ds_hdls_luy_ke_den_ngay_bc)))
    = dedupe per-bdscif via MAX, excluding bdscif 1609448630. nhom_phu_trach/dia_ban/pkkh are all
    native columns on silver_pvkh_DL_KH_luy_ke — no listbds()/pkkh_lookup() join, per user request
    ("if it is from silver_pvkh_DL_KH_luy_ke then take the native columns"), same source of truth
    y_ln_mbnt_nhom_diaban_pkkh.py / y_nim_mbnt_nhom_diaban_pkkh.py already use. This used to
    derive nhom_phu_trach/dia_ban via a bds -> listbds() join (pkkh had already been switched to
    native in an earlier pass, but not these two). No SelectedBDSCIF/dim_bdscif membership filter
    (that table isn't available outside Power BI)."""
    df = silver_pvkh_dl_kh_luy_ke(date_str)
    df = df[df["bdscif"] != EXCLUDED_BDSCIF].copy()
    df = _clean_dia_ban(df)
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"

    return df.groupby("bdscif").agg(
        ds=("ds_hdls_luy_ke_den_ngay_bc", "max"),
        irs=("ds_irs_luy_ke_den_ngay_bc", "max"),
        ccs=("ds_ccs_luy_ke_den_ngay_bc", "max"),
        nhom_phu_trach=("nhom_phu_trach", "first"),
        dia_ban=("dia_ban", "first"),
        pkkh=("pkkh", "first"),
    ).reset_index()


@_df_cache()
def y_ds_hdls_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """Y_DS_HDLS_Nhom_DiaBan_PKKH, grouped by (nhom_phu_trach, dia_ban)."""
    per_bdscif = _y_ds_hdls_per_bdscif(date_str)
    result = per_bdscif.groupby(["nhom_phu_trach", "dia_ban"])["ds"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "doanh_so"]
    return result


@_df_cache()
def y_ds_hdls_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """Y_DS_HDLS_Nhom_DiaBan_PKKH, grouped by (nhom_phu_trach, pkkh)."""
    per_bdscif = _y_ds_hdls_per_bdscif(date_str)
    result = per_bdscif.groupby(["nhom_phu_trach", "pkkh"])["ds"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "doanh_so"]
    return result


@_df_cache()
def y_ds_hdls_irs_ccs_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """Same source/grouping as y_ds_hdls_by_nhom_diaban, but IRS and CCS kept as separate
    columns instead of summed into one doanh_so total — for the stacked IRS+CCS chart. LN has
    no equivalent split: silver only carries a combined ln_hdls_luy_ke_den_ngay_bc column, not
    per-sub-product ones, at customer level."""
    per_bdscif = _y_ds_hdls_per_bdscif(date_str)
    result = per_bdscif.groupby(["nhom_phu_trach", "dia_ban"])[["irs", "ccs"]].sum().reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "irs", "ccs"]
    return result


@_df_cache()
def y_ds_hdls_irs_ccs_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    per_bdscif = _y_ds_hdls_per_bdscif(date_str)
    result = per_bdscif.groupby(["nhom_phu_trach", "pkkh"])[["irs", "ccs"]].sum().reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "irs", "ccs"]
    return result


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("By dia_ban:\n", y_ds_hdls_by_nhom_diaban(d).to_string())
    print("By pkkh:\n", y_ds_hdls_by_nhom_pkkh(d).to_string())
