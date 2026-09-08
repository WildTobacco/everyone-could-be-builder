from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_pstc_nhom_phu_trach

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


@_df_cache()
def tong_ds_hdls_ytd_by_nhom(date_str: str):
    """Tong_DS_HDLS_YTD_Nhom: MAX(pvkh_pstc_nhom_phu_trach[sum_ds_hdls_luy_ke]) at the latest
    available ngay within date_str's year (on or before date_str), grouped by nhom_phu_trach."""
    df = pvkh_pstc_nhom_phu_trach(date_str)
    by_group = df.groupby("nhom_phu_trach")["sum_ds_hdls_luy_ke"].max()
    total = by_group.get("TOTAL", 0.0)  # table's own native TOTAL row, not sum of the 3 groups
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


if __name__ == "__main__":
    from date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print(tong_ds_hdls_ytd_by_nhom(d))
