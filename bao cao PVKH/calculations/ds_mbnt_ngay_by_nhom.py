"""Python port of DS_MBNT_PTKD1_update / DS_MBNT_PTKD2_update / DS_MBNT_VPV_update /
DS_MBNT_HT_update, from a different, pre-existing dashboard's DAX (not this project's
own Power BI model) — its table/column names don't necessarily match this project's
Postgres schema. Ported against the equivalent bronze_baocaotudong.pvkh_mbnt_nhom_phu_trach
columns instead: pvkh_MBNT_Nhom_phu_trach_ngay[sum_DS_MBNT_ngay_bc] -> sum_ds_mbnt_ngay_bc,
[Nhom_phu_trach] -> nhom_phu_trach (verified identical values, just different casing).

    CALCULATE(SUM(pvkh_MBNT_Nhom_phu_trach_ngay[sum_DS_MBNT_ngay_bc]), [Nhom_phu_trach] = "<X>")
"""

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_mbnt_nhom_phu_trach
from calculations.date_table import latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def ds_mbnt_ngay_by_nhom(date_str: str):
    """One row per nhóm already in the source table, so CALCULATE+SUM+filter is just that
    day's value for the matching Nhóm phụ trách row. HT/TOTAL is read directly from the
    source's own pre-aggregated 'TOTAL' row (per the DAX), not recomputed by summing
    PTKD1+PTKD2+VPV like tong_ds_mbnt_ytd_by_nhom does for the YTD/lũy kế measure.
    .max() (not .sum()) matches the defensive groupby already used for this same table
    in tong_ds_mbnt_ytd.py, in case of duplicate rows for a (nhóm, ngày) pair."""
    df = pvkh_mbnt_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["sum_ds_mbnt_ngay_bc"].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


if __name__ == "__main__":
    print(ds_mbnt_ngay_by_nhom(latest_date()))
