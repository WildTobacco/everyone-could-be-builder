"""NIM HĐLS ngày b/c (single-day, non-cumulative) by nhóm phụ trách.

    NIM = LN_HĐLS_ngày × 365 × 100 / [(số dư CCS ngày b/c + số dư IRS ngày b/c) × tỷ giá ngày b/c]

All three inputs are that single day's own figures — not lũy kế/cumulative — matching
bronze_baocaotudong.pvkh_pstc_nhom_phu_trach's own _ngay_bc columns and
bronze_reuter_domestic.daily_currency_domestic's rate for the same date.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_pstc_nhom_phu_trach, usd_vnd_rate

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def nim_hdls_ngay_by_nhom(date_str: str) -> pd.Series:
    df = pvkh_pstc_nhom_phu_trach(date_str)
    ln = df.groupby("nhom_phu_trach")["sum_ln_hdls_ngay_bc"].sum().reindex(GROUPS + ["TOTAL"], fill_value=0.0)
    so_du = (
        df.groupby("nhom_phu_trach")[["sum_so_du_ccs_ngay_bc", "sum_so_du_irs_ngay_bc"]]
        .sum().sum(axis=1)
        .reindex(GROUPS + ["TOTAL"], fill_value=0.0)
    )
    rate = usd_vnd_rate(date_str)
    if not rate:
        return pd.Series(pd.NA, index=GROUPS + ["TOTAL"])

    denom = (so_du * rate).replace(0, pd.NA)
    return ln * 365 * 100 / denom


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}, usd_vnd_rate: {usd_vnd_rate(d)}")
    print(nim_hdls_ngay_by_nhom(d))
