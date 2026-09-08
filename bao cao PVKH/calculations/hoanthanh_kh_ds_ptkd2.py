"""Python port of HoanThanh_KH_DS_PTKD2_Update. See hoanthanh_kh_ds_mbnt.py for the shared
gap/format logic this wraps."""

from data_connect.db_connect import _df_cache
from calculations.hoanthanh_kh_ds_mbnt import hoanthanh_kh_ds_mbnt


@_df_cache()
def hoanthanh_kh_ds_ptkd2(date_str: str) -> str | None:
    return hoanthanh_kh_ds_mbnt(date_str, "PTKD 2")


if __name__ == "__main__":
    from calculations.date_table import latest_date

    print(hoanthanh_kh_ds_ptkd2(latest_date()))
