"""Python port of the 'CN trọng điểm' (key branch) DAX measures.

Grain: one row per branch in CN_trong_diem() (the 64 key branches), keyed by BDS.
Every named function below returns a pd.Series of that measure indexed by "Chi nhánh",
matching its original DAX measure name (with "%" spelled out as "Pct" since Python
identifiers can't contain "%").

KH_KDNTPS_T6_CN / KH_MBNT_T2_CN / KH_PSTC_T2_CN intentionally hardcode months
T1-T6 / T2 exactly as the source DAX does — they are not derived from selected_date.
"""

from data_connect.db_connect import _df_cache
import functools

import numpy as np
import pandas as pd

from data_connect.db_connect import pvkh_kq_chinhanh
from data_connect.excel_connect import CN_trong_diem, khkd_cn_ht, khkd_cn_td

KDNTPS_T1_T6_COLUMNS = [f"KHKD KDNT&PS T{i}.2026" for i in range(1, 7)]
KQ_LUY_KE_COLUMNS = [
    "sum_ln_hdls_luy_ke",
    "sum_ln_kdntps_luy_ke",
    "sum_ln_mbnt_luy_ke_den_ngay_bc",
    "sum_ln_pshh_luy_ke",
    "sum_ln_tdps_luy_ke",
]


@functools.lru_cache(maxsize=1)
def _cn_ht() -> pd.DataFrame:
    return khkd_cn_ht()


@functools.lru_cache(maxsize=1)
def _cn_td() -> pd.DataFrame:
    return khkd_cn_td()


@functools.lru_cache(maxsize=1)
def _cn_trong_diem() -> pd.DataFrame:
    return CN_trong_diem()


@functools.lru_cache(maxsize=1)
def _kq_chinhanh_all() -> pd.DataFrame:
    df = pvkh_kq_chinhanh()
    df["bds"] = pd.to_numeric(df["bds"], errors="coerce").astype("Int64")
    return df


def _dax_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """DIVIDE(numerator, denominator, BLANK()) — NaN instead of inf/nan-on-0/0 when denominator is 0."""
    return numerator / denominator.replace(0, np.nan)


@functools.lru_cache(maxsize=32)
def _scorecard(selected_date: str) -> pd.DataFrame:
    base = _cn_trong_diem()[["BDS", "Chi nhánh", "Nhóm phụ trách", "Cán bộ phụ trách"]].set_index("BDS")

    ht_by_bds = _cn_ht().groupby("BDS")[["KHKD KDNT&PS 2026"]].sum()

    td = _cn_td()
    td_by_bds = td.groupby("BDS")[KDNTPS_T1_T6_COLUMNS].sum()
    td_by_chinhanh = td.groupby("Chi nhánh")[[
        "KHKD KDNT 2026 (triệu đồng)", "KHKD KDNT T2.2026",
        "KHKD PSTC 2026", "KHKD PSTC T2.2026",
    ]].sum()

    kq = _kq_chinhanh_all()
    target = pd.to_datetime(selected_date).date()
    kq_today_by_bds = kq[kq["ngay"] == target].groupby("bds")[KQ_LUY_KE_COLUMNS].sum()

    numeric = ht_by_bds.join(td_by_bds, how="left").join(kq_today_by_bds, how="left")
    numeric = numeric.reindex(base.index).fillna(0.0)
    numeric = numeric.join(td_by_chinhanh.reindex(base["Chi nhánh"]).set_axis(base.index).fillna(0.0))

    df = base.join(numeric)

    df["KH_KDNTPS_2026_CN"] = df["KHKD KDNT&PS 2026"]
    df["KH_KDNTPS_T6_CN"] = df[KDNTPS_T1_T6_COLUMNS].sum(axis=1)
    df["KH_MBNT_2026_CN"] = df["KHKD KDNT 2026 (triệu đồng)"]
    df["KH_MBNT_T2_CN"] = df["KHKD KDNT T2.2026"]
    df["KH_PSTC_2026_CN"] = df["KHKD PSTC 2026"]
    df["KH_PSTC_T2_CN"] = df["KHKD PSTC T2.2026"]

    df["LN_HDLS_LuyKe_update"] = df["sum_ln_hdls_luy_ke"] / 1_000_000
    df["LN_KDNTPS_LuyKe_CN"] = df["sum_ln_kdntps_luy_ke"] / 1_000_000
    df["LN_MBNT_LuyKe_update"] = df["sum_ln_mbnt_luy_ke_den_ngay_bc"] / 1_000_000
    df["LN_PSHH_LuyKe_CN"] = df["sum_ln_pshh_luy_ke"] / 1_000_000
    df["LN_TDPS_LuyKe_update"] = df["sum_ln_tdps_luy_ke"] / 1_000_000
    df["LN_PSTC"] = df["LN_HDLS_LuyKe_update"].fillna(0.0) + df["LN_TDPS_LuyKe_update"].fillna(0.0)

    df["PctHoanThanh_Nam_KDNTPS"] = _dax_divide(df["LN_KDNTPS_LuyKe_CN"], df["KH_KDNTPS_2026_CN"])
    df["PctHoanThanh_Nam_MBNT"] = _dax_divide(df["LN_MBNT_LuyKe_update"], df["KH_MBNT_2026_CN"])
    df["PctHoanThanh_Nam_PSTC"] = _dax_divide(df["LN_PSTC"], df["KH_PSTC_2026_CN"])
    df["PctHoanThanh_Thang_KDNTPS"] = _dax_divide(df["LN_KDNTPS_LuyKe_CN"], df["KH_KDNTPS_T6_CN"])
    df["PctHoanThanh_Thang_MBNT"] = _dax_divide(df["LN_MBNT_LuyKe_update"], df["KH_MBNT_T2_CN"])
    df["PctHoanThanh_Thang_PSTC"] = _dax_divide(df["LN_PSTC"], df["KH_PSTC_T2_CN"])

    # RANKX(ALLSELECTED(...), ..., DESC, DENSE) — ranked within the current Nhóm phụ trách
    # filter context (highest % gets rank 1); DAX default ranks blanks last, pandas leaves
    # NaN as NaN (branches with no plan/no data are simply unranked here). Ranked by % năm so
    # STT stays sequential with the table's own % năm sort order, not a separate ordering.
    df["STT_PctNam_KDNTPS_CN"] = df.groupby("Nhóm phụ trách")["PctHoanThanh_Nam_KDNTPS"].rank(method="dense", ascending=False)
    df["STT_PctNam_MBNT"] = df.groupby("Nhóm phụ trách")["PctHoanThanh_Nam_MBNT"].rank(method="dense", ascending=False)
    df["STT_PctNam_PSTC"] = df.groupby("Nhóm phụ trách")["PctHoanThanh_Nam_PSTC"].rank(method="dense", ascending=False)

    return df.reset_index()


@_df_cache()
def _measure(column: str):
    def fn(selected_date: str) -> pd.Series:
        return _scorecard(selected_date).set_index("Chi nhánh")[column]
    fn.__name__ = column
    return fn


KH_KDNTPS_2026_CN = _measure("KH_KDNTPS_2026_CN")
KH_KDNTPS_T6_CN = _measure("KH_KDNTPS_T6_CN")
KH_MBNT_2026_CN = _measure("KH_MBNT_2026_CN")
KH_MBNT_T2_CN = _measure("KH_MBNT_T2_CN")
KH_PSTC_2026_CN = _measure("KH_PSTC_2026_CN")
KH_PSTC_T2_CN = _measure("KH_PSTC_T2_CN")

LN_HDLS_LuyKe_update = _measure("LN_HDLS_LuyKe_update")
LN_KDNTPS_LuyKe_CN = _measure("LN_KDNTPS_LuyKe_CN")
LN_MBNT_LuyKe_update = _measure("LN_MBNT_LuyKe_update")
LN_PSHH_LuyKe_CN = _measure("LN_PSHH_LuyKe_CN")
LN_PSTC = _measure("LN_PSTC")
LN_TDPS_LuyKe_update = _measure("LN_TDPS_LuyKe_update")

PctHoanThanh_Nam_KDNTPS = _measure("PctHoanThanh_Nam_KDNTPS")
PctHoanThanh_Nam_MBNT = _measure("PctHoanThanh_Nam_MBNT")
PctHoanThanh_Nam_PSTC = _measure("PctHoanThanh_Nam_PSTC")
PctHoanThanh_Thang_KDNTPS = _measure("PctHoanThanh_Thang_KDNTPS")
PctHoanThanh_Thang_MBNT = _measure("PctHoanThanh_Thang_MBNT")
PctHoanThanh_Thang_PSTC = _measure("PctHoanThanh_Thang_PSTC")

STT_PctNam_KDNTPS_CN = _measure("STT_PctNam_KDNTPS_CN")
STT_PctNam_MBNT = _measure("STT_PctNam_MBNT")
STT_PctNam_PSTC = _measure("STT_PctNam_PSTC")


DISPLAY_COLUMNS = {
    "STT_PctNam_KDNTPS_CN": "STT",
    "Chi nhánh": "Chi nhánh",
    "Cán bộ phụ trách": "Cán bộ phụ trách",
    "KH_KDNTPS_2026_CN": "KH KDNTPS 2026 (tr đồng)",
    "LN_MBNT_LuyKe_update": "KQ MBNT (tr đồng)",
    "LN_HDLS_LuyKe_update": "KQ HDLS (tr đồng)",
    "LN_TDPS_LuyKe_update": "KQ TDPS (tr đồng)",
    "LN_PSHH_LuyKe_CN": "KQ PSHH (tr đồng)",
    "LN_KDNTPS_LuyKe_CN": "KQ KDNT&PS (tr đồng)",
    "PctHoanThanh_Thang_KDNTPS": "% tháng",
    "PctHoanThanh_Nam_KDNTPS": "% năm",
}


@_df_cache()
def branch_table(selected_date: str) -> pd.DataFrame:
    """Scorecard columns renamed to their Power BI display headers, plus Nhóm phụ trách for grouping."""
    df = _scorecard(selected_date)[["Nhóm phụ trách"] + list(DISPLAY_COLUMNS.keys())]
    return df.rename(columns=DISPLAY_COLUMNS)


if __name__ == "__main__":
    from date_table import latest_date

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    d = latest_date()
    print(f"selected_date: {d}\n")
    print(_scorecard(d)[[
        "Chi nhánh", "KH_KDNTPS_2026_CN", "LN_KDNTPS_LuyKe_CN",
        "PctHoanThanh_Nam_KDNTPS", "STT_PctNam_KDNTPS_CN",
    ]].sort_values("STT_PctNam_KDNTPS_CN").to_string())
