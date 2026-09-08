"""Trong ngày (single-day) PSHH by nhóm phụ trách + dia_ban + PKKH — pvkh_dailyreport already
carries nhom_phu_trach/dia_ban/pkkh natively on every row, so no join is needed at all here
(unlike the lũy kế DS TLHH/OTC, which comes from a different table needing a pkkh join — see
y_pshh_nhom_diaban_pkkh.py). ds_tlhh_ngay_bc/ds_otc_ngay_bc/ln_pshh_ngay_bc are that day's own
figure, not a cumulative one."""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_dailyreport

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _daily_by_nhom(value_col: str, date_str: str) -> pd.Series:
    df = pvkh_dailyreport(date_str)
    by_group = df.groupby("nhom_phu_trach")[value_col].sum()
    total = by_group.sum()  # includes every group present, not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def daily_ds_pshh_tlhh_by_nhom(date_str: str) -> pd.Series:
    return _daily_by_nhom("ds_tlhh_ngay_bc", date_str)


@_df_cache()
def daily_ds_pshh_otc_by_nhom(date_str: str) -> pd.Series:
    return _daily_by_nhom("ds_otc_ngay_bc", date_str)


@_df_cache()
def daily_ln_pshh_by_nhom(date_str: str) -> pd.Series:
    return _daily_by_nhom("ln_pshh_ngay_bc", date_str)


def _daily_by_nhom_dim(value_col: str, dim_col: str, output_col: str,
                        output_value_col: str, date_str: str) -> pd.DataFrame:
    df = pvkh_dailyreport(date_str)
    result = df.groupby(["nhom_phu_trach", dim_col])[value_col].sum().reset_index()
    result.columns = ["nhom_phu_trach", output_col, output_value_col]
    return result


@_df_cache()
def daily_ds_pshh_tlhh_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _daily_by_nhom_dim("ds_tlhh_ngay_bc", "dia_ban", "dia_ban", "doanh_so", date_str)


@_df_cache()
def daily_ds_pshh_tlhh_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _daily_by_nhom_dim("ds_tlhh_ngay_bc", "pkkh", "pkkh", "doanh_so", date_str)


@_df_cache()
def daily_ds_pshh_otc_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _daily_by_nhom_dim("ds_otc_ngay_bc", "dia_ban", "dia_ban", "doanh_so", date_str)


@_df_cache()
def daily_ds_pshh_otc_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _daily_by_nhom_dim("ds_otc_ngay_bc", "pkkh", "pkkh", "doanh_so", date_str)


@_df_cache()
def daily_ln_pshh_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _daily_by_nhom_dim("ln_pshh_ngay_bc", "dia_ban", "dia_ban", "loi_nhuan", date_str)


@_df_cache()
def daily_ln_pshh_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _daily_by_nhom_dim("ln_pshh_ngay_bc", "pkkh", "pkkh", "loi_nhuan", date_str)


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("Daily DS TLHH by nhom:\n", daily_ds_pshh_tlhh_by_nhom(d))
    print("Daily DS OTC by nhom:\n", daily_ds_pshh_otc_by_nhom(d))
    print("Daily LN by nhom:\n", daily_ln_pshh_by_nhom(d))
    print("Daily LN by pkkh:\n", daily_ln_pshh_by_nhom_pkkh(d).to_string())
