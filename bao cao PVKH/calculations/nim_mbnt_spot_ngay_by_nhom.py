"""NIM Spot Mua / NIM Spot Bán by nhóm, for the selected day — from a Power BI card visual
using pvkh_mbnt_nhom_phu_trach's nim_mbnt_buy_spot_ngay_bc / nim_mbnt_sell_spot_ngay_bc
columns (buy-spot / sell-spot NIM, as opposed to nim_mbnt_ngay_bc's combined figure or
nim_mbnt_luy_ke_den_ngay_bc's cumulative one)."""

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_mbnt_nhom_phu_trach
from calculations.date_table import latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def nim_mbnt_buy_spot_by_nhom(date_str: str):
    """One row per nhóm already in the source table. TOTAL is read directly from the
    source's own pre-aggregated 'TOTAL' row, not recomputed (NIM is a ratio — averaging
    it across groups ourselves would be wrong; the source's own TOTAL row is correct)."""
    df = pvkh_mbnt_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["nim_mbnt_buy_spot_ngay_bc"].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


@_df_cache()
def nim_mbnt_sell_spot_by_nhom(date_str: str):
    df = pvkh_mbnt_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["nim_mbnt_sell_spot_ngay_bc"].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


@_df_cache()
def nim_mbnt_ngay_by_nhom(date_str: str):
    """NIM MBNT ngày — the day's combined/blended NIM (nim_mbnt_ngay_bc), as opposed to the
    buy-spot/sell-spot split above. Same shape as HĐLS/TDPS's own "NIM ngày" lookups."""
    df = pvkh_mbnt_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["nim_mbnt_ngay_bc"].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


if __name__ == "__main__":
    d = latest_date()
    print("NIM Spot Mua:\n", nim_mbnt_buy_spot_by_nhom(d))
    print("NIM Spot Bán:\n", nim_mbnt_sell_spot_by_nhom(d))
    print("NIM ngày:\n", nim_mbnt_ngay_by_nhom(d))
