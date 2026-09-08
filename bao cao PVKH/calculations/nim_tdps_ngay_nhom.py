"""NIM TDPS ngày b/c (single-day, non-cumulative) by nhóm phụ trách.

    NIM = LN_TDPS_ngày × 365 × 100 / [số dư TDPS ngày b/c × tỷ giá ngày b/c]

Same shape as nim_hdls_ngay_nhom.py, just TDPS's own single balance column instead of
HĐLS's CCS+IRS pair.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_pstc_nhom_phu_trach, usd_vnd_rate

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def nim_tdps_ngay_by_nhom(date_str: str) -> pd.Series:
    df = pvkh_pstc_nhom_phu_trach(date_str)
    ln = df.groupby("nhom_phu_trach")["sum_ln_tdps_ngay_bc"].sum().reindex(GROUPS + ["TOTAL"], fill_value=0.0)
    so_du = df.groupby("nhom_phu_trach")["sum_so_du_tdps_ngay_bc"].sum().reindex(GROUPS + ["TOTAL"], fill_value=0.0)
    rate = usd_vnd_rate(date_str)
    if not rate:
        return pd.Series(pd.NA, index=GROUPS + ["TOTAL"])

    denom = (so_du * rate).replace(0, pd.NA)
    return ln * 365 * 100 / denom


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}, usd_vnd_rate: {usd_vnd_rate(d)}")
    print(nim_tdps_ngay_by_nhom(d))
