"""Python port of LN_TDPS_du_kien_cuoi_thang / DS_TDPS_du_kien_cuoi_thang and
HoanThanh_KH_LN_tdps_ForecastGap (and their PTKD1/PTKD2/VPV/TOTAL siblings) — same shape as
mbnt_forecast_end_of_month.py / hdls_forecast_end_of_month.py.

    Forecast_EndMonth = YTD_lũy_kế / WorkingDays_Passed * WorkingDays_MonthEnd
    Gap = LN_Forecast_EndMonth - KH_Thang

WorkingDays_Passed/WorkingDays_MonthEnd come from working_days_ytd.py's real-calendar functions
— see mbnt_forecast_end_of_month.py's docstring for why they're separate from working_days_ytd()
(the older, hand-maintained SWITCH used by the HT tháng gauge measures elsewhere).

The source DAX's KH_LN_PSTC reference maps to this project's existing "LN TDPS" plan
(ke_hoach_ln_tdps_thang, from hoanthanh_kh_ln_tdps.py) — same source already used for TDPS's
HT panel elsewhere.

Doanh số has no equivalent gap: ke_hoach_theo_ptkd() (the KHKD plan sheet) has no "DS TDPS"
san_phẩm entry at all, so there is no KH_DS_TPDS to compare the forecast against — confirmed
by the user, who asked for the forecasted DS figure shown plainly instead of a gap."""

from data_connect.db_connect import _df_cache
import pandas as pd

from calculations.ln_tdps_luy_ke_by_nhom import ln_tdps_luy_ke_by_nhom
from calculations.ds_tdps import ds_tdps_luy_ke_by_nhom
from calculations.hoanthanh_kh_ln_tdps import ke_hoach_ln_tdps_thang
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
def ln_tdps_forecast_end_of_month_by_nhom(date_str: str) -> pd.Series:
    return _forecast_end_of_month(ln_tdps_luy_ke_by_nhom(date_str), date_str)


@_df_cache()
def ds_tdps_forecast_end_of_month_by_nhom(date_str: str) -> pd.Series:
    return _forecast_end_of_month(ds_tdps_luy_ke_by_nhom(date_str), date_str)


@_df_cache()
def hoanthanh_kh_ln_tdps_forecast_gap(date_str: str, group: str) -> str | None:
    forecast = ln_tdps_forecast_end_of_month_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ln_tdps_thang(month_value).get(group)
    if pd.isna(forecast) or pd.isna(kh_thang):
        return None
    gap = forecast - kh_thang
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def ds_tdps_forecast_end_of_month_value(date_str: str, group: str) -> str | None:
    """No KH DS TDPS to compare against, so this is just the forecasted figure formatted
    plainly (no ▲/▼ arrow) — see module docstring."""
    forecast = ds_tdps_forecast_end_of_month_by_nhom(date_str).get(group)
    if pd.isna(forecast):
        return None
    return _fmt_gap_value(forecast)


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("LN forecast end-of-month:\n", ln_tdps_forecast_end_of_month_by_nhom(d))
    print("DS forecast end-of-month:\n", ds_tdps_forecast_end_of_month_by_nhom(d))
    for g in GROUPS:
        print(g, "LN gap:", hoanthanh_kh_ln_tdps_forecast_gap(d, g), " DS forecast:", ds_tdps_forecast_end_of_month_value(d, g))
