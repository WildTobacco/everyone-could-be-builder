from data_connect.db_connect import _df_cache
import pandas as pd
from data_connect.excel_connect import ke_hoach_theo_ptkd

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
SAN_PHAM = "LN MBNT"


def ke_hoach_ln_mbnt_nam() -> pd.Series:
    """Annual (month='total') LN MBNT plan by nhom_phu_trach, + TOTAL."""
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == "total")
    result = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    result = result.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = result.sum()
    return result


@_df_cache()
def ke_hoach_ln_mbnt_thang(month_value: str) -> pd.Series:
    """Same source/shape as ke_hoach_ln_mbnt_nam, but for a single month (e.g. "8" for
    August) instead of the annual total. This is the lũy kế/cumulative-through-that-month
    figure (the source column itself is cumulative), not that month's own portion alone —
    see ke_hoach_ln_mbnt_thang_only for that."""
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == month_value)
    result = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    result = result.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = result.sum()
    return result


@_df_cache()
def ke_hoach_ln_mbnt_thang_only(month_value: str) -> pd.Series:
    """Non-cumulative: just the selected month's own LN MBNT plan portion, i.e. this
    month's cumulative KH minus the previous month's cumulative KH (month 1 has no
    previous month, so it's used as-is). For comparing against non-accumulative
    (single-day) actuals like LN_Current, instead of ke_hoach_ln_mbnt_thang's YTD figure."""
    month_num = int(month_value)
    current = ke_hoach_ln_mbnt_thang(month_value)
    if month_num == 1:
        return current
    return current - ke_hoach_ln_mbnt_thang(str(month_num - 1))


if __name__ == "__main__":
    print(ke_hoach_ln_mbnt_nam())
    print(ke_hoach_ln_mbnt_thang("8"))
    print(ke_hoach_ln_mbnt_thang_only("8"))
