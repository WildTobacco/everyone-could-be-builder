"""Python port of HoanThanh_KH_DS_<nhóm>_Update, from a different, pre-existing dashboard's
DAX (not this project's own Power BI model) — see ds_mbnt_ngay_by_nhom.py for the naming
note on the source table/columns.

Compares today's non-accumulative (single day, not YTD/lũy kế) DS MBNT actual against a
daily-pace target: this month's DS MBNT plan (KH_Thang, itself cumulative/lũy kế — the
DAX just reads a hardcoded per-month column like "T8.2026" directly, no subtraction from
the prior month) divided by the cumulative working-days-elapsed count for that month
(WorkingDays_YTD). This matches the DAX exactly, rather than isolating just that month's
own portion — the DAX's hardcoded-per-month-measure design (KH_LN_KDNT_T8_PTKD1 etc.,
one measure per month) means KH_Thang was always meant to be used as its raw cumulative
value, not decomposed further. Shared by the 4 per-nhóm wrapper files
(hoanthanh_kh_ds_ptkd1.py, _ptkd2.py, _vpv.py, _ht.py) so the gap/format logic isn't
duplicated 4 times.

    VAR DS_Current = CALCULATE(SUM(...[sum_DS_MBNT_ngay_bc]), [Nhom_phu_trach] = "<X>")
    VAR KH_Thang = <DS MBNT plan for the selected month, nhóm "<X>">
    VAR KH_PerDay = DIVIDE(KH_Thang, WorkingDays_YTD)
    VAR Gap = DS_Current - KH_PerDay
    RETURN IF(Gap >= 0, "▲ " & Gap_Format, "▼ " & Gap_Format)
"""

from data_connect.db_connect import _df_cache
import pandas as pd

from calculations.ds_mbnt_ngay_by_nhom import ds_mbnt_ngay_by_nhom
from calculations.ht_ds_mbnt_nam import ke_hoach_ds_mbnt_thang
from calculations.working_days_ytd import working_days_ytd


def _fmt_gap_value(value: float) -> str:
    """Port of Gap_Format's SWITCH: FORMAT(..., "0.#") shows 1 decimal only if non-zero.
    M is the smallest unit shown — a sub-1M gap used to fall back to a bare unitless integer
    (e.g. "500,000"), which read as a raw count rather than a currency gap; now floors to "0M"
    or "0.x M" instead, per user request ("HT so với KH/ngày round to M at minimum")."""
    if value >= 1e9:
        n = value / 1e9
        s = f"{n:.1f}"
        return (s[:-2] if s.endswith(".0") else s) + "bn"
    n = value / 1e6
    s = f"{n:.1f}"
    return (s[:-2] if s.endswith(".0") else s) + "M"


@_df_cache()
def _ds_current_and_kh_per_day(date_str: str, group: str):
    """Shared by hoanthanh_kh_ds_mbnt (absolute gap) and ht_thang_ds_mbnt_pct (% completion) —
    both are just different presentations of the same DS_Current vs. KH_PerDay comparison."""
    ds_current = ds_mbnt_ngay_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ds_mbnt_thang(month_value).get(group)
    if pd.isna(ds_current) or pd.isna(kh_thang):
        return None, None
    return ds_current, kh_thang / working_days_ytd(date_str)


@_df_cache()
def hoanthanh_kh_ds_mbnt(date_str: str, group: str) -> str | None:
    ds_current, kh_per_day = _ds_current_and_kh_per_day(date_str, group)
    if ds_current is None:
        return None
    gap = ds_current - kh_per_day
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def ht_thang_ds_mbnt_pct(date_str: str, group: str) -> float | None:
    """DS_Current as a % of that day's pace target (this month's KH_Thang / WorkingDays_YTD) —
    i.e. "HT tháng", since KH_Thang is already scoped to the selected month specifically."""
    ds_current, kh_per_day = _ds_current_and_kh_per_day(date_str, group)
    if ds_current is None or not kh_per_day:
        return None
    return ds_current / kh_per_day * 100


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    for g in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        print(g, hoanthanh_kh_ds_mbnt(d, g), f"{ht_thang_ds_mbnt_pct(d, g):.2f}%")
