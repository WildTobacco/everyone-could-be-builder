"""DS / LN TDPS by (nhóm phụ trách, địa bàn | PKKH) — the dimension-level measures behind the
TDPS địa bàn and PKKH charts, mirroring the HĐLS pair in y_/y1_ds_hdls_ and y_/y1_ln_hdls_.

Each year comes from a different table, because pvkh_pstc is only reliable for 2025:

  2026  DS  pvkh_dsdaily_temp[doanhsotdps]        — daily, non-accumulative; summed 1/1 → date
        LN  silver[ln_tdps_luy_ke_den_ngay_bc]    — YTD cumulative, deduped per bdscif via MAX
  2025  DS  pvkh_pstc[doanhso]  sanpham='TDPS'    | Full + Partial × ProrationRatio, the usual
        LN  pvkh_pstc[loinhuan] sanpham='TDPS'    | monthly-to-part-month approximation

pvkh_pstc is not used for 2026 on either measure: its TDPS doanh số is 591.5M against the
real 2,180.4M, and its TDPS lợi nhuận 46.6bn against 240.8bn.

The silver LN rollup reconciles to pvkh_pstc_nhom_phu_trach[sum_ln_tdps_luy_ke] exactly for
PTKD 1, PTKD 2 and TOTAL; VPV differs by 1.67M (0.003%), a reallocation between nhóm that
nets to zero overall.

Dimensions: LN (sourced from silver_pvkh_DL_KH_luy_ke) uses that table's own native
nhom_phu_trach/dia_ban/pkkh columns directly — no join. DS (sourced from pvkh_dsdaily_temp,
which carries no native dimension columns at all) still needs listbds() via bds for nhóm/địa
bàn and pvkh_listcif → pvkh_pkkh via cif for PKKH, with KHCN*/ME normalised either way.
"""

import calendar

import pandas as pd

from data_connect.db_connect import _df_cache

from data_connect.db_connect import (
    pvkh_dsdaily_temp, silver_pvkh_dl_kh_luy_ke, pvkh_pstc, pkkh_lookup, pvkh_dailyreport,
)
from calculations.date_table import same_day_last_year, latest_date
from calculations.y_ln_mbnt_nhom_diaban_pkkh import _DIA_BAN_REPLACEMENTS


def _attach_pkkh(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    lookup = pkkh_lookup(date_str)
    df = df.copy()
    df["cif"] = pd.to_numeric(df["cif"], errors="coerce").astype("Int64")
    lookup["cif"] = pd.to_numeric(lookup["cif"], errors="coerce").astype("Int64")
    df = df.merge(lookup, on="cif", how="left")
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    return df


def _shape(df: pd.DataFrame, dim_src: str, value_src: str, dim_out: str, value_out: str) -> pd.DataFrame:
    result = df.groupby(["nhomphutrach", dim_src])[value_src].sum().reset_index()
    result.columns = ["nhom_phu_trach", dim_out, value_out]
    return result


# ---------------------------------------------------------------- 2026 doanh số

@_df_cache()
def _y_ds_tdps(date_str: str) -> pd.DataFrame:
    """Non-accumulative rows accumulated from 1 January of date_str's year through date_str."""
    start = pd.to_datetime(date_str).replace(month=1, day=1).strftime("%Y-%m-%d")
    return _attach_pkkh(pvkh_dsdaily_temp(start, date_str), date_str)


@_df_cache()
def y_ds_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _shape(_y_ds_tdps(date_str), "diaban", "doanhsotdps", "dia_ban", "doanh_so")


@_df_cache()
def y_ds_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _shape(_y_ds_tdps(date_str), "pkkh", "doanhsotdps", "pkkh", "doanh_so")


@_df_cache()
def _ngay_ds_tdps(date_str: str) -> pd.DataFrame:
    """That date's rows only. Unlike every other Trong ngày measure this needs no differencing —
    pvkh_dsdaily_temp is already one row per (bds, cif, day), not a running cumulative."""
    return _attach_pkkh(pvkh_dsdaily_temp(date_str, date_str), date_str)


@_df_cache()
def ds_tdps_ngay_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _shape(_ngay_ds_tdps(date_str), "diaban", "doanhsotdps", "dia_ban", "doanh_so")


@_df_cache()
def ds_tdps_ngay_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _shape(_ngay_ds_tdps(date_str), "pkkh", "doanhsotdps", "pkkh", "doanh_so")


# ---------------------------------------------------------------- 2026 lợi nhuận

@_df_cache()
def _y_ln_tdps(date_str: str) -> pd.DataFrame:
    """SUMX(VALUES[bdscif], CALCULATE(MAX(...))) — dedupe per bdscif via MAX, the same shape as
    y_ln_hdls_nhom_diaban_pkkh. No chia sẻ deduction (that is MBNT-only) and no bdscif
    exclusion, matching the HĐLS LN measure.

    nhom_phu_trach/dia_ban/pkkh are all native columns on silver_pvkh_DL_KH_luy_ke — no
    listbds()/pkkh_lookup() join, per user request ("if it is from silver_pvkh_DL_KH_luy_ke then
    take the native columns"), same source of truth y_ln_mbnt_nhom_diaban_pkkh.py /
    y_nim_mbnt_nhom_diaban_pkkh.py already use. This used to derive nhom_phu_trach/dia_ban via a
    bds -> listbds() join (pkkh had already been switched to native in an earlier pass, but not
    these two) — see y_ds_mbnt_nhom_diaban_pkkh.py's docstring for the reconciliation that
    surfaced this same bug on DS_MBNT's FDI total. DS TDPS above still needs the
    listbds()/pkkh_lookup() join — it's sourced from pvkh_dsdaily_temp, a table with no native
    dia_ban/pkkh/nhom_phu_trach columns at all."""
    df = silver_pvkh_dl_kh_luy_ke(date_str).copy()
    for old, new in _DIA_BAN_REPLACEMENTS:
        df["dia_ban"] = df["dia_ban"].str.replace(old, new, regex=False)
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"

    return df.groupby("bdscif").agg(
        ln=("ln_tdps_luy_ke_den_ngay_bc", "max"),
        nhom_phu_trach=("nhom_phu_trach", "first"),
        dia_ban=("dia_ban", "first"),
        pkkh=("pkkh", "first"),
    ).reset_index()


@_df_cache()
def y_ln_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    result = _y_ln_tdps(date_str).groupby(["nhom_phu_trach", "dia_ban"])["ln"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "loi_nhuan"]
    return result


@_df_cache()
def y_ln_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    result = _y_ln_tdps(date_str).groupby(["nhom_phu_trach", "pkkh"])["ln"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "loi_nhuan"]
    return result


# ---------------------------------------------------------------- 2025 baselines

# ---------------------------------------------------------------- số dư (2026 only)

@_df_cache()
def _so_du_tdps(date_str: str) -> pd.DataFrame:
    """Số dư TDPS on the report day, from pvkh_dailyreport — the only customer-level source.
    Rolls up to pvkh_pstc_nhom_phu_trach[sum_so_du_tdps_ngay_bc] exactly (verified 11/08/2026,
    all three nhóm and TOTAL, zero difference).

    Its dia_ban/pkkh are raw like silver's, so they get the same cleanup. Both columns also
    carry a junk "0" bucket, dropped per-dimension rather than up front: on 11/08/2026 seven
    rows have a real địa bàn but pkkh = "0" (775,698.32), so filtering both at once would strip
    them from the địa bàn chart too. Rows with no nhóm at all ("0") are dropped outright —
    they would otherwise render as a fourth nhóm group."""
    df = pvkh_dailyreport(date_str).copy()
    for old, new in _DIA_BAN_REPLACEMENTS:
        df["dia_ban"] = df["dia_ban"].str.replace(old, new, regex=False)
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    df = df.rename(columns={"nhom_phu_trach": "nhomphutrach", "dia_ban": "diaban"})
    return df[df["nhomphutrach"] != "0"]


@_df_cache()
def so_du_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    df = _so_du_tdps(date_str)
    return _shape(df[df["diaban"] != "0"], "diaban", "so_du_tdps_ngay_bc", "dia_ban", "so_du")


@_df_cache()
def so_du_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    df = _so_du_tdps(date_str)
    return _shape(df[df["pkkh"] != "0"], "pkkh", "so_du_tdps_ngay_bc", "pkkh", "so_du")


@_df_cache()
def so_du_tdps_luy_ke_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    """Lũy kế counterpart to so_du_tdps_by_nhom_diaban: so_du_tdps_bq_nam (average balance
    year-to-date through date_str) instead of that single day's own snapshot. Same
    pvkh_dailyreport row set, just a different column — balance has no "sum since Jan 1" that
    would mean anything, so "lũy kế" here is the average, matching the nhóm-level
    so_du_tdps_binh_quan already used elsewhere (e.g. pvkh_pstc_nhom_phu_trach)."""
    df = _so_du_tdps(date_str)
    return _shape(df[df["diaban"] != "0"], "diaban", "so_du_tdps_bq_nam", "dia_ban", "so_du")


@_df_cache()
def so_du_tdps_luy_ke_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    df = _so_du_tdps(date_str)
    return _shape(df[df["pkkh"] != "0"], "pkkh", "so_du_tdps_bq_nam", "pkkh", "so_du")


@_df_cache()
def _y1_tdps(date_str: str, value_col: str) -> pd.DataFrame:
    """Full + Partial × ProrationRatio over pvkh_pstc, sanpham = 'TDPS'. date_str is the Y-1
    date. Returns the prorated value per (nhomphutrach, diaban, pkkh) row group."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_pstc(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df = df[df["sanpham"] == "TDPS"].copy()
    df["_v"] = df[value_col] * df["monthyear"].eq(ref_month).map({True: proration_ratio, False: 1.0})
    return df[df["monthyear"] <= ref_month]


@_df_cache()
def y1_ds_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _shape(_y1_tdps(date_str, "doanhso"), "diaban", "_v", "dia_ban", "doanh_so")


@_df_cache()
def y1_ds_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _shape(_y1_tdps(date_str, "doanhso"), "pkkh", "_v", "pkkh", "doanh_so")


@_df_cache()
def y1_ln_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _shape(_y1_tdps(date_str, "loinhuan"), "diaban", "_v", "dia_ban", "loi_nhuan")


@_df_cache()
def y1_ln_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _shape(_y1_tdps(date_str, "loinhuan"), "pkkh", "_v", "pkkh", "loi_nhuan")


if __name__ == "__main__":
    d = latest_date()
    d25 = same_day_last_year(d)
    print(f"date: {d}  (Y-1: {d25})\n")
    for name, fn, arg in [
        ("DS 2026 / dia_ban", y_ds_tdps_by_nhom_diaban, d),
        ("LN 2026 / dia_ban", y_ln_tdps_by_nhom_diaban, d),
        ("DS 2025 / dia_ban", y1_ds_tdps_by_nhom_diaban, d25),
        ("LN 2025 / pkkh", y1_ln_tdps_by_nhom_pkkh, d25),
    ]:
        r = fn(arg)
        print(f"--- {name}: {len(r)} rows, total {r.iloc[:, 2].sum():,.2f}")
        print(r.to_string(index=False, float_format=lambda x: f"{x:,.2f}"), "\n")
