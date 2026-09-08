from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_mbnt_nhom_phu_trach
from calculations.date_table import latest_date

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def tong_ln_mbnt_ytd_by_nhom(date_str: str):
    df = pvkh_mbnt_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["sum_ln_mbnt_luy_ke_den_ngay_bc"].max()
    # exclude the source table's own pre-aggregated 'TOTAL' row to avoid double-counting
    total = by_group.drop(labels=["TOTAL"], errors="ignore").sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


if __name__ == "__main__":
    print(tong_ln_mbnt_ytd_by_nhom(latest_date()))
