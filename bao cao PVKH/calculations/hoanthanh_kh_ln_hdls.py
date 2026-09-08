"""Python port of HoanThanh_KH_LN_hdls_<nhóm>_Update — exact same shape as
hoanthanh_kh_ds_hdls.py, just LN HDLS instead of DS HDLS. See that module for why the
source DAX's hardcoded DIVIDE(KH_Thang, 79) is replaced with the dynamic WorkingDays_YTD.

    VAR LN_Current = CALCULATE(SUM(...[sum_LN_HDLS_ngay_bc]), [Nhom_phu_trach] = "<X>")
    VAR KH_Thang = <LN HDLS plan for the selected month, nhóm "<X>">
    VAR KH_PerDay = DIVIDE(KH_Thang, WorkingDays_YTD)
    VAR Gap = LN_Current - KH_PerDay
    RETURN IF(Gap >= 0, "▲ " & Gap_Format, "▼ " & Gap_Format)
"""

from data_connect.db_connect import _df_cache
import pandas as pd

from calculations.ln_hdls_ngay_by_nhom import ln_hdls_ngay_by_nhom
from calculations.ln_hdls_hoan_thanh import ke_hoach_ln_hdls_thang
from calculations.working_days_ytd import working_days_ytd
from calculations.hoanthanh_kh_ds_mbnt import _fmt_gap_value


@_df_cache()
def _ln_current_and_kh_per_day(date_str: str, group: str):
    ln_current = ln_hdls_ngay_by_nhom(date_str).get(group)
    month_value = str(pd.to_datetime(date_str).month)
    kh_thang = ke_hoach_ln_hdls_thang(month_value).get(group)
    if pd.isna(ln_current) or pd.isna(kh_thang):
        return None, None
    return ln_current, kh_thang / working_days_ytd(date_str)


@_df_cache()
def hoanthanh_kh_ln_hdls(date_str: str, group: str) -> str | None:
    ln_current, kh_per_day = _ln_current_and_kh_per_day(date_str, group)
    if ln_current is None:
        return None
    gap = ln_current - kh_per_day
    arrow = "▲" if gap >= 0 else "▼"
    return f"{arrow} {_fmt_gap_value(abs(gap))}"


@_df_cache()
def ht_thang_ln_hdls_pct(date_str: str, group: str) -> float | None:
    ln_current, kh_per_day = _ln_current_and_kh_per_day(date_str, group)
    if ln_current is None or not kh_per_day:
        return None
    return ln_current / kh_per_day * 100


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    for g in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        print(g, hoanthanh_kh_ln_hdls(d, g), f"{ht_thang_ln_hdls_pct(d, g):.2f}%")
