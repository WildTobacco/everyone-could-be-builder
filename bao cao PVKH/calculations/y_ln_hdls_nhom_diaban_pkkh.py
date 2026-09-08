import pandas as pd
from data_connect.db_connect import _df_cache, silver_pvkh_dl_kh_luy_ke
from calculations.y_ln_mbnt_nhom_diaban_pkkh import _DIA_BAN_REPLACEMENTS


def _clean_dia_ban(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for old, new in _DIA_BAN_REPLACEMENTS:
        df["dia_ban"] = df["dia_ban"].str.replace(old, new, regex=False)
    return df


@_df_cache()
def _y_ln_hdls_per_bdscif(date_str: str) -> pd.DataFrame:
    """y_LN_HDLS_Nhom_DiaBan_PKKH: SUMX(VALUES[bdscif], CALCULATE(MAX(ln_hdls_luy_ke_den_ngay_bc)))
    = dedupe per-bdscif via MAX (no chiase deduction on this measure, unlike the MBNT LN one).
    nhom_phu_trach/dia_ban/pkkh are all native columns on silver_pvkh_DL_KH_luy_ke — no
    listbds()/pkkh_lookup() join, per user request ("if it is from silver_pvkh_DL_KH_luy_ke then
    take the native columns"), same source of truth y_ln_mbnt_nhom_diaban_pkkh.py /
    y_nim_mbnt_nhom_diaban_pkkh.py already use. This used to derive nhom_phu_trach/dia_ban via a
    bds -> listbds() join (pkkh had already been switched to native in an earlier pass, but not
    these two). No SelectedBDSCIF/dim_bdscif membership filter (that table isn't available
    outside Power BI)."""
    df = silver_pvkh_dl_kh_luy_ke(date_str)
    df = df.copy()
    df = _clean_dia_ban(df)
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"

    return df.groupby("bdscif").agg(
        ln=("ln_hdls_luy_ke_den_ngay_bc", "max"),
        nhom_phu_trach=("nhom_phu_trach", "first"),
        dia_ban=("dia_ban", "first"),
        pkkh=("pkkh", "first"),
    ).reset_index()


@_df_cache()
def y_ln_hdls_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """y_LN_HDLS_Nhom_DiaBan_PKKH, grouped by (nhom_phu_trach, dia_ban)."""
    per_bdscif = _y_ln_hdls_per_bdscif(date_str)
    result = per_bdscif.groupby(["nhom_phu_trach", "dia_ban"])["ln"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "loi_nhuan"]
    return result


@_df_cache()
def y_ln_hdls_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """y_LN_HDLS_Nhom_DiaBan_PKKH, grouped by (nhom_phu_trach, pkkh)."""
    per_bdscif = _y_ln_hdls_per_bdscif(date_str)
    result = per_bdscif.groupby(["nhom_phu_trach", "pkkh"])["ln"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "loi_nhuan"]
    return result


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("By dia_ban:\n", y_ln_hdls_by_nhom_diaban(d).to_string())
    print("By pkkh:\n", y_ln_hdls_by_nhom_pkkh(d).to_string())
