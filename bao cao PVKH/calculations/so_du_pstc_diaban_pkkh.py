"""Số dư TDPS / CCS / IRS by dia_ban or pkkh, sourced directly from the pre-aggregated
bronze_baocaotudong.pvkh_pstc_dia_ban / pvkh_pstc_pkkh tables instead of exploding
pvkh_dailyreport's customer-level rows (see calculations/tdps_diaban_pkkh.py and
so_du_hdls_diaban_pkkh.py for that customer-level path).

pvkh_pstc_dia_ban/pkkh carry no nhóm phụ trách dimension at all (db_connect.py's
pvkh_dailyreport docstring: "every other so_du_tdps_* column in the warehouse sits on a
pre-aggregated table (pvkh_pstc_dia_ban, _pkkh, _nhom_phu_trach) that holds one dimension
each and so cannot be crossed with nhóm") — so this module is usable ONLY where a chart pools
every nhóm together, i.e. Tổng quan (pool_nhom=True). Nhóm phụ trách's own Số dư charts still
need the customer-level pvkh_dailyreport path, since they show one bar per (nhóm, dim) and
these tables have no way to supply the nhóm half of that.

Every function here returns a 3-column frame — nhom_phu_trach (a constant placeholder, never
a real nhóm), dim_out, value_out — matching the shape _build_daily_dim_chart already expects,
so it plugs into the same chart builder used everywhere else."""

import pandas as pd
from data_connect.db_connect import _df_cache, pvkh_pstc_dia_ban, pvkh_pstc_pkkh

# Exact-match cleanup for pvkh_pstc_dia_ban's dia_ban — this table mixes several spellings for
# the same địa bàn across its history (accented short codes, unaccented full names, and one
# "DLPB - Ngoai HN" variant that needs folding into ĐLPB rather than partially replaced), so a
# substring-replace list (like y_ln_mbnt_nhom_diaban_pkkh._DIA_BAN_REPLACEMENTS) isn't safe
# here — every raw value observed in the table is mapped explicitly instead.
DIA_BAN_MAP = {
    "Ha Noi": "HN", "HN": "HN",
    "Tay Nguyen": "TN", "TN": "TN",
    "Mien nui phia Bac": "MNPB", "MNPB": "MNPB",
    "Nam Trung Bo": "NTB", "NTB": "NTB",
    "DLPB": "ĐLPB", "DLPB - Ngoai HN": "ĐLPB", "ĐLPB": "ĐLPB",
    "DBSH": "ĐBSH", "ĐBSH": "ĐBSH",
    "DLPN": "ĐLPN", "ĐLPN": "ĐLPN",
    "DBSCL": "ĐBSCL", "ĐBSCL": "ĐBSCL",
    "BTB": "BTB",
    "TP HCM": "TP HCM",
}
# Junk/aggregate buckets to drop outright, for both dia_ban and pkkh.
_JUNK_VALUES = {"0", "Chưa phân bổ", "TOTAL"}


def _clean_dia_ban(df: pd.DataFrame) -> pd.DataFrame:
    df = df[~df["dia_ban"].isin(_JUNK_VALUES)].copy()
    df["dia_ban"] = df["dia_ban"].map(DIA_BAN_MAP).fillna(df["dia_ban"])
    return df


def _clean_pkkh(df: pd.DataFrame) -> pd.DataFrame:
    df = df[~df["pkkh"].isin(_JUNK_VALUES)].copy()
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    return df


def _shape(df: pd.DataFrame, dim_col: str, value_col: str, dim_out: str, value_out: str) -> pd.DataFrame:
    result = df.groupby(dim_col, as_index=False)[value_col].sum()
    result.columns = [dim_out, value_out]
    result.insert(0, "nhom_phu_trach", "")  # placeholder — see module docstring
    return result


@_df_cache()
def so_du_tdps_pstc_by_diaban(date_str: str) -> pd.DataFrame:
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    return _shape(df, "dia_ban", "so_du_tdps_binh_quan", "dia_ban", "so_du")


@_df_cache()
def so_du_tdps_pstc_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    return _shape(df, "pkkh", "so_du_tdps_binh_quan", "pkkh", "so_du")


@_df_cache()
def so_du_ccs_pstc_by_diaban(date_str: str) -> pd.DataFrame:
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    return _shape(df, "dia_ban", "so_du_ccs_binh_quan", "dia_ban", "so_du")


@_df_cache()
def so_du_ccs_pstc_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    return _shape(df, "pkkh", "so_du_ccs_binh_quan", "pkkh", "so_du")


@_df_cache()
def so_du_irs_pstc_by_diaban(date_str: str) -> pd.DataFrame:
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    return _shape(df, "dia_ban", "so_du_irs_binh_quan", "dia_ban", "so_du")


@_df_cache()
def so_du_irs_pstc_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    return _shape(df, "pkkh", "so_du_irs_binh_quan", "pkkh", "so_du")


@_df_cache()
def so_du_hdls_pstc_by_diaban(date_str: str) -> pd.DataFrame:
    """Combined CCS+IRS số dư HĐLS by dia_ban — summed from the two sub-product columns rather
    than the table's own so_du_hdls_binh_quan, matching the sum-not-trust-combined-column
    convention already used at nhóm level (so_du_hdls_ngay_by_nhom.py)."""
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    df = df.copy()
    df["so_du"] = df["so_du_ccs_binh_quan"].fillna(0.0) + df["so_du_irs_binh_quan"].fillna(0.0)
    result = df.groupby("dia_ban", as_index=False)["so_du"].sum()
    result.insert(0, "nhom_phu_trach", "")
    return result


@_df_cache()
def so_du_hdls_pstc_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    df = df.copy()
    df["so_du"] = df["so_du_ccs_binh_quan"].fillna(0.0) + df["so_du_irs_binh_quan"].fillna(0.0)
    result = df.groupby("pkkh", as_index=False)["so_du"].sum()
    result.insert(0, "nhom_phu_trach", "")
    return result


@_df_cache()
def so_du_hdls_stack_pstc_by_diaban(date_str: str) -> pd.DataFrame:
    """Same source as so_du_hdls_pstc_by_diaban, but keeping IRS and CCS as separate columns
    instead of summing them — feeds Tổng quan's stacked Số dư HĐLS chart (one bar split into an
    IRS segment and a CCS segment) instead of one flat total."""
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    result = df.groupby("dia_ban", as_index=False)[["so_du_irs_binh_quan", "so_du_ccs_binh_quan"]].sum()
    result.insert(0, "nhom_phu_trach", "")
    return result


@_df_cache()
def so_du_hdls_stack_pstc_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    result = df.groupby("pkkh", as_index=False)[["so_du_irs_binh_quan", "so_du_ccs_binh_quan"]].sum()
    result.insert(0, "nhom_phu_trach", "")
    return result


# ---------------------------------------------------------------- ngày (single-day snapshot)
# Same tables, the sum_so_du_*_ngay_bc columns instead of the *_binh_quan (YTD average) ones —
# confirmed present on pvkh_pstc_dia_ban/pkkh by direct query (same column family as
# pvkh_pstc_nhom_phu_trach, which so_du_hdls_ngay_by_nhom.py / tdps_ngay_by_nhom.py already read
# at nhóm level). Feeds Tổng quan's Trong ngày dia_ban/PKKH Số dư charts and contribution donuts.

@_df_cache()
def so_du_tdps_pstc_ngay_by_diaban(date_str: str) -> pd.DataFrame:
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    return _shape(df, "dia_ban", "sum_so_du_tdps_ngay_bc", "dia_ban", "so_du")


@_df_cache()
def so_du_tdps_pstc_ngay_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    return _shape(df, "pkkh", "sum_so_du_tdps_ngay_bc", "pkkh", "so_du")


@_df_cache()
def so_du_ccs_pstc_ngay_by_diaban(date_str: str) -> pd.DataFrame:
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    return _shape(df, "dia_ban", "sum_so_du_ccs_ngay_bc", "dia_ban", "so_du")


@_df_cache()
def so_du_ccs_pstc_ngay_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    return _shape(df, "pkkh", "sum_so_du_ccs_ngay_bc", "pkkh", "so_du")


@_df_cache()
def so_du_irs_pstc_ngay_by_diaban(date_str: str) -> pd.DataFrame:
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    return _shape(df, "dia_ban", "sum_so_du_irs_ngay_bc", "dia_ban", "so_du")


@_df_cache()
def so_du_irs_pstc_ngay_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    return _shape(df, "pkkh", "sum_so_du_irs_ngay_bc", "pkkh", "so_du")


@_df_cache()
def so_du_hdls_pstc_ngay_by_diaban(date_str: str) -> pd.DataFrame:
    """Combined CCS+IRS số dư HĐLS ngày by dia_ban — summed from the two sub-product columns,
    same sum-not-trust-combined-column convention as the bình quân variant above."""
    df = _clean_dia_ban(pvkh_pstc_dia_ban(date_str))
    df = df.copy()
    df["so_du"] = df["sum_so_du_ccs_ngay_bc"].fillna(0.0) + df["sum_so_du_irs_ngay_bc"].fillna(0.0)
    result = df.groupby("dia_ban", as_index=False)["so_du"].sum()
    result.insert(0, "nhom_phu_trach", "")
    return result


@_df_cache()
def so_du_hdls_pstc_ngay_by_pkkh(date_str: str) -> pd.DataFrame:
    df = _clean_pkkh(pvkh_pstc_pkkh(date_str))
    df = df.copy()
    df["so_du"] = df["sum_so_du_ccs_ngay_bc"].fillna(0.0) + df["sum_so_du_irs_ngay_bc"].fillna(0.0)
    result = df.groupby("pkkh", as_index=False)["so_du"].sum()
    result.insert(0, "nhom_phu_trach", "")
    return result


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("So du TDPS by dia_ban:\n", so_du_tdps_pstc_by_diaban(d).to_string())
    print("So du TDPS by pkkh:\n", so_du_tdps_pstc_by_pkkh(d).to_string())
    print("So du HDLS (CCS+IRS) by dia_ban:\n", so_du_hdls_pstc_by_diaban(d).to_string())
    print("So du HDLS (CCS+IRS) by pkkh:\n", so_du_hdls_pstc_by_pkkh(d).to_string())
