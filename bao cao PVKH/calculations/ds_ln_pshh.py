"""Doanh số & Lợi nhuận PSHH (phái sinh hàng hóa = TLHH + OTC).

Doanh số is kept split by sản phẩm con (TLHH, OTC) rather than combined into one figure —
doanhsotlhh (pvkh_dsdaily_temp) is denominated in lots, not currency, so summing it together
with doanhsootc (already USD, same convention as every other product's Doanh số in this
dashboard) would mix incompatible units. Lợi nhuận has no such split; it's always one VND
figure regardless of which PSHH sub-product it came from.

Two different sources depending on year, same split as ds_tdps.py uses for TDPS:

  2026  DS TLHH  pvkh_dsdaily_temp[doanhsotlhh]         — lots, daily/non-accumulative rows;
        DS OTC   pvkh_dsdaily_temp[doanhsootc]          — USD, same shape
                                                            both summed 1/1 → date_str
        LN       pvkh_dailyreport[ln_pshh_theo_mpa_ytd]  — that day's own YTD-cumulative
                                                            snapshot, already accumulated in
                                                            the source (no ln_pshh_luy_ke_den_
                                                            ngay_bc column exists for PSHH the
                                                            way TDPS/MBNT/HĐLS have — this "mpa
                                                            ytd" column is PSHH's equivalent)
  2025  DS TLHH  pvkh_pshh[doanhso] sanpham='TLHH'       | Full + Partial × ProrationRatio,
        DS OTC   pvkh_pshh[doanhso] sanpham='OTC'        | the usual monthly-to-part-month
        LN       pvkh_pshh[loinhuan] sanpham in (TLHH,OTC)| approximation

pvkh_pshh is a 2025-only source in practice — it is monthly and only loaded through mid-2026,
so it is used for the Y-1 baseline only, exactly like pvkh_pstc is for TDPS (see ds_tdps.py's
module docstring for the same reasoning applied to a sibling product).

TOTAL only (no nhóm/dia_ban/pkkh breakdown) — that's all Tổng quan's scorecard needs."""

import calendar

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_pshh, pvkh_dailyreport, pvkh_dsdaily_temp


@_df_cache()
def _year_start(date_str: str) -> str:
    return pd.to_datetime(date_str).replace(month=1, day=1).strftime("%Y-%m-%d")


@_df_cache()
def ds_pshh_tlhh_luy_ke(date_str: str) -> float:
    """2026 Doanh số TLHH, in lots — accumulated from the start of date_str's year through
    date_str inclusive. Intended for 2026 dates only — see the module docstring for why 2025
    takes a different route."""
    df = pvkh_dsdaily_temp(_year_start(date_str), date_str)
    return float(df["doanhsotlhh"].sum())


@_df_cache()
def ds_pshh_otc_luy_ke(date_str: str) -> float:
    """2026 Doanh số OTC, in USD — same shape as ds_pshh_tlhh_luy_ke."""
    df = pvkh_dsdaily_temp(_year_start(date_str), date_str)
    return float(df["doanhsootc"].sum())


@_df_cache()
def ln_pshh_luy_ke(date_str: str) -> float:
    """2026 Lợi nhuận: pvkh_dailyreport is already one row per bdscif for a given ngay, and
    ln_pshh_theo_mpa_ytd is already that row's YTD-cumulative figure — no dedup or date-range
    summing needed, just sum the single day's rows."""
    df = pvkh_dailyreport(date_str)
    return float(df["ln_pshh_theo_mpa_ytd"].sum())


# Trong ngày PSHH (DS TLHH/OTC + LN, single day) lives in daily_pshh_nhom_diaban_pkkh.py instead
# of here — pvkh_dailyreport carries genuine raw _ngay_bc columns for all three
# (ds_tlhh_ngay_bc/ds_otc_ngay_bc/ln_pshh_ngay_bc), so no differencing approximation is needed
# the way it briefly was attempted here.


@_df_cache()
def _y1_pshh(date_str: str, value_col: str, sanpham: str | None = None) -> float:
    """Y-1 baseline: Full + Partial × ProrationRatio over pvkh_pshh, optionally filtered to one
    sub-product (sanpham='TLHH'/'OTC'; None sums both, used for Lợi nhuận). date_str is already
    the Y-1 date."""
    ref_date = pd.to_datetime(date_str)
    ref_month = ref_date.replace(day=1)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    proration_ratio = ref_date.day / days_in_month

    df = pvkh_pshh(date_str)
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    if sanpham is not None:
        df = df[df["sanpham"] == sanpham]

    full = df.loc[df["monthyear"] < ref_month, value_col].sum()
    partial = df.loc[df["monthyear"] == ref_month, value_col].sum() * proration_ratio
    return float(full + partial)


def y1_ds_pshh_tlhh(date_str: str) -> float:
    return _y1_pshh(date_str, "doanhso", sanpham="TLHH")


def y1_ds_pshh_otc(date_str: str) -> float:
    return _y1_pshh(date_str, "doanhso", sanpham="OTC")


def y1_ln_pshh(date_str: str) -> float:
    return _y1_pshh(date_str, "loinhuan")


if __name__ == "__main__":
    from calculations.date_table import latest_date, same_day_last_year

    d = latest_date()
    d25 = same_day_last_year(d)
    print(f"date: {d}   (Y-1: {d25})")
    print(f"DS PSHH TLHH lũy kế 2026 (lots): {ds_pshh_tlhh_luy_ke(d):,.2f}")
    print(f"DS PSHH OTC lũy kế 2026 (USD): {ds_pshh_otc_luy_ke(d):,.2f}")
    print(f"LN PSHH lũy kế 2026: {ln_pshh_luy_ke(d):,.2f}")
    print(f"DS PSHH TLHH Y-1 (lots, prorated): {y1_ds_pshh_tlhh(d25):,.2f}")
    print(f"DS PSHH OTC Y-1 (USD, prorated): {y1_ds_pshh_otc(d25):,.2f}")
    print(f"LN PSHH Y-1 (prorated): {y1_ln_pshh(d25):,.2f}")
