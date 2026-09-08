"""Python port of HoanThanh_KH_LN_<nhóm>_Update, from a different, pre-existing dashboard's
DAX (not this project's own Power BI model) — see ds_mbnt_ngay_by_nhom.py for the naming
note on the source table/columns. Exact same shape as hoanthanh_kh_ds_mbnt.py, just LN
instead of DS (the source DAX's own variable is misleadingly still named "DS_Current" for
the LN measure too — a copy-paste artifact in the original; named correctly here).

Compares today's non-accumulative (single day, not YTD/lũy kế) LN MBNT actual against a
daily-pace target: this month's LN MBNT plan (KH_Thang, itself cumulative/lũy kế — the
DAX just reads a hardcoded per-month column like "T8.2026" directly, no subtraction from
the prior month) divided by the cumulative working-days-elapsed count for that month
(WorkingDays_YTD). This matches the DAX exactly, rather than isolating just that month's
own portion — the DAX's hardcoded-per-month-measure design (KH_LN_KDNT_T8_PTKD1 etc., one
measure per month, "sau này có thể auto hoá") means KH_Thang was always meant to be used
as its raw cumulative value, not decomposed further. Ported against ke_hoach_ln_mbnt_thang,
the already-existing LN MBNT (not the broader LN KDNT&PS) monthly plan, matching how
KH_DS_KDNT_T8_PTKD1 was ported against the DS-MBNT-specific plan for the same reason:
DS_Current/LN_Current above is unambiguously MBNT-scoped.
"""

from data_connect.db_connect import _df_cache
import pandas as pd

from calculations.ln_mbnt_ngay_by_nhom import ln_mbnt_ngay_by_nhom
from calculations.ht_ln_mbnt_nam import ke_hoach_ln_mbnt_thang
from calculations.working_days_ytd import working_days_ytd
from calculations.hoanthanh_kh_ds_mbnt import _fmt_gap_value


@_df_cache()
def _ln_current_and_kh_per_day(date_str: str, group: str):
    """Shared by hoanthanh_kh_ln_mbnt (absolute gap) and ht_thang_ln_mbnt_pct (% completion)."""
    ln_current = ln_mbnt_ngay_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ln_mbnt_thang(month_value).get(group)
    if pd.isna(ln_current) or pd.isna(kh_thang):
        return None, None
    return ln_current, kh_thang / working_days_ytd(date_str)


@_df_cache()
def hoanthanh_kh_ln_mbnt(date_str: str, group: str) -> str | None:
    ln_current, kh_per_day = _ln_current_and_kh_per_day(date_str, group)
    if ln_current is None:
        return None
    gap = ln_current - kh_per_day
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def ht_thang_ln_mbnt_pct(date_str: str, group: str) -> float | None:
    """LN_Current as a % of that day's pace target (this month's KH_Thang / WorkingDays_YTD)
    — i.e. "HT tháng", since KH_Thang is already scoped to the selected month specifically."""
    ln_current, kh_per_day = _ln_current_and_kh_per_day(date_str, group)
    if ln_current is None or not kh_per_day:
        return None
    return ln_current / kh_per_day * 100


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    for g in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        print(g, hoanthanh_kh_ln_mbnt(d, g), f"{ht_thang_ln_mbnt_pct(d, g):.2f}%")
