import pandas as pd
from data_connect.db_connect import _df_cache, silver_pvkh_dl_kh_luy_ke
from calculations.y_ln_mbnt_nhom_diaban_pkkh import _DIA_BAN_REPLACEMENTS

EXCLUDED_BDSCIF = "1609448630"  # KHO BAC NHA NUOC (bds 160, cif 9448630)


def _clean_dia_ban(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for old, new in _DIA_BAN_REPLACEMENTS:
        df["dia_ban"] = df["dia_ban"].str.replace(old, new, regex=False)
    return df


def _y_ds_mbnt(date_str: str, group_cols) -> pd.Series:
    """SUM(silver_pvkh_DL_KH_luy_ke[ds_mbnt_luy_ke_den_ngay_bc]), excluding KBNN (bdscif
    1609448630) per user request — same exclusion y_ds_hdls_nhom_diaban_pkkh.py already applies,
    so the dia_ban/pkkh charts treat both products' KBNN business consistently. (An earlier pass
    included KBNN here after reconciling against a headline HN total that turned out to already
    have had KBNN in it — see git history / prior conversation for that number; superseded by
    this explicit instruction.)

    nhom_phu_trach/dia_ban/pkkh are all native columns on this table — no listbds()/pkkh_lookup()
    join, per user request ("if it is from silver_pvkh_DL_KH_luy_ke then take the native
    columns"), same source of truth y_ln_mbnt_nhom_diaban_pkkh.py / y_nim_mbnt_nhom_diaban_pkkh.py
    already use for LN/NIM (those two measures do NOT exclude KBNN — no filter here reaches
    across into their own functions). A handful of rows carry no nhom_phu_trach at all (NULL in
    the source) — tagged "Không xác định" rather than silently dropped by groupby(), matching the
    LN/NIM siblings."""
    df = silver_pvkh_dl_kh_luy_ke(date_str)
    df = df[df["bdscif"] != EXCLUDED_BDSCIF].copy()
    df["nhom_phu_trach"] = df["nhom_phu_trach"].fillna("Không xác định")
    if "dia_ban" in group_cols:
        df = _clean_dia_ban(df)
    if "pkkh" in group_cols:
        df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    return df.groupby(list(group_cols))["ds_mbnt_luy_ke_den_ngay_bc"].sum()


@_df_cache()
def y_ds_mbnt_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """Grouped by (nhom_phu_trach, dia_ban), both native to silver_pvkh_DL_KH_luy_ke."""
    return _y_ds_mbnt(date_str, ("nhom_phu_trach", "dia_ban")).rename("doanh_so").reset_index()


@_df_cache()
def y_ds_mbnt_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """Grouped by (nhom_phu_trach, pkkh), both native to silver_pvkh_DL_KH_luy_ke."""
    return _y_ds_mbnt(date_str, ("nhom_phu_trach", "pkkh")).rename("doanh_so").reset_index()


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("By dia_ban:")
    print(y_ds_mbnt_by_nhom_diaban(d).to_string())
    print("By pkkh:")
    print(y_ds_mbnt_by_nhom_pkkh(d).to_string())
