"""Python port of DS_HDLS_PTKD1_ngay (and its PTKD2/VPV/TOTAL siblings), from a different,
pre-existing dashboard's DAX (not this project's own Power BI model). Source table name
(pvkh_PSTC_Nhom_phu_trach_ngay -> bronze_baocaotudong.pvkh_pstc_nhom_phu_trach) and column
name (sum_DS_HDLS_ngay_bc -> sum_ds_hdls_ngay_bc) match this project's existing schema
directly, just different casing — no name-mapping judgment call needed here (unlike the
MBNT "KDNT" ports).

    CALCULATE(SUM(pvkh_PSTC_Nhom_phu_trach_ngay[sum_DS_HDLS_ngay_bc]), [Nhom_phu_trach] = "<X>")
"""

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_pstc_nhom_phu_trach
from calculations.date_table import latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def ds_hdls_ngay_by_nhom(date_str: str):
    """One row per nhóm already in the source table, so CALCULATE+SUM+filter is just that
    day's value for the matching Nhóm phụ trách row. TOTAL is read directly from the
    source's own pre-aggregated row, not recomputed by summing PTKD1+PTKD2+VPV.
    .max() (not .sum()) matches the defensive groupby already used for this table
    elsewhere in the project, in case of duplicate rows for a (nhóm, ngày) pair."""
    df = pvkh_pstc_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["sum_ds_hdls_ngay_bc"].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


if __name__ == "__main__":
    print(ds_hdls_ngay_by_nhom(latest_date()))
