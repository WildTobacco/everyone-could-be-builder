"""Two distinct working-day conventions live in the source Power BI model, both named
similarly but computed differently, and this module ports both separately:

1. The WorkingDays_YTD SWITCH used by HoanThanh_KH_DS_*_Update (the HT tháng gauge measures)
   — a fixed, hand-maintained business-calendar convention for cumulative working days from
   Jan 1 through end of month, not derived from an actual calendar/holiday table. Ported as
   working_days_ytd()/working_days_in_month() below, unchanged.

2. WorkingDays_Passed/WorkingDays_MonthEnd used by the *_du_kien_cuoi_thang forecast measures
   — CALCULATE(COUNTROWS(DateTable), ...DateTable[IsWorkingDay]=1...), i.e. a real day-level
   count against DateTable's own IsWorkingDay calculated column:

       IsWorkingDay = IF ( WEEKDAY(Ngay, 2) > 5 || Ngay IN {holiday dates}, 0, 1 )

   Ported as working_days_passed()/working_days_month_end() below, using _VN_HOLIDAYS_2026 —
   copied verbatim from that column's own DAX (Tết Feb 16-21, Hùng Kings' Day observed Apr 27
   since the actual lunar date Apr 26 falls on a Sunday in 2026, Reunification Day Apr 30, Labor
   Day May 1, National Day Sep 2 — no Jan 1 entry, unlike convention #1's table). Confirmed
   against a live forecast card: reproduced Power BI's DS/LN forecast for all 4 nhóm exactly
   once WorkingDays_MonthEnd was pulled from *this* real-calendar count instead of convention
   #1's fixed table (164 vs. the real 165 for August) — the two conventions really do diverge,
   they are not the same "August has 164 working days" fact reused twice."""

from data_connect.db_connect import _df_cache
import calendar
import datetime
import pandas as pd

_WORKING_DAYS_YTD = {
    1: 21, 2: 36, 3: 58, 4: 79, 5: 99, 6: 121,
    7: 144, 8: 164, 9: 185, 10: 207, 11: 228, 12: 251,
}

_VN_HOLIDAYS_2026 = {
    datetime.date(2026, 2, 16), datetime.date(2026, 2, 17), datetime.date(2026, 2, 18),
    datetime.date(2026, 2, 19), datetime.date(2026, 2, 20), datetime.date(2026, 2, 21),
    datetime.date(2026, 4, 27), datetime.date(2026, 4, 30),
    datetime.date(2026, 5, 1),
    datetime.date(2026, 9, 2),
}


@_df_cache()
def working_days_ytd(date_str: str) -> int:
    month = pd.to_datetime(date_str).month
    return _WORKING_DAYS_YTD[month]


@_df_cache()
def working_days_in_month(date_str: str) -> int:
    """Working days within just the selected date's month (not cumulative from Jan 1) —
    this month's WorkingDays_YTD minus the previous month's (month 1 has no previous
    month, so it's used as-is)."""
    month = pd.to_datetime(date_str).month
    previous = _WORKING_DAYS_YTD[month - 1] if month > 1 else 0
    return _WORKING_DAYS_YTD[month] - previous


def _is_working_day(d: datetime.date) -> bool:
    return d.weekday() < 5 and d not in _VN_HOLIDAYS_2026


def _count_working_days(year: int, through: datetime.date) -> int:
    d = datetime.date(year, 1, 1)
    count = 0
    while d <= through:
        if _is_working_day(d):
            count += 1
        d += datetime.timedelta(days=1)
    return count


@_df_cache()
def working_days_passed(date_str: str) -> int:
    """DAX's WorkingDays_Passed — real working days from Jan 1 through the selected date,
    inclusive, per _VN_HOLIDAYS_2026. Only exact for 2026 (the only year that list covers)."""
    ref_date = pd.to_datetime(date_str).date()
    return _count_working_days(ref_date.year, ref_date)


@_df_cache()
def working_days_month_end(date_str: str) -> int:
    """DAX's WorkingDays_MonthEnd — real working days from Jan 1 through the end of the
    selected date's month. NOT the same number as working_days_ytd() for the same month (see
    module docstring) — this one comes from the real calendar, that one from the separate
    hand-maintained SWITCH."""
    ref_date = pd.to_datetime(date_str).date()
    month_end = datetime.date(ref_date.year, ref_date.month, calendar.monthrange(ref_date.year, ref_date.month)[1])
    return _count_working_days(ref_date.year, month_end)


if __name__ == "__main__":
    for m in range(1, 13):
        d = f"2026-{m:02d}-15"
        print(
            m, "ytd(SWITCH):", working_days_ytd(d), "in_month:", working_days_in_month(d),
            "passed:", working_days_passed(d), "month_end(real):", working_days_month_end(d),
        )
