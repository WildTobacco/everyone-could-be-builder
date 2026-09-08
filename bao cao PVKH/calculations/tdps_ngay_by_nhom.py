"""Daily (non-accumulative) LN and số dư for TDPS — tín dụng phái sinh — by nhóm phụ trách,
from pvkh_pstc_nhom_phu_trach's sum_ln_tdps_ngay_bc / sum_so_du_tdps_ngay_bc.

Same shape as ds_mbnt_ngay_by_nhom.py / ds_hdls_ngay_by_nhom.py: one row per nhóm already
exists in the source, so a CALCULATE+SUM filtered to one nhóm is just that day's value.
TOTAL is read from the source's own pre-aggregated TOTAL row rather than recomputed.

No doanh số here: [sum_ds_tdps_ngay_bc] is empty in the source, so DS TDPS comes from
pvkh_dsdaily_temp via ds_tdps.py instead.
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
def ln_tdps_ngay_by_nhom(date_str: str):
    return _by_nhom(date_str, "sum_ln_tdps_ngay_bc")


@_df_cache()
def so_du_tdps_ngay_by_nhom(date_str: str):
    """Số dư (outstanding balance) TDPS on the selected day."""
    return _by_nhom(date_str, "sum_so_du_tdps_ngay_bc")


@_df_cache()
def so_du_tdps_binh_quan_by_nhom(date_str: str):
    """Số dư (outstanding balance) TDPS bình quân (YTD average) — same source table/column as
    nim_tdps_binh_quan_nhom.py's denominator."""
    return _by_nhom(date_str, "so_du_tdps_binh_quan")


@_df_cache()
def so_du_irs_binh_quan_by_nhom(date_str: str):
    """Số dư IRS bình quân (YTD average) — the IRS half of so_du_tdps_binh_quan_by_nhom's total
    (TDPS = IRS + CCS)."""
    return _by_nhom(date_str, "so_du_irs_binh_quan")


@_df_cache()
def so_du_ccs_binh_quan_by_nhom(date_str: str):
    """Số dư CCS bình quân (YTD average) — the CCS half of so_du_tdps_binh_quan_by_nhom's total
    (TDPS = IRS + CCS)."""
    return _by_nhom(date_str, "so_du_ccs_binh_quan")


if __name__ == "__main__":
    d = latest_date()
    print("LN TDPS:\n", ln_tdps_ngay_by_nhom(d))
    print("Số dư TDPS:\n", so_du_tdps_ngay_by_nhom(d))
