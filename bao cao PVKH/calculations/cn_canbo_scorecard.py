"""Python port of the per-staff (Cán bộ phụ trách) DAX measure set.

Grain: one row per staff member who has a 'pvkh_KQ_CanBo' row on the selected
date (mirrors a Power BI table visual grouped by 'pvkh_KQ_CanBo'[CB_phu_trach],
page-filtered to a single 'DateTable'[Ngay]).

'%' isn't a legal Python identifier character, so every '%Measure' DAX name is
ported as 'PctMeasure' here (e.g. '%HoanThanh_Nam_KDNTPS_CB' -> 'PctHoanThanh_Nam_KDNTPS_CB').
'KDNT&PS' is ported as 'KDNTPS' (no '&'), matching the spelling already used
elsewhere in this codebase (e.g. LN_KDNTPS_LuyKe_CN).
"""

from data_connect.db_connect import _df_cache
import functools

import numpy as np
import pandas as pd

from data_connect.db_connect import get_connection, pvkh_kq_chinhanh
from data_connect.excel_connect import khkd_cn_ht
from calculations.pvkh_kq_canbo import pvkh_KQ_CanBo

KDNTPS_T1_T7_COLUMNS = [f"KHKD KDNT&PS T{i}.2026" for i in range(1, 8)]

KQ_LUY_KE_COLUMNS = {
    "hdls": "sum_ln_hdls_luy_ke",
    "kdntps": "sum_ln_kdntps_luy_ke",
    "mbnt": "sum_ln_mbnt_luy_ke_den_ngay_bc",
    "pshh": "sum_ln_pshh_luy_ke",
    "tdps": "sum_ln_tdps_luy_ke",
}

KBNN_BDS = 160
KBNN_ANNUAL_DEDUCTION = 110_000.0
KBNN_T7_DEDUCTION = 110_000 / 100 * 57  # = 62,700 — literal port of the DAX constant


@functools.lru_cache(maxsize=1)
def _cn_ht() -> pd.DataFrame:
    return khkd_cn_ht()


@functools.lru_cache(maxsize=1)
def _staff_table() -> pd.DataFrame:
    return pvkh_KQ_CanBo()


@functools.lru_cache(maxsize=1)
def _kq_chinhanh_all() -> pd.DataFrame:
    df = pvkh_kq_chinhanh()
    df["bds"] = pd.to_numeric(df["bds"], errors="coerce").astype("Int64")
    return df


@functools.lru_cache(maxsize=1)
def _staff_bds_map() -> pd.DataFrame:
    """One row per (staff, BDS) pair, from KHKD CN HT's 'Cán bộ phụ trách' -> 'BDS'."""
    ht = _cn_ht()[["BDS", "Cán bộ phụ trách"]].dropna()
    ht["BDS"] = ht["BDS"].astype(int)
    return ht.drop_duplicates()


@functools.lru_cache(maxsize=1)
def _staff_bds_sets() -> dict:
    return _staff_bds_map().groupby("Cán bộ phụ trách")["BDS"].apply(set).to_dict()


@functools.lru_cache(maxsize=1)
def LoiNhuan_KBNN() -> float:
    """Raw (un-scaled) 2026 profit-share for the KBNN client (cif 9448630, bds 160)."""
    conn = get_connection()
    df = pd.read_sql(
        "SELECT loinhuanchiase FROM bronze_baocaotudong.pvkh_chiase "
        "WHERE cif = 9448630 AND bds = 160 AND EXTRACT(YEAR FROM monthyear) = 2026;",
        conn
    )
    conn.close()
    return float(df["loinhuanchiase"].sum())


def _dax_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


@functools.lru_cache(maxsize=64)
def _scorecard(selected_date: str) -> pd.DataFrame:
    """Full per-staff scorecard (all measures) for one date. Indexed by CB_phu_trach."""
    target = pd.to_datetime(selected_date).date()

    staff_today = _staff_table()
    staff_today = staff_today[staff_today["Ngay"] == target]
    staff_today = staff_today[["CB_phu_trach", "Nhóm phụ trách"]].drop_duplicates("CB_phu_trach")
    df = staff_today.set_index("CB_phu_trach")

    ht = _cn_ht()
    kh_2026 = ht.groupby("Cán bộ phụ trách")["KHKD KDNT&PS 2026"].sum()
    kh_t7 = ht.groupby("Cán bộ phụ trách")[KDNTPS_T1_T7_COLUMNS].sum().sum(axis=1)

    df["KH_KDNTPS_2026_CB"] = kh_2026.reindex(df.index).fillna(0.0)
    df["KH_KDNTPS_T7_2026_CB"] = kh_t7.reindex(df.index).fillna(0.0)

    staff_bds_sets = _staff_bds_sets()
    is_bds_160 = df.index.to_series().map(lambda s: KBNN_BDS in staff_bds_sets.get(s, set()))

    df["KH_KDNTPS_2026_CB_ko_KBNN"] = df["KH_KDNTPS_2026_CB"] - is_bds_160 * KBNN_ANNUAL_DEDUCTION
    df["KH_KDNTPS_T7_2026_CB_ko_KBNN"] = df["KH_KDNTPS_T7_2026_CB"] - is_bds_160 * KBNN_T7_DEDUCTION

    staff_bds = _staff_bds_map()
    kq_today = _kq_chinhanh_all()
    kq_today = kq_today[kq_today["ngay"] == target]
    exploded = staff_bds.merge(kq_today, left_on="BDS", right_on="bds", how="left")
    ln_by_staff = exploded.groupby("Cán bộ phụ trách")[list(KQ_LUY_KE_COLUMNS.values())].sum(min_count=0)
    ln_by_staff = ln_by_staff.reindex(df.index).fillna(0.0)

    df["LN_HDLS_LuyKe_CB"] = ln_by_staff[KQ_LUY_KE_COLUMNS["hdls"]] / 1_000_000
    df["LN_KDNTPS_LuyKe_CB"] = ln_by_staff[KQ_LUY_KE_COLUMNS["kdntps"]] / 1_000_000
    df["LN_MBNT_LuyKe_CB"] = ln_by_staff[KQ_LUY_KE_COLUMNS["mbnt"]] / 1_000_000
    df["LN_PSHH_LuyKe_CB"] = ln_by_staff[KQ_LUY_KE_COLUMNS["pshh"]] / 1_000_000
    df["LN_TDPS_LuyKe_CB"] = ln_by_staff[KQ_LUY_KE_COLUMNS["tdps"]] / 1_000_000

    kbnn_raw = LoiNhuan_KBNN()
    kbnn_deduction = is_bds_160 * kbnn_raw
    df["LN_KDNTPS_LuyKe_CB_ko_KBNN"] = (ln_by_staff[KQ_LUY_KE_COLUMNS["kdntps"]] - kbnn_deduction) / 1_000_000
    df["LN_MBNT_LuyKe_CB_ko_KBNN"] = (ln_by_staff[KQ_LUY_KE_COLUMNS["mbnt"]] - kbnn_deduction) / 1_000_000

    df["PctHoanThanh_Nam_KDNTPS_CB"] = _dax_divide(df["LN_KDNTPS_LuyKe_CB"], df["KH_KDNTPS_2026_CB"])
    df["PctHoanThanh_Nam_KDNTPS_CB_ko_KBNN"] = _dax_divide(df["LN_KDNTPS_LuyKe_CB_ko_KBNN"], df["KH_KDNTPS_2026_CB_ko_KBNN"])
    df["PctHoanThanh_Thang_KDNTPS_CB"] = _dax_divide(df["LN_KDNTPS_LuyKe_CB"], df["KH_KDNTPS_T7_2026_CB"])
    df["PctHoanThanh_Thang_KDNTPS_CB_ko_KBNN"] = _dax_divide(df["LN_KDNTPS_LuyKe_CB_ko_KBNN"], df["KH_KDNTPS_T7_2026_CB_ko_KBNN"])

    # RANKX(ALLSELECTED(...), measure, , DESC, DENSE), ranked within the current Nhóm phụ
    # trách filter context: highest % = rank 1, ties share a rank. Ranked by the _ko_KBNN
    # variant, which is also now what's displayed as "% năm" — see DISPLAY_COLUMNS — so this
    # stays sequential with the table's own sort order without a separate basis mismatch.
    df["STT_PctNam_CB"] = df.groupby("Nhóm phụ trách")["PctHoanThanh_Nam_KDNTPS_CB_ko_KBNN"].rank(method="dense", ascending=False)

    return df


# ---- thin wrappers, one per DAX measure name, so each can be called directly ----

@_df_cache()
def KH_KDNTPS_2026_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["KH_KDNTPS_2026_CB"]


@_df_cache()
def KH_KDNTPS_2026_CB_ko_KBNN(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["KH_KDNTPS_2026_CB_ko_KBNN"]


@_df_cache()
def KH_KDNTPS_T7_2026_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["KH_KDNTPS_T7_2026_CB"]


@_df_cache()
def KH_KDNTPS_T7_2026_CB_ko_KBNN(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["KH_KDNTPS_T7_2026_CB_ko_KBNN"]


@_df_cache()
def LN_HDLS_LuyKe_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["LN_HDLS_LuyKe_CB"]


@_df_cache()
def LN_KDNTPS_LuyKe_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["LN_KDNTPS_LuyKe_CB"]


@_df_cache()
def LN_KDNTPS_LuyKe_CB_ko_KBNN(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["LN_KDNTPS_LuyKe_CB_ko_KBNN"]


@_df_cache()
def LN_MBNT_LuyKe_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["LN_MBNT_LuyKe_CB"]


@_df_cache()
def LN_MBNT_LuyKe_CB_ko_KBNN(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["LN_MBNT_LuyKe_CB_ko_KBNN"]


@_df_cache()
def LN_PSHH_LuyKe_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["LN_PSHH_LuyKe_CB"]


@_df_cache()
def LN_TDPS_LuyKe_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["LN_TDPS_LuyKe_CB"]


@_df_cache()
def PctHoanThanh_Nam_KDNTPS_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["PctHoanThanh_Nam_KDNTPS_CB"]


@_df_cache()
def PctHoanThanh_Nam_KDNTPS_CB_ko_KBNN(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["PctHoanThanh_Nam_KDNTPS_CB_ko_KBNN"]


@_df_cache()
def PctHoanThanh_Thang_KDNTPS_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["PctHoanThanh_Thang_KDNTPS_CB"]


@_df_cache()
def PctHoanThanh_Thang_KDNTPS_CB_ko_KBNN(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["PctHoanThanh_Thang_KDNTPS_CB_ko_KBNN"]


@_df_cache()
def STT_PctNam_CB(selected_date: str) -> pd.Series:
    return _scorecard(selected_date)["STT_PctNam_CB"]


@_df_cache()
def Rank_Today(selected_date: str) -> pd.Series:
    """Alias of STT_PctNam_CB — same RANKX formula, kept as its own name to match the DAX."""
    return STT_PctNam_CB(selected_date)


@_df_cache()
def Rank_MonthAgo(selected_date: str) -> pd.Series:
    """Ranked over TODAY's staff roster using each person's %-completion from 1 month ago
    (same day-of-month; pd.DateOffset handles shorter months), so a staff member who joined
    since then (no row a month back at all) still gets a baseline rank — treated as 0% (worst),
    rather than excluded/blank. The displayed column is "Thay đổi (m/m)" — month-over-month,
    not day-over-day; a 1-day lookback almost never reorders a cumulative YTD % this late in
    the year, which is why it always showed "—" before this fix."""
    month_ago = (pd.to_datetime(selected_date) - pd.DateOffset(months=1)).strftime("%Y-%m-%d")
    today_groups = _scorecard(selected_date)["Nhóm phụ trách"]
    month_ago_pct = PctHoanThanh_Nam_KDNTPS_CB_ko_KBNN(month_ago)
    pct = month_ago_pct.reindex(today_groups.index).fillna(0.0)
    return pct.groupby(today_groups).rank(method="dense", ascending=False)


@_df_cache()
def _rank_diff(selected_date: str) -> pd.DataFrame:
    today = Rank_Today(selected_date)
    month_ago = Rank_MonthAgo(selected_date)
    combined = pd.DataFrame({"today": today, "month_ago": month_ago})
    combined["diff"] = combined["month_ago"] - combined["today"]
    return combined


@_df_cache()
def ThaydoiRank_Num(selected_date: str) -> pd.Series:
    return _rank_diff(selected_date)["diff"]


@_df_cache()
def STT_Change_CB(selected_date: str) -> pd.Series:
    diff = ThaydoiRank_Num(selected_date)

    def _fmt(d):
        if pd.isna(d):
            return None
        if d > 0:
            return f"▲ {int(d)}"
        if d < 0:
            return f"▼ {int(abs(d))}"
        return "—"

    return diff.map(_fmt)


DISPLAY_COLUMNS = {
    "STT_PctNam_CB": "STT",
    "STT_Change_CB": "Thay đổi (m/m)",
    # KH KDNT&PS, KQ MBNT, KQ KDNT&PS, % tháng, % năm all use the _ko_KBNN variant — Power BI's
    # actual displayed figures net out the KBNN client's plan/profit for whichever staff member
    # is attributed to it (bds 160), not just an internal ranking-only adjustment.
    "KH_KDNTPS_2026_CB_ko_KBNN": "KH KDNT&PS 2026 (tr đồng)",
    "LN_MBNT_LuyKe_CB_ko_KBNN": "KQ MBNT (tr đồng)",
    "LN_HDLS_LuyKe_CB": "KQ HĐLS (tr đồng)",
    "LN_TDPS_LuyKe_CB": "KQ TDPS (tr đồng)",
    "LN_PSHH_LuyKe_CB": "KQ PSHH (tr đồng)",
    "LN_KDNTPS_LuyKe_CB_ko_KBNN": "KQ KDNT&PS (tr đồng)",
    "PctHoanThanh_Thang_KDNTPS_CB_ko_KBNN": "% tháng",
    "PctHoanThanh_Nam_KDNTPS_CB_ko_KBNN": "% năm",
}


@_df_cache()
def staff_table(selected_date: str) -> pd.DataFrame:
    """Scorecard columns renamed to their Power BI display headers, plus Nhóm phụ trách for grouping."""
    df = _scorecard(selected_date).copy()
    df["STT_Change_CB"] = STT_Change_CB(selected_date)
    df = df.reset_index().rename(columns={"CB_phu_trach": "Cán bộ"})
    df = df[["Nhóm phụ trách", "Cán bộ"] + list(DISPLAY_COLUMNS.keys())]
    return df.rename(columns=DISPLAY_COLUMNS)


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    date_str = "2026-08-10"
    sc = _scorecard(date_str)
    print(sc[[
        "Nhóm phụ trách", "KH_KDNTPS_2026_CB_ko_KBNN", "LN_KDNTPS_LuyKe_CB_ko_KBNN",
        "PctHoanThanh_Nam_KDNTPS_CB_ko_KBNN", "STT_PctNam_CB",
    ]].sort_values("STT_PctNam_CB").to_string())
    print()
    print("LoiNhuan_KBNN:", LoiNhuan_KBNN())
    print()
    print(STT_Change_CB(date_str).dropna().to_string())
