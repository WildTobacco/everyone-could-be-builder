"""Daily (non-accumulative) DS / LN / NIM by (nhóm phụ trách, địa bàn | PKKH) for MBNT and HĐLS.

Unlike the nhóm-level cards, which read a pre-computed *_ngay_bc column straight from
pvkh_*_nhom_phu_trach, there is no daily column broken down by địa bàn/PKKH anywhere in the
source. So a day's own figure is derived the way the request specified:

    daily(d) = cumulative(d) - cumulative(previous report day)

previous_date() walks the date table rather than subtracting one calendar day, so Mondays
difference against Friday and post-holiday days against the last actual trading day.

Only the 2026 series is differenced — these charts are single-series, not the 2025-vs-2026
clustered pairs the lũy kế charts use. The y1_* (2025) measures are a Full + Partial ×
ProrationRatio approximation built off *monthly* rows, so differencing one day-over-day
collapses to month_total / days_in_month: a flat synthetic rate, not a real day's trading.
There is nothing meaningful to compare a real daily figure against on the 2025 side.

NIM is a ratio, so it is recomputed from the differenced components (daily LN / daily DS)
rather than differenced itself. Its DS is sourced from y_nim_mbnt_nhom_diaban_pkkh's own
helper, not the y_ds_ module, because the NIM chart groups by silver's native cleaned
dia_ban while the DS/LN charts group by listbds()'s — mixing them would misalign the columns.

**MBNT lợi nhuận trong ngày is gross of chia sẻ** — it differences
silver_pvkh_DL_KH_luy_ke[ln_mbnt_luy_ke_den_ngay_bc] directly, where the lũy kế measure
differences nothing and reports LN *sau* chia sẻ. This is deliberate, per the user.

The reason: chia sẻ is a monthly figure. _y_ln_sau_chiase holds its window fixed within a
month then advances it on the last calendar day, so differencing the sau-chia-sẻ cumulative
cancels the term on ordinary days but dumps a whole month of it into month end — on
31/07/2026 that left PTKD 2 / HN reporting 1.07bn against ~4.82bn of actual trading, the
3.75bn gap being July's chia sẻ. Excluding it entirely makes every day a clean measure of
that day's trading.

The trade-off to know: daily LN no longer telescopes back to the lũy kế sau-chia-sẻ figure
over a month — the daily series sums to LN *trước* chia sẻ. HĐLS LN has no chia sẻ term at
all, and doanh số never did, so both are unaffected either way.
"""

import pandas as pd

from data_connect.db_connect import _df_cache

from data_connect.db_connect import silver_pvkh_dl_kh_luy_ke
from calculations.date_table import previous_date
from calculations.y_ds_mbnt_nhom_diaban_pkkh import (
    y_ds_mbnt_by_nhom_diaban, y_ds_mbnt_by_nhom_pkkh,
)
from calculations.y_ds_hdls_nhom_diaban_pkkh import (
    y_ds_hdls_by_nhom_diaban, y_ds_hdls_by_nhom_pkkh,
    y_ds_hdls_irs_ccs_by_nhom_diaban, y_ds_hdls_irs_ccs_by_nhom_pkkh,
)
from calculations.y_ln_hdls_nhom_diaban_pkkh import (
    y_ln_hdls_by_nhom_diaban, y_ln_hdls_by_nhom_pkkh,
)
from calculations.y_ln_mbnt_nhom_diaban_pkkh import _clean_dia_ban
from calculations.y_nim_mbnt_nhom_diaban_pkkh import _y_doanhso
from calculations.tdps_diaban_pkkh import (
    ds_tdps_ngay_by_nhom_diaban, ds_tdps_ngay_by_nhom_pkkh,
    y_ln_tdps_by_nhom_diaban, y_ln_tdps_by_nhom_pkkh,
)


def _diff(fetch, date_str: str, dim_col: str, value_col: str) -> pd.DataFrame:
    """cumulative(date_str) - cumulative(previous report day), aligned on (nhóm, dim).

    An outer join + fillna(0) is deliberate: a địa bàn/PKKH present today but absent yesterday
    had no prior cumulative, so its whole figure is today's movement."""
    today = fetch(date_str)
    prev = previous_date(date_str)
    if prev is None:  # earliest date on record — nothing to difference against
        return today[["nhom_phu_trach", dim_col, value_col]].copy()

    yesterday = fetch(prev)
    merged = pd.merge(
        today, yesterday, on=["nhom_phu_trach", dim_col], how="outer", suffixes=("_t", "_y")
    ).fillna(0.0)
    merged[value_col] = merged[f"{value_col}_t"] - merged[f"{value_col}_y"]
    return merged[["nhom_phu_trach", dim_col, value_col]]


def _diff_stacked(fetch, date_str: str, dim_col: str, seg_cols: list) -> pd.DataFrame:
    """Same cumulative(date_str) - cumulative(previous report day) differencing as _diff, but
    for multiple segment columns at once (e.g. irs + ccs) instead of a single value_col."""
    today = fetch(date_str)
    prev = previous_date(date_str)
    if prev is None:
        return today[["nhom_phu_trach", dim_col] + seg_cols].copy()

    yesterday = fetch(prev)
    merged = pd.merge(
        today, yesterday, on=["nhom_phu_trach", dim_col], how="outer", suffixes=("_t", "_y")
    ).fillna(0.0)
    for col in seg_cols:
        merged[col] = merged[f"{col}_t"] - merged[f"{col}_y"]
    return merged[["nhom_phu_trach", dim_col] + seg_cols]


@_df_cache()
def daily_ds_hdls_irs_ccs_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _diff_stacked(y_ds_hdls_irs_ccs_by_nhom_diaban, date_str, "dia_ban", ["irs", "ccs"])


@_df_cache()
def daily_ds_hdls_irs_ccs_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _diff_stacked(y_ds_hdls_irs_ccs_by_nhom_pkkh, date_str, "pkkh", ["irs", "ccs"])


@_df_cache()
def daily_ds_mbnt_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _diff(y_ds_mbnt_by_nhom_diaban, date_str, "dia_ban", "doanh_so")


@_df_cache()
def daily_ds_mbnt_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _diff(y_ds_mbnt_by_nhom_pkkh, date_str, "pkkh", "doanh_so")


def _ln_mbnt_truoc_chiase(date_str: str, group_cols) -> pd.Series:
    """LN MBNT *before* chia sẻ: the raw cumulative column, with none of _y_ln_sau_chiase's
    pvkh_chiase deduction. Same grouping/cleanup as that function so the columns still line up
    with the lũy kế chart (silver's own dia_ban, cleaned; KHCN*/ME collapsed) — the only
    difference is the missing subtraction. No bdscif exclusion, matching _y_loinhuan."""
    df = silver_pvkh_dl_kh_luy_ke(date_str)
    if "dia_ban" in group_cols:
        df = _clean_dia_ban(df)
    if "pkkh" in group_cols:
        df = df.copy()
        df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    return df.groupby(group_cols)["ln_mbnt_luy_ke_den_ngay_bc"].sum()


@_df_cache()
def _fetch_ln_truoc_chiase(dim_col: str):
    group_cols = ["nhom_phu_trach", dim_col]
    return lambda d: _ln_mbnt_truoc_chiase(d, group_cols).rename("loi_nhuan").reset_index()


@_df_cache()
def daily_ln_mbnt_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _diff(_fetch_ln_truoc_chiase("dia_ban"), date_str, "dia_ban", "loi_nhuan")


@_df_cache()
def daily_ln_mbnt_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _diff(_fetch_ln_truoc_chiase("pkkh"), date_str, "pkkh", "loi_nhuan")


@_df_cache()
def daily_ds_hdls_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _diff(y_ds_hdls_by_nhom_diaban, date_str, "dia_ban", "doanh_so")


@_df_cache()
def daily_ds_hdls_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _diff(y_ds_hdls_by_nhom_pkkh, date_str, "pkkh", "doanh_so")


@_df_cache()
def daily_ln_hdls_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _diff(y_ln_hdls_by_nhom_diaban, date_str, "dia_ban", "loi_nhuan")


@_df_cache()
def daily_ln_hdls_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _diff(y_ln_hdls_by_nhom_pkkh, date_str, "pkkh", "loi_nhuan")


# TDPS doanh số is the one Trong ngày measure that is NOT differenced: pvkh_dsdaily_temp is
# already one row per day, so the day's figure is read straight off. Lợi nhuận still is, coming
# from silver's YTD cumulative like every other LN measure.
@_df_cache()
def daily_ds_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return ds_tdps_ngay_by_nhom_diaban(date_str)


@_df_cache()
def daily_ds_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return ds_tdps_ngay_by_nhom_pkkh(date_str)


@_df_cache()
def daily_ln_tdps_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _diff(y_ln_tdps_by_nhom_diaban, date_str, "dia_ban", "loi_nhuan")


@_df_cache()
def daily_ln_tdps_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _diff(y_ln_tdps_by_nhom_pkkh, date_str, "pkkh", "loi_nhuan")


@_df_cache()
def _daily_nim(date_str: str, dim_col: str) -> pd.DataFrame:
    """Daily NIM = (that day's LN) / (that day's DS).

    NIM is not additive across days, so the ratio itself cannot be differenced — only its two
    components can, and the ratio is then rebuilt from them. Both are cumulative columns in the
    source, so each is differenced against the previous trading day first:

        daily NIM = (LN_cum(d) - LN_cum(d-1)) / (DS_cum(d) - DS_cum(d-1))

    The numerator is LN *trước* chia sẻ, matching daily_ln_mbnt_* — see the module docstring.
    A day with no DS movement leaves the denominator at 0, so NIM is NA and the chart plots it
    as an empty column rather than dividing by zero."""
    group_cols = ["nhom_phu_trach", dim_col]

    def _fetch_ds(d):
        return _y_doanhso(d, group_cols).rename("doanh_so").reset_index()

    ds = _diff(_fetch_ds, date_str, dim_col, "doanh_so")
    ln = _diff(_fetch_ln_truoc_chiase(dim_col), date_str, dim_col, "loi_nhuan")
    merged = pd.merge(ds, ln, on=group_cols, how="outer").fillna(0.0)
    merged["nim"] = merged["loi_nhuan"] / merged["doanh_so"].replace(0, pd.NA)
    return merged[group_cols + ["nim"]]


@_df_cache()
def daily_nim_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _daily_nim(date_str, "dia_ban")


@_df_cache()
def daily_nim_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _daily_nim(date_str, "pkkh")


@_df_cache()
def _daily_nim_pooled(date_str: str, dim_col: str) -> pd.DataFrame:
    """Daily NIM pooled across every nhóm — same day-over-day differencing as _daily_nim, but
    DS and LN are each summed by dim_col alone (not per-nhóm) before differencing, so the
    resulting ratio is a genuine combined NIM, not an average of the per-nhóm ones."""
    def _fetch_ds_pooled(d):
        return _y_doanhso(d, [dim_col]).rename("doanh_so").reset_index()

    def _fetch_ln_pooled(d):
        return _ln_mbnt_truoc_chiase(d, [dim_col]).rename("loi_nhuan").reset_index()

    def _diff_pooled(fetch, value_col):
        today = fetch(date_str)
        prev = previous_date(date_str)
        if prev is None:
            return today[[dim_col, value_col]].copy()
        yesterday = fetch(prev)
        merged = pd.merge(today, yesterday, on=[dim_col], how="outer", suffixes=("_t", "_y")).fillna(0.0)
        merged[value_col] = merged[f"{value_col}_t"] - merged[f"{value_col}_y"]
        return merged[[dim_col, value_col]]

    ds = _diff_pooled(_fetch_ds_pooled, "doanh_so")
    ln = _diff_pooled(_fetch_ln_pooled, "loi_nhuan")
    merged = pd.merge(ds, ln, on=dim_col, how="outer").fillna(0.0)
    merged["nim"] = merged["loi_nhuan"] / merged["doanh_so"].replace(0, pd.NA)
    merged["nhom_phu_trach"] = ""
    return merged[["nhom_phu_trach", dim_col, "nim"]]


def daily_nim_diaban_pooled(date_str: str) -> pd.DataFrame:
    return _daily_nim_pooled(date_str, "dia_ban")


def daily_nim_pkkh_pooled(date_str: str) -> pd.DataFrame:
    return _daily_nim_pooled(date_str, "pkkh")


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}  (prev: {previous_date(d)})")
    for name, fn in [
        ("DS MBNT / dia_ban", daily_ds_mbnt_by_nhom_diaban),
        ("LN MBNT / dia_ban", daily_ln_mbnt_by_nhom_diaban),
        ("NIM MBNT / dia_ban", daily_nim_by_nhom_diaban),
        ("DS HDLS / dia_ban", daily_ds_hdls_by_nhom_diaban),
        ("LN HDLS / dia_ban", daily_ln_hdls_by_nhom_diaban),
    ]:
        print(f"\n{name}:\n{fn(d).to_string()}")
