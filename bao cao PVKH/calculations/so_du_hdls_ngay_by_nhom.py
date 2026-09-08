"""Số dư (outstanding balance) HĐLS by nhóm phụ trách — both the selected day's snapshot
(ngay_bc, same source/shape as so_du_tdps_ngay_by_nhom in tdps_ngay_by_nhom.py) and the YTD
average (binh_quan). HĐLS splits into CCS and IRS sub-products, each with its own balance
column, plus a combined one.
"""

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_pstc_nhom_phu_trach
from calculations.date_table import latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def _by_nhom(date_str: str, column: str):
    df = pvkh_pstc_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")[column].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


@_df_cache()
def so_du_ccs_ngay_by_nhom(date_str: str):
    return _by_nhom(date_str, "sum_so_du_ccs_ngay_bc")


@_df_cache()
def so_du_irs_ngay_by_nhom(date_str: str):
    return _by_nhom(date_str, "sum_so_du_irs_ngay_bc")


@_df_cache()
def so_du_hdls_ngay_by_nhom(date_str: str):
    """Combined CCS+IRS số dư HĐLS on the selected day — summed from the two sub-product
    columns rather than read off the source's own sum_so_du_hdls_ngay_bc, which goes to 0 on
    weekends/holidays while sum_so_du_ccs_ngay_bc/sum_so_du_irs_ngay_bc still carry the last
    business day's snapshot forward (same inconsistency nim_hdls_ngay_nhom.py already works
    around the same way)."""
    return so_du_ccs_ngay_by_nhom(date_str).add(so_du_irs_ngay_by_nhom(date_str), fill_value=0.0)


@_df_cache()
def so_du_ccs_binh_quan_by_nhom(date_str: str):
    return _by_nhom(date_str, "so_du_ccs_binh_quan")


@_df_cache()
def so_du_irs_binh_quan_by_nhom(date_str: str):
    return _by_nhom(date_str, "so_du_irs_binh_quan")


@_df_cache()
def so_du_hdls_binh_quan_by_nhom(date_str: str):
    """Combined CCS+IRS số dư HĐLS bình quân — summed from the two sub-product columns, same
    reasoning as so_du_hdls_ngay_by_nhom (not read off a separate combined column)."""
    return so_du_ccs_binh_quan_by_nhom(date_str).add(so_du_irs_binh_quan_by_nhom(date_str), fill_value=0.0)


if __name__ == "__main__":
    d = latest_date()
    print("Số dư HĐLS ngày (Tất cả):\n", so_du_hdls_ngay_by_nhom(d))
    print("Số dư CCS ngày:\n", so_du_ccs_ngay_by_nhom(d))
    print("Số dư IRS ngày:\n", so_du_irs_ngay_by_nhom(d))
    print("Số dư HĐLS bình quân (Tất cả):\n", so_du_hdls_binh_quan_by_nhom(d))
    print("Số dư CCS bình quân:\n", so_du_ccs_binh_quan_by_nhom(d))
    print("Số dư IRS bình quân:\n", so_du_irs_binh_quan_by_nhom(d))
