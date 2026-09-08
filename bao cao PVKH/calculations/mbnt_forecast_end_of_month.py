"""Python port of LN_MBNT_du_kien_cuoi_thang / DS_MBNT_du_kien_cuoi_thang and their
HoanThanh_KH_..._ForecastGap DAX measures — a forecast of MBNT's cumulative (lũy kế) DS/LN as
of month-end, extrapolated from the YTD-so-far average daily pace, compared against that
month's KH (kế hoạch).

    DS_Forecast_EndMonth = DS_YTD / WorkingDays_Passed * WorkingDays_MonthEnd
    Gap = DS_Forecast_EndMonth - KH_Thang

WorkingDays_Passed/WorkingDays_MonthEnd both come from working_days_ytd.py's real-calendar
functions (working_days_passed()/working_days_month_end()), not the older
working_days_ytd()/_WORKING_DAYS_YTD SWITCH table used by the HT tháng gauge measures — those
are two different DAX measures with different values for the same month (see that module's
docstring). Confirmed exact against a live forecast card once wired to the real-calendar
pair."""

from data_connect.db_connect import _df_cache
import pandas as pd

from calculations.tong_ds_mbnt_ytd import tong_ds_mbnt_ytd_by_nhom
from calculations.tong_ln_mbnt_ytd import tong_ln_mbnt_ytd_by_nhom
from calculations.ht_ds_mbnt_nam import ke_hoach_ds_mbnt_thang
from calculations.ht_ln_mbnt_nam import ke_hoach_ln_mbnt_thang
from calculations.working_days_ytd import working_days_passed, working_days_month_end
from calculations.hoanthanh_kh_ds_mbnt import _fmt_gap_value

GROUPS = ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]


def _forecast_end_of_month(ytd: pd.Series, date_str: str) -> pd.Series:
    wd_passed = working_days_passed(date_str)
    wd_month_end = working_days_month_end(date_str)
    if not wd_passed:
        return pd.Series(float("nan"), index=ytd.index)
    return ytd / wd_passed * wd_month_end


@_df_cache()
def ds_mbnt_forecast_end_of_month_by_nhom(date_str: str) -> pd.Series:
    return _forecast_end_of_month(tong_ds_mbnt_ytd_by_nhom(date_str), date_str)


@_df_cache()
def ln_mbnt_forecast_end_of_month_by_nhom(date_str: str) -> pd.Series:
    return _forecast_end_of_month(tong_ln_mbnt_ytd_by_nhom(date_str), date_str)


def _forecast_gap(forecast: float, kh_thang: float) -> str | None:
    if pd.isna(forecast) or pd.isna(kh_thang):
        return None
    gap = forecast - kh_thang
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def hoanthanh_kh_ds_mbnt_forecast_gap(date_str: str, group: str) -> str | None:
    forecast = ds_mbnt_forecast_end_of_month_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ds_mbnt_thang(month_value).get(group)
    return _forecast_gap(forecast, kh_thang)


@_df_cache()
def hoanthanh_kh_ln_mbnt_forecast_gap(date_str: str, group: str) -> str | None:
    forecast = ln_mbnt_forecast_end_of_month_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ln_mbnt_thang(month_value).get(group)
    return _forecast_gap(forecast, kh_thang)


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("DS forecast end-of-month:\n", ds_mbnt_forecast_end_of_month_by_nhom(d))
    print("LN forecast end-of-month:\n", ln_mbnt_forecast_end_of_month_by_nhom(d))
    for g in GROUPS:
        print(g, "DS gap:", hoanthanh_kh_ds_mbnt_forecast_gap(d, g), " LN gap:", hoanthanh_kh_ln_mbnt_forecast_gap(d, g))
