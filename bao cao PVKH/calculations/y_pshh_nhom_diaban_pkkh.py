"""2026 PSHH (phái sinh hàng hóa) actuals by nhóm phụ trách + dia_ban + PKKH.

Doanh số stays split into TLHH (lots) and OTC (USD) throughout — see ds_ln_pshh.py's module
docstring for why summing them would mix incompatible units. Lợi nhuận is one VND figure with
no split.

DS TLHH/OTC come from pvkh_dsdaily_temp, which already carries nhom_phu_trach/dia_ban natively
(via its own bds->listbds() merge) but not pkkh — that join is added here the same way
_fx_or_pstc_merged does it for pvkh_fx/pvkh_pstc/pvkh_chiase/pvkh_pshh (cif->pvkh_listcif->
mapkkh->pvkh_pkkh).

Lợi nhuận comes from pvkh_dailyreport, which already carries nhom_phu_trach/dia_ban/pkkh
natively on every row — no join needed at all."""

import pandas as pd

from data_connect.db_connect import _df_cache, pvkh_dsdaily_temp, pvkh_dailyreport, pkkh_lookup
from calculations.ds_ln_pshh import _year_start

GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


def _pshh_ds_with_pkkh(date_str: str) -> pd.DataFrame:
    """pvkh_dsdaily_temp for the YTD window, with pkkh joined on via cif. Blank/unmatched cif
    (no CIF-based customer relationship — same situation as MBNT's "KH vang lai") falls back to
    a "Không xác định" placeholder rather than being silently dropped, same convention used for
    MBNT's own nhom_phu_trach gaps."""
    df = pvkh_dsdaily_temp(_year_start(date_str), date_str).copy()
    lookup = pkkh_lookup(date_str)
    df["cif"] = pd.to_numeric(df["cif"], errors="coerce").astype("Int64")
    lookup["cif"] = pd.to_numeric(lookup["cif"], errors="coerce").astype("Int64")
    df = df.merge(lookup, on="cif", how="left")
    df["pkkh"] = df["pkkh"].fillna("Không xác định")
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    df.loc[df["pkkh"] == "ME", "pkkh"] = "SME"
    return df


def _ds_by_nhom(value_col: str, date_str: str) -> pd.Series:
    df = pvkh_dsdaily_temp(_year_start(date_str), date_str)
    by_group = df.groupby("nhomphutrach")[value_col].sum()
    total = by_group.sum()  # includes every group present, not just GROUPS
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def ds_pshh_tlhh_by_nhom(date_str: str) -> pd.Series:
    return _ds_by_nhom("doanhsotlhh", date_str)


@_df_cache()
def ds_pshh_otc_by_nhom(date_str: str) -> pd.Series:
    return _ds_by_nhom("doanhsootc", date_str)


def _ds_by_nhom_dim(value_col: str, dim_col: str, output_col: str, date_str: str) -> pd.DataFrame:
    df = _pshh_ds_with_pkkh(date_str) if dim_col == "pkkh" else pvkh_dsdaily_temp(_year_start(date_str), date_str)
    result = df.groupby(["nhomphutrach", dim_col])[value_col].sum().reset_index()
    result.columns = ["nhom_phu_trach", output_col, "doanh_so"]
    return result


@_df_cache()
def ds_pshh_tlhh_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _ds_by_nhom_dim("doanhsotlhh", "diaban", "dia_ban", date_str)


@_df_cache()
def ds_pshh_tlhh_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _ds_by_nhom_dim("doanhsotlhh", "pkkh", "pkkh", date_str)


@_df_cache()
def ds_pshh_otc_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    return _ds_by_nhom_dim("doanhsootc", "diaban", "dia_ban", date_str)


@_df_cache()
def ds_pshh_otc_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    return _ds_by_nhom_dim("doanhsootc", "pkkh", "pkkh", date_str)


@_df_cache()
def ln_pshh_by_nhom(date_str: str) -> pd.Series:
    df = pvkh_dailyreport(date_str)
    by_group = df.groupby("nhom_phu_trach")["ln_pshh_theo_mpa_ytd"].sum()
    total = by_group.sum()
    result = by_group.reindex(GROUPS, fill_value=0.0)
    result["TOTAL"] = total
    return result


@_df_cache()
def ln_pshh_by_nhom_diaban(date_str: str) -> pd.DataFrame:
    df = pvkh_dailyreport(date_str)
    result = df.groupby(["nhom_phu_trach", "dia_ban"])["ln_pshh_theo_mpa_ytd"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "dia_ban", "loi_nhuan"]
    return result


@_df_cache()
def ln_pshh_by_nhom_pkkh(date_str: str) -> pd.DataFrame:
    df = pvkh_dailyreport(date_str)
    result = df.groupby(["nhom_phu_trach", "pkkh"])["ln_pshh_theo_mpa_ytd"].sum().reset_index()
    result.columns = ["nhom_phu_trach", "pkkh", "loi_nhuan"]
    return result


if __name__ == "__main__":
    from calculations.date_table import latest_date

    d = latest_date()
    print(f"date: {d}")
    print("DS TLHH by nhom:\n", ds_pshh_tlhh_by_nhom(d))
    print("DS OTC by nhom:\n", ds_pshh_otc_by_nhom(d))
    print("LN by nhom:\n", ln_pshh_by_nhom(d))
    print("DS TLHH by dia_ban:\n", ds_pshh_tlhh_by_nhom_diaban(d).to_string())
    print("DS TLHH by pkkh:\n", ds_pshh_tlhh_by_nhom_pkkh(d).to_string())
    print("LN by pkkh:\n", ln_pshh_by_nhom_pkkh(d).to_string())
