"""NIM TDPS bình quân (year-to-date average) by nhóm phụ trách.

    NIM = LN_TDPS_lũy_kế × 365 × 100 / (số dư TDPS bình quân nhóm × tỷ giá ngày báo cáo × số ngày từ 1/1 đến ngày báo cáo)

"số ngày từ 1/1 đến ngày báo cáo" is calendar days elapsed since Jan 1 (inclusive of both
ends), matching the "*365" annualization already in the numerator — both sides of the ratio
use the same calendar-day basis, not a mix of calendar and working days. This day-count term
is what keeps the result comparable in scale to NIM HĐLS bình quân (nim_hdls_binh_quan_nhom.py),
whose day-by-day weighted-average formula has the same deflation built in implicitly by
summing over every day since 1/1 rather than using a single already-averaged balance figure.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_pstc_nhom_phu_trach, usd_vnd_rate
from calculations.ln_tdps_luy_ke_by_nhom import ln_tdps_luy_ke_by_nhom

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def nim_tdps_binh_quan_by_nhom(date_str: str) -> pd.Series:
    ln = ln_tdps_luy_ke_by_nhom(date_str)
    df = pvkh_pstc_nhom_phu_trach(date_str)
    so_du = df.groupby("nhom_phu_trach")["so_du_tdps_binh_quan"].sum().reindex(GROUPS + ["TOTAL"], fill_value=0.0)
    rate = usd_vnd_rate(date_str)
    if not rate:
        return pd.Series(pd.NA, index=GROUPS + ["TOTAL"])

    year_start = pd.Timestamp(date_str).replace(month=1, day=1)
    so_ngay = (pd.Timestamp(date_str) - year_start).days + 1

    denom = (so_du * rate * so_ngay).replace(0, pd.NA)
    return ln * 365 * 100 / denom


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}, usd_vnd_rate: {usd_vnd_rate(d)}")
    print(nim_tdps_binh_quan_by_nhom(d))
