from data_connect.db_connect import _df_cache
import pandas as pd
from data_connect.excel_connect import ke_hoach_theo_ptkd
from calculations.tong_ds_hdls_ytd_nhom import tong_ds_hdls_ytd_by_nhom

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
SAN_PHAM = "DS HDLS"


def _ke_hoach_ds_hdls_nam() -> pd.Series:
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == "total")
    by_group = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    total = by_group.get("Tổng", 0.0)  # table's own native Tổng row, not sum of the 3 groups
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def ke_hoach_ds_hdls_thang(month_value: str) -> pd.Series:
    """Same source/shape as _ke_hoach_ds_hdls_nam, but for a single month (e.g. "8" for
    August) instead of the annual total. Used by HoanThanh_KH_DS_hdls_*_Update's KH_Thang."""
    df = ke_hoach_theo_ptkd()
    mask = (df["san_pham"] == SAN_PHAM) & (df["month"] == month_value)
    by_group = df.loc[mask].groupby("nhom_phu_trach")["ke_hoach"].sum()
    total = by_group.get("Tổng", 0.0)
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def ds_hdls_hoan_thanh(date_str: str) -> pd.Series:
    """DS_HDLS_Hoan_Thanh: DIVIDE(tong_ds_hdls_ytd_nhom, annual KH), by nhom_phu_trach + TOTAL.
    Returned as a fraction (0.9756 == "97.56%"), not a formatted string."""
    ds_ytd = tong_ds_hdls_ytd_by_nhom(date_str)
    kh = _ke_hoach_ds_hdls_nam()
    return ds_ytd / kh.replace(0, pd.NA)


if __name__ == "__main__":
    d = "2026-08-10"
    result = ds_hdls_hoan_thanh(d)
    print(f"date: {d}")
    for key, val in result.items():
        print(f"{key}: HT năm: {val:.2%}" if pd.notna(val) else f"{key}: HT năm: n/a")
