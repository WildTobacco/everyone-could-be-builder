"""Python port of LN_HDLS_PTKD1_ngay (and its PTKD2/VPV/TOTAL siblings). See
ds_hdls_ngay_by_nhom.py for the source table/column naming note — same table, LN instead
of DS.

    CALCULATE(SUM(pvkh_PSTC_Nhom_phu_trach_ngay[sum_LN_HDLS_ngay_bc]), [Nhom_phu_trach] = "<X>")
"""

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_pstc_nhom_phu_trach
from calculations.date_table import latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def ln_hdls_ngay_by_nhom(date_str: str):
    df = pvkh_pstc_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["sum_ln_hdls_ngay_bc"].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


if __name__ == "__main__":
    print(ln_hdls_ngay_by_nhom(latest_date()))
