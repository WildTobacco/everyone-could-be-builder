"""Python port of HoanThanh_KH_LN_VPV_Update. See hoanthanh_kh_ln_mbnt.py for the shared
gap/format logic this wraps."""

from data_connect.db_connect import _df_cache
from calculations.hoanthanh_kh_ln_mbnt import hoanthanh_kh_ln_mbnt


@_df_cache()
def hoanthanh_kh_ln_vpv(date_str: str) -> str | None:
    return hoanthanh_kh_ln_mbnt(date_str, "VPV")


if __name__ == "__main__":
    from calculations.date_table import latest_date

    print(hoanthanh_kh_ln_vpv(latest_date()))
