from data_connect.db_connect import _df_cache
import pandas as pd
from data_connect.excel_connect import ke_hoach_theo_ptkd

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
SAN_PHAM = "LN KDNT&PS"


@_df_cache()
def _ke_hoach_by_group(month_value: str) -> pd.Series:
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == month_value)
    by_group = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = result.sum()
    return result


def compute_ht_thang_nam(kdntps: pd.Series, selected_date: str) -> pd.DataFrame:
    """kdntps: LN KDNTPS lũy kế by group (+TOTAL), from ln_luy_ke_kdntps_by_nhom.
    Returns a DataFrame indexed by group with ht_thang / ht_nam as fractions (0.971 = 97.1%)."""
    month_value = str(pd.to_datetime(selected_date).month)
    ke_hoach_thang = _ke_hoach_by_group(month_value)
    ke_hoach_nam = _ke_hoach_by_group("total")

    ht_thang = kdntps / ke_hoach_thang.replace(0, pd.NA)
    ht_nam = kdntps / ke_hoach_nam.replace(0, pd.NA)

    return pd.DataFrame({"ht_thang": ht_thang, "ht_nam": ht_nam})


if __name__ == "__main__":
    from ln_luy_ke_kdntps import ln_luy_ke_kdntps_by_nhom
    from date_table import latest_date

    date_str = latest_date()
    kdntps = ln_luy_ke_kdntps_by_nhom(date_str)
    kdntps["TOTAL"] = kdntps.reindex(GROUPS).sum()

    print(compute_ht_thang_nam(kdntps, date_str))
