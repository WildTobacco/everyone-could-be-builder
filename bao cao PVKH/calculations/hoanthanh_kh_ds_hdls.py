"""Python port of HoanThanh_KH_DS_hdls_<nhóm>_Update, from a different, pre-existing
dashboard's DAX (not this project's own Power BI model).

Compares today's non-accumulative (single day, not YTD/lũy kế) DS HDLS actual against a
daily-pace target: this month's DS HDLS plan (KH_Thang, cumulative/lũy kế) divided by the
working days elapsed that year (WorkingDays_YTD), same as the MBNT equivalent.

The source HĐLS DAX instead hardcodes DIVIDE(KH_Thang, 79) — 79 being that table's April
value, so an August plan was being divided by April's day count, roughly doubling the
target. Deliberately not reproduced: this now uses the dynamic divisor, so HĐLS agrees with
MBNT and TDPS. It will differ from the existing Power BI report until those measures are
corrected the same way.

    VAR DS_Current = CALCULATE(SUM(...[sum_DS_HDLS_ngay_bc]), [Nhom_phu_trach] = "<X>")
    VAR KH_Thang = <DS HDLS plan for the selected month, nhóm "<X>">
    VAR KH_PerDay = DIVIDE(KH_Thang, WorkingDays_YTD)
    VAR Gap = DS_Current - KH_PerDay
    RETURN IF(Gap >= 0, "▲ " & Gap_Format, "▼ " & Gap_Format)
"""

from data_connect.db_connect import _df_cache
import pandas as pd

from calculations.ds_hdls_ngay_by_nhom import ds_hdls_ngay_by_nhom
from calculations.ds_hdls_hoan_thanh import ke_hoach_ds_hdls_thang
from calculations.working_days_ytd import working_days_ytd
from calculations.hoanthanh_kh_ds_mbnt import _fmt_gap_value


@_df_cache()
def _ds_current_and_kh_per_day(date_str: str, group: str):
    ds_current = ds_hdls_ngay_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ds_hdls_thang(month_value).get(group)
    if pd.isna(ds_current) or pd.isna(kh_thang):
        return None, None
    return ds_current, kh_thang / working_days_ytd(date_str)


@_df_cache()
def hoanthanh_kh_ds_hdls(date_str: str, group: str) -> str | None:
    ds_current, kh_per_day = _ds_current_and_kh_per_day(date_str, group)
    if ds_current is None:
        return None
    gap = ds_current - kh_per_day
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def ht_thang_ds_hdls_pct(date_str: str, group: str) -> float | None:
    ds_current, kh_per_day = _ds_current_and_kh_per_day(date_str, group)
    if ds_current is None or not kh_per_day:
        return None
    return ds_current / kh_per_day * 100


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    for g in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        print(g, hoanthanh_kh_ds_hdls(d, g), f"{ht_thang_ds_hdls_pct(d, g):.2f}%")
