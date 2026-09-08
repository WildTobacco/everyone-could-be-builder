from data_connect.db_connect import _df_cache
from data_connect.db_connect import pvkh_kdntps_nhom_phu_trach
from calculations.date_table import latest_date


@_df_cache()
def ln_luy_ke_kdntps_by_nhom(date_str: str):
    df = pvkh_kdntps_nhom_phu_trach(date_str)
    return df.groupby("nhom_phu_trach")["sum_ln_kdntps_luy_ke"].max()


if __name__ == "__main__":
    print(ln_luy_ke_kdntps_by_nhom(latest_date()))