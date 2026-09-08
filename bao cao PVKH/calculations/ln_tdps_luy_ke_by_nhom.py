"""LN TDPS lũy kế (cumulative-to-date) by nhóm phụ trách, from
pvkh_pstc_nhom_phu_trach[sum_ln_tdps_luy_ke]. Same shape as tdps_ngay_by_nhom.py's daily
functions — one row per nhóm already exists in the source, so this is a straight lookup, and
TOTAL is read from the source's own pre-aggregated TOTAL row rather than recomputed.

Lợi nhuận only. The doanh số counterpart used to live here reading [sum_ds_tdps_luy_ke], but
that column is empty in the source; it now comes from pvkh_dsdaily_temp via ds_tdps.py."""

from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_pstc_nhom_phu_trach
from calculations.date_table import latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def ln_tdps_luy_ke_by_nhom(date_str: str):
    df = pvkh_pstc_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["sum_ln_tdps_luy_ke"].max()
    return by_group.reindex(GROUPS + ["TOTAL"], fill_value=0.0)


if __name__ == "__main__":
    print("LN TDPS lũy kế:\n", ln_tdps_luy_ke_by_nhom(latest_date()))
