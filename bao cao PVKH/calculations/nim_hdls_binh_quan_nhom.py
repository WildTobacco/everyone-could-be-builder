"""NIM HĐLS bình quân (year-to-date, balance-weighted average) by nhóm phụ trách.

    NIM = Σᵢ [(số dư CCS ngày i + số dư IRS ngày i) × NIM_HĐLS_ngày_i] / Σᵢ (số dư CCS ngày i + số dư IRS ngày i)
    for i = 1/1 → ngày báo cáo (the selected date), where NIM_HĐLS_ngày_i is
    nim_hdls_ngay_nhom.py's own per-day formula.

weight_i × NIM_ngày_i algebraically reduces to ln_i × 365 × 100 / rate_i whenever weight_i > 0
(the balance term cancels), so this sums that reduced term directly across every day in the
window instead of computing 228+ individual daily NIM ratios first. On a zero-balance day the
literal formula's weight_i × NIM_ngày_i is 0 by definition (NIM_ngày_i itself is undefined with
no balance to divide by) — handled explicitly here rather than relying on the reduced term
alone, which would not automatically zero out just because the balance happens to be 0.
"""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_pstc_nhom_phu_trach_range, usd_vnd_rate_range

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def nim_hdls_binh_quan_by_nhom(date_str: str) -> pd.Series:
    year_start = pd.Timestamp(date_str).replace(month=1, day=1).strftime("%Y-%m-%d")
    df = pvkh_pstc_nhom_phu_trach_range(year_start, date_str).copy()
    rates = usd_vnd_rate_range(year_start, date_str)

    df["ngay"] = pd.to_datetime(df["ngay"])
    df["rate"] = df["ngay"].map(rates)
    df["balance"] = df["sum_so_du_ccs_ngay_bc"].fillna(0) + df["sum_so_du_irs_ngay_bc"].fillna(0)
    df["term"] = (df["sum_ln_hdls_ngay_bc"].fillna(0) * 365 * 100 / df["rate"]).where(df["balance"] > 0, 0.0)

    numerator = df.groupby("nhom_phu_trach")["term"].sum().reindex(GROUPS + ["TOTAL"], fill_value=0.0)
    denominator = df.groupby("nhom_phu_trach")["balance"].sum().reindex(GROUPS + ["TOTAL"], fill_value=0.0)
    return numerator / denominator.replace(0, pd.NA)


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print(nim_hdls_binh_quan_by_nhom(d))
