import calendar
import pandas as pd
from data_connect.db_connect import _df_cache, silver_pvkh_dl_kh_luy_ke, pvkh_chiase

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
EXCLUDED_BDSCIF = "1609448630"
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


def _y_doanhso(date_str: str, group_cols) -> pd.Series:
    df = silver_pvkh_dl_kh_luy_ke(date_str)
    df = df[df["bdscif"] != EXCLUDED_BDSCIF]
    # A handful of rows carry no nhom_phu_trach at all (NULL in the source table) — left as NaN,
    # groupby() drops them silently, so they vanish even from TOTAL/pool_nhom (which are supposed
    # to sum everything). Tagging them with their own label keeps them out of any real nhóm's
    # breakdown (reindex(GROUPS,...) elsewhere still won't pick this label up) while letting them
    # surface in whatever sums across every group actually present, per user request.
    df = df.copy()
    df["nhom_phu_trach"] = df["nhom_phu_trach"].fillna("Không xác định")
    if "dia_ban" in group_cols:
        df = _clean_dia_ban(df)
    if "pkkh" in group_cols:
        df = df.copy()
        df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    return df.groupby(group_cols)["ds_mbnt_luy_ke_den_ngay_bc"].sum()


def _y_loinhuan(date_str: str, group_cols) -> pd.Series:
    """loi_nhuan_sau_chiase = loi_nhuan_truoc_chiase (silver_pvkh_DL_KH_luy_ke, already YTD cumulative)
    - loi_nhuan_chiase (pvkh_chiase, YTD sum through the effective month boundary, 2026 data)."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    first_day = ref_date.replace(month=1, day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    effective_month_boundary = (
        ref_month + pd.DateOffset(months=1) if ref_date.day == days_in_month else ref_month
    )

    df = silver_pvkh_dl_kh_luy_ke(date_str)
    df = df.copy()
    df["nhom_phu_trach"] = df["nhom_phu_trach"].fillna("Không xác định")
    if "dia_ban" in group_cols:
        df = _clean_dia_ban(df)
    if "pkkh" in group_cols:
        df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    truoc_chiase = df.groupby(group_cols)["ln_mbnt_luy_ke_den_ngay_bc"].sum()

    # pvkh_chiase() already normalizes KHCN centrally in db_connect.py's _fx_or_pstc_merged
    chiase_df = pvkh_chiase(date_str)  # date_str already scopes the query to its own year (2026)
    chiase_df["monthyear"] = pd.to_datetime(chiase_df["monthyear"])
    chiase_window = chiase_df[
        (chiase_df["monthyear"] >= first_day) & (chiase_df["monthyear"] < effective_month_boundary)
    ]
    chiase_group_cols = [_CHIASE_COL_MAP[c] for c in group_cols]
    chiase_by_group = chiase_window.groupby(chiase_group_cols)["loinhuanchiase"].sum()
    chiase_by_group.index.names = group_cols

    return truoc_chiase.subtract(chiase_by_group, fill_value=0.0)


@_df_cache()
def y_doanhso_by_nhom(date_str: str) -> pd.Series:
    """SUM(silver_pvkh_DL_KH_luy_ke[ds_mbnt_luy_ke_den_ngay_bc]), excluding bdscif 1609448630."""
    by_group = _y_doanhso(date_str, ["nhom_phu_trach"])
    total = by_group.sum()  # includes every group present (e.g. TSC), not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def y_loinhuan_by_nhom(date_str: str) -> pd.Series:
    by_group = _y_loinhuan(date_str, ["nhom_phu_trach"])
    total = by_group.sum()  # includes every group present (e.g. TSC), not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def y_loinhuan_gross_by_nhom(date_str: str) -> pd.Series:
    """SUM(silver_pvkh_DL_KH_luy_ke[ln_mbnt_luy_ke_den_ngay_bc]) — the "trước chia sẻ" leg of
    y_loinhuan_by_nhom, without subtracting pvkh_chiase. Not KBNN-excluded (LN never excludes
    KBNN anywhere else on the dashboard, only DS does)."""
    df = silver_pvkh_dl_kh_luy_ke(date_str).copy()
    df["nhom_phu_trach"] = df["nhom_phu_trach"].fillna("Không xác định")
    by_group = df.groupby("nhom_phu_trach")["ln_mbnt_luy_ke_den_ngay_bc"].sum()
    total = by_group.sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def y_nim_mbnt_nhom_diaban_pkkh(date_str: str) -> pd.Series:
    """NIM 2026 = loi_nhuan_sau_chiase / doanhso, by nhom_phu_trach + TOTAL.

    TOTAL = PTKD1+PTKD2+VPV+"Không xác định" (every group y_doanhso_by_nhom/y_loinhuan_by_nhom's
    own TOTAL already includes) — reverted from excluding "Không xác định" specifically for this
    ratio: neither silver_pvkh_DL_KH_luy_ke nor any other source table carries an actual
    nhom_phu_trach='TOTAL' row to select instead, so per user decision TOTAL here means "sum of
    every group actually present," same definition as the DS/LN totals, not a narrower
    PTKD1/2/VPV-only rate."""
    doanhso = y_doanhso_by_nhom(date_str)
    loinhuan = y_loinhuan_by_nhom(date_str)
    return loinhuan / doanhso.replace(0, pd.NA)


@_df_cache()
def _y_nim_by_nhom_dim(date_str: str, source_col: str, output_col: str) -> pd.DataFrame:
    group_cols = ["nhom_phu_trach", source_col]
    doanhso = _y_doanhso(date_str, group_cols).rename("doanh_so")
    loinhuan = _y_loinhuan(date_str, group_cols).rename("loi_nhuan")
    merged = pd.concat([doanhso, loinhuan], axis=1).fillna(0.0).reset_index()
    merged["nim"] = merged["loi_nhuan"] / merged["doanh_so"].replace(0, pd.NA)
    merged = merged.rename(columns={source_col: output_col})
    return merged[["nhom_phu_trach", output_col, "nim"]]


@_df_cache()
def y_nim_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """NIM 2026, grouped by (nhom_phu_trach, dia_ban) — both native to silver_pvkh_DL_KH_luy_ke."""
    return _y_nim_by_nhom_dim(date_str, "dia_ban", "dia_ban")


@_df_cache()
def y_nim_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    """NIM 2026, grouped by (nhom_phu_trach, pkkh) — both native to silver_pvkh_DL_KH_luy_ke."""
    return _y_nim_by_nhom_dim(date_str, "pkkh", "pkkh")


@_df_cache()
def _y_nim_by_dim_pooled(date_str: str, source_col: str, output_col: str) -> pd.DataFrame:
    """NIM 2026 pooled across every nhóm — doanh số and lợi nhuận are summed by dim_col alone
    (not per-nhóm) before dividing, so this is a genuine combined ratio (aggregate LN ÷
    aggregate DS), not an average of the per-nhóm NIMs. nhom_phu_trach is set to a constant
    placeholder so the result can still flow through _build_clustered_chart's usual merge/
    pool_nhom shape (one row per dim_col, groupby(dim_col).sum() on it is then a no-op)."""
    doanhso = _y_doanhso(date_str, [source_col]).rename("doanh_so")
    loinhuan = _y_loinhuan(date_str, [source_col]).rename("loi_nhuan")
    merged = pd.concat([doanhso, loinhuan], axis=1).fillna(0.0).reset_index()
    merged["nim"] = merged["loi_nhuan"] / merged["doanh_so"].replace(0, pd.NA)
    merged["nhom_phu_trach"] = ""
    merged = merged.rename(columns={source_col: output_col})
    return merged[["nhom_phu_trach", output_col, "nim"]]


def y_nim_diaban_pooled(date_str: str) -> pd.DataFrame:
    return _y_nim_by_dim_pooled(date_str, "dia_ban", "dia_ban")


def y_nim_pkkh_pooled(date_str: str) -> pd.DataFrame:
    return _y_nim_by_dim_pooled(date_str, "pkkh", "pkkh")


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("Doanh so:\n", y_doanhso_by_nhom(d))
    print("Loi nhuan (sau chiase):\n", y_loinhuan_by_nhom(d))
    print("NIM 2026:\n", y_nim_mbnt_nhom_diaban_pkkh(d))
    print("NIM 2026 by dia_ban:\n", y_nim_by_nhom_diaban(d).to_string())
    print("NIM 2026 by pkkh:\n", y_nim_by_nhom_pkkh(d).to_string())
