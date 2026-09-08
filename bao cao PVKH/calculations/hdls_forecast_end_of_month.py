"""Python port of LN_HDLS_du_kien_cuoi_thang / DS_HDLS_du_kien_cuoi_thang and their
HoanThanh_KH_..._ForecastGap DAX measures — a forecast of HĐLS's cumulative (lũy kế) DS/LN as
of month-end, extrapolated from the YTD-so-far average daily pace, compared against that
month's KH (kế hoạch). Same shape as mbnt_forecast_end_of_month.py — see that module's
docstring for where WorkingDays_Passed/WorkingDays_MonthEnd come from.

    DS_Forecast_EndMonth = DS_YTD / WorkingDays_Passed * WorkingDays_MonthEnd
    Gap = DS_Forecast_EndMonth - KH_Thang

The supplied HoanThanh_KH_LN_HDLS_ForecastGap DAX compared the LN forecast against
KH_LN_PSTC_T8_PTKD1 (PSTC/TDPS's plan, not HĐLS's own) — a copy-paste artifact from a
TDPS-based template, per the user. This ports the corrected version: LN HĐLS's forecast
against HĐLS's own KH (ke_hoach_ln_hdls_thang), matching how the DS side already correctly
used KH_DS_HDLS and how the MBNT sibling module compares each metric to its own product's
plan."""

from data_connect.db_connect import _df_cache
import pandas as pd

from calculations.tong_ds_hdls_ytd_nhom import tong_ds_hdls_ytd_by_nhom
from calculations.tong_ln_hdls_ytd_nhom import tong_ln_hdls_ytd_by_nhom
from calculations.ds_hdls_hoan_thanh import ke_hoach_ds_hdls_thang
from calculations.ln_hdls_hoan_thanh import ke_hoach_ln_hdls_thang
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
def ds_hdls_forecast_end_of_month_by_nhom(date_str: str) -> pd.Series:
    return _forecast_end_of_month(tong_ds_hdls_ytd_by_nhom(date_str), date_str)


@_df_cache()
def ln_hdls_forecast_end_of_month_by_nhom(date_str: str) -> pd.Series:
    return _forecast_end_of_month(tong_ln_hdls_ytd_by_nhom(date_str), date_str)


def _forecast_gap(forecast: float, kh_thang: float) -> str | None:
    if pd.isna(forecast) or pd.isna(kh_thang):
        return None
    gap = forecast - kh_thang
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def hoanthanh_kh_ds_hdls_forecast_gap(date_str: str, group: str) -> str | None:
    forecast = ds_hdls_forecast_end_of_month_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ds_hdls_thang(month_value).get(group)
    return _forecast_gap(forecast, kh_thang)


@_df_cache()
def hoanthanh_kh_ln_hdls_forecast_gap(date_str: str, group: str) -> str | None:
    forecast = ln_hdls_forecast_end_of_month_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ln_hdls_thang(month_value).get(group)
    return _forecast_gap(forecast, kh_thang)


@_df_cache()
def ht_forecast_ds_hdls_pct(date_str: str, group: str) -> float | None:
    """Forecast_EndMonth as a % of that month's KH_Thang — pairs with the absolute gap for the
    new pace row, same "gap number + %" shape as HT so với KH/ngày."""
    forecast = ds_hdls_forecast_end_of_month_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ds_hdls_thang(month_value).get(group)
    if pd.isna(forecast) or not kh_thang:
        return None
    return forecast / kh_thang * 100


@_df_cache()
def ht_forecast_ln_hdls_pct(date_str: str, group: str) -> float | None:
    forecast = ln_hdls_forecast_end_of_month_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ln_hdls_thang(month_value).get(group)
    if pd.isna(forecast) or not kh_thang:
        return None
    return forecast / kh_thang * 100


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("DS forecast end-of-month:\n", ds_hdls_forecast_end_of_month_by_nhom(d))
    print("LN forecast end-of-month:\n", ln_hdls_forecast_end_of_month_by_nhom(d))
    for g in GROUPS:
        print(
            g, "DS gap:", hoanthanh_kh_ds_hdls_forecast_gap(d, g),
            " LN gap:", hoanthanh_kh_ln_hdls_forecast_gap(d, g),
        )
