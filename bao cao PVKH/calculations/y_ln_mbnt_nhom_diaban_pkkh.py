import pandas as pd
from data_connect.db_connect import _df_cache, silver_pvkh_dl_kh_luy_ke, pvkh_chiase

# pvkh_chiase()'s dimension columns come from its own listbds/listcif join and use different names
# than silver_pvkh_DL_KH_luy_ke's native ones (nhomphutrach/diaban vs nhom_phu_trach/dia_ban).
_CHIASE_COL_MAP = {"nhom_phu_trach": "nhomphutrach", "dia_ban": "diaban", "pkkh": "pkkh"}
# silver_pvkh_DL_KH_luy_ke's native dia_ban needs the same cleanup Power Query applies upstream
# (raw values are inconsistent: full names / missing diacritics) before it matches listbds()'s labels.
_DIA_BAN_REPLACEMENTS = [
    ("Ha Noi", "HN"), ("Tay Nguyen", "TN"),
    ("DLPB", "ĐLPB"), ("DBSH", "ĐBSH"), ("DLPN", "ĐLPN"), ("DBSCL", "ĐBSCL"),
]


def _clean_dia_ban(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for old, new in _DIA_BAN_REPLACEMENTS:
        df["dia_ban"] = df["dia_ban"].str.replace(old, new, regex=False)
    return df


def _y_ln_sau_chiase(date_str: str, group_cols) -> pd.Series:
    """(Y)LN_MBNT_Nhom_DiaBan_PKKH's TotalLNsauChiaSe:
    TotalLNtruocChiaSe = SUM(silver_pvkh_DL_KH_luy_ke[ln_mbnt_luy_ke_den_ngay_bc]) WHERE ngay = SelectedDate
    LNChiaSe = SUM(pvkh_chiase[loinhuanchiase]) WHERE monthyear in [FirstDayOfYear, EffectiveMonthBoundary)
    TotalLNsauChiaSe = TotalLNtruocChiaSe - LNChiaSe."""
    ref_date = pd.to_datetime(date_str)
    first_day = ref_date.replace(month=1, day=1)
    current_month_start = ref_date.replace(day=1)
    is_last_day_of_month = ref_date == (current_month_start + pd.offsets.MonthEnd(0))
    effective_month_boundary = (
        current_month_start + pd.DateOffset(months=1) if is_last_day_of_month else current_month_start
    )

    df = silver_pvkh_dl_kh_luy_ke(date_str)
    df = df.copy()
    # A handful of rows carry no nhom_phu_trach at all (NULL in the source table) — left as NaN,
    # groupby() drops them silently, so they vanish even from TOTAL/pool_nhom (which are supposed
    # to sum everything). Tagging them with their own label keeps them out of any real nhóm's
    # breakdown (reindex(GROUPS,...) elsewhere still won't pick this label up) while letting them
    # surface in whatever sums across every group actually present, per user request.
    df["nhom_phu_trach"] = df["nhom_phu_trach"].fillna("Không xác định")
    if "dia_ban" in group_cols:
        df = _clean_dia_ban(df)
    if "pkkh" in group_cols:
        df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    total_ln_truoc_chiase = df.groupby(group_cols)["ln_mbnt_luy_ke_den_ngay_bc"].sum()

    # pvkh_chiase() already normalizes KHCN centrally in db_connect.py's _fx_or_pstc_merged
    chiase_df = pvkh_chiase(date_str)  # date_str already scopes the query to its own year (2026)
    chiase_df["monthyear"] = pd.to_datetime(chiase_df["monthyear"])
    chiase_window = chiase_df[
        (chiase_df["monthyear"] >= first_day) & (chiase_df["monthyear"] < effective_month_boundary)
    ]
    chiase_group_cols = [_CHIASE_COL_MAP[c] for c in group_cols]
    ln_chia_se = chiase_window.groupby(chiase_group_cols)["loinhuanchiase"].sum()
    ln_chia_se.index.names = group_cols

    return total_ln_truoc_chiase.subtract(ln_chia_se, fill_value=0.0)


@_df_cache()
def y_ln_mbnt_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """TotalLNsauChiaSe, grouped by (nhom_phu_trach, dia_ban)."""
    return _y_ln_sau_chiase(date_str, ["nhom_phu_trach", "dia_ban"]).rename("loi_nhuan").reset_index()


@_df_cache()
def y_ln_mbnt_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """TotalLNsauChiaSe, grouped by (nhom_phu_trach, pkkh)."""
    return _y_ln_sau_chiase(date_str, ["nhom_phu_trach", "pkkh"]).rename("loi_nhuan").reset_index()


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("LN sau chiase by dia_ban:\n", y_ln_mbnt_by_nhom_diaban(d).to_string())
    print("LN sau chiase by pkkh:\n", y_ln_mbnt_by_nhom_pkkh(d).to_string())
