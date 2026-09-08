import re
import pandas as pd

PTKD_PATH = r"\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC Dashboard PVKH ngày\Dữ liệu\KHKD PTKD 2026.xlsx"
CN_PATH = r"\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC Dashboard PVKH ngày\Dữ liệu\KHKD CN 2026.xlsx"
PL02_PATH = r"\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC Dashboard PVKH ngày\Dữ liệu\PL02 - KHKD Từng CN theo phân khúc và KQ thực hiện.xlsx"
CN_TRONG_DIEM_PATH = r"\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC Dashboard PVKH ngày\Dữ liệu\DS CN trọng điểm 2026.xlsx"

ANNUAL_COLUMNS = {
    "KH DS KDNT 2026 (TR USD)",
    "KH DS HĐLS 2026",
    "KH DS PSHH 2026",
    "KH LN KDNT 2026 (TR VND)",
    "KH LN HĐLS 2026",
    "KH LN TDPS 2026",
    "KH LN PSHH 2026",
    "KH KDNT&PS 2026",
}

REQUIRED_SUBSTRINGS = [
    "KH DS KDNT",
    "KH DS HĐLS",
    "KH DS PSHH",
    "KH LN KDNT",
    "KH LN HĐLS",
    "KH LN TDPS",
    "KH LN PSHH",
    "KH KDNT&PS",
]

INDICATOR_MAP = [
    ("KH DS KDNT", "DS MBNT"),
    ("KH DS HĐLS", "DS HDLS"),
    ("KH DS PSHH", "DS PSHH"),
    ("KH LN KDNT", "LN MBNT"),
    ("KH LN HĐLS", "LN HDLS"),
    ("KH LN TDPS", "LN TDPS"),
    ("KH LN PSHH", "LN PSHH"),
    ("KH KDNT&PS", "LN KDNT&PS"),
]

LISTBDS_COLUMNS = {
    "BDS": "bds",
    "Chi_nhánh": "tencn",
    "Địa bàn": "diaban",
    "Nhóm phụ trách": "nhomphutrach",
    "Cán bộ phụ trách": "tencb",
}

KDNT_CB_COLUMNS = [f"CB T{i}" for i in range(1, 13)]
KDNT_REQUIRED_SUBSTRING = "KHKD KDNT"
KDNT_EXCLUDED_SUBSTRING = "KHKD KDNT&PS"


def clean_column_name(name) -> str:
    text = str(name)
    text = text.replace("\xa0", " ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    text = re.sub(r"[^\x20-\x7E\u00C0-\u1EF9]", " ", text)
    words = [w for w in text.split(" ") if w != ""]
    return " ".join(words).strip()


def get_month_number(column_name: str):
    clean_name = clean_column_name(column_name).upper()
    idx = clean_name.rfind(" T")
    if idx == -1:
        return None
    after = clean_name[idx + 2:]
    month_text = after.split(".")[0] if "." in after else after
    digits = re.sub(r"\D", "", month_text)
    if not digits:
        return None
    month_number = int(digits)
    return month_number if 1 <= month_number <= 12 else None


def is_annual_column(column_name: str) -> bool:
    return clean_column_name(column_name).upper() in ANNUAL_COLUMNS


def is_required_indicator(column_name: str) -> bool:
    clean_name = clean_column_name(column_name).upper()
    return any(sub in clean_name for sub in REQUIRED_SUBSTRINGS)


def is_required_column(column_name: str) -> bool:
    is_monthly = get_month_number(column_name) is not None
    is_annual = is_annual_column(column_name)
    return is_required_indicator(column_name) and (is_monthly or is_annual)


def compute_month(original_name: str):
    if is_annual_column(original_name):
        return "total"
    month_number = get_month_number(original_name)
    return str(month_number) if month_number is not None else None


def compute_month_sort(month_value):
    if month_value == "total":
        return 13
    try:
        return int(month_value)
    except (TypeError, ValueError):
        return None


def compute_indicator(original_name: str):
    clean_name = clean_column_name(original_name).upper()
    for substring, label in INDICATOR_MAP:
        if substring in clean_name:
            return label
    return None


def adjust_value(value, indicator):
    if pd.isna(value):
        return None
    if indicator.startswith("DS"):
        return value * 1_000_000
    if indicator.startswith("LN"):
        return value * 1_000_000_000
    return value


def ke_hoach_theo_ptkd(path: str = PTKD_PATH) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1")
    df.columns = [clean_column_name(c) for c in df.columns]
    df = df.drop(columns=["STT"], errors="ignore")
    df = df.iloc[:-7]

    columns_to_keep = [c for c in df.columns if c == "Nhóm phụ trách" or is_required_column(c)]
    df = df[columns_to_keep]

    numeric_columns = [c for c in df.columns if c != "Nhóm phụ trách"]
    df["Nhóm phụ trách"] = df["Nhóm phụ trách"].astype(str)
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[numeric_columns] = df[numeric_columns].fillna(0)

    df_long = df.melt(
        id_vars=["Nhóm phụ trách"],
        value_vars=numeric_columns,
        var_name="Original Column Name",
        value_name="Value",
    )

    df_long["Month"] = df_long["Original Column Name"].apply(compute_month)
    df_long["Month Sort"] = df_long["Month"].apply(compute_month_sort)
    df_long["Indicator"] = df_long["Original Column Name"].apply(compute_indicator)

    df_long = df_long[df_long["Indicator"].notna() & df_long["Month"].notna()]

    df_long["Adjusted Value"] = df_long.apply(
        lambda row: adjust_value(row["Value"], row["Indicator"]), axis=1
    )

    df_long = df_long.drop(columns=["Original Column Name", "Value"])
    df_long = df_long.rename(columns={
        "Nhóm phụ trách": "nhom_phu_trach",
        "Month": "month",
        "Indicator": "san_pham",
        "Adjusted Value": "ke_hoach",
        "Month Sort": "month_sort",
    })
    df_long = df_long[["nhom_phu_trach", "month", "san_pham", "ke_hoach", "month_sort"]]

    df_long = df_long.sort_values(by=["nhom_phu_trach", "month_sort", "san_pham"]).reset_index(drop=True)
    return df_long.drop(columns=["month_sort"])


def listbds(path: str = CN_PATH) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1")
    df = df[list(LISTBDS_COLUMNS.keys())].rename(columns=LISTBDS_COLUMNS)
    df["bds"] = pd.to_numeric(df["bds"], errors="coerce").astype("Int64")
    for col in ["tencn", "diaban", "nhomphutrach", "tencb"]:
        df[col] = df[col].astype(str)
    return df


def CN_trong_diem(path: str = CN_TRONG_DIEM_PATH) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1")
    df["STT"] = pd.to_numeric(df["STT"], errors="coerce").astype("Int64")
    df["BDS"] = pd.to_numeric(df["BDS"], errors="coerce").astype("Int64")
    for col in ["Chi nhánh", "Nhóm phụ trách", "Cán bộ phụ trách"]:
        df[col] = df[col].astype(str)
    df["Chi nhánh"] = df["Chi nhánh"].str.upper()
    return df


KHKD_CN_TEXT_COLUMNS = ["Chi nhánh", "Địa bàn", "Nhóm phụ trách", "Cán bộ phụ trách"]


def khkd_cn_ht(path: str = CN_PATH) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sheet1")
    df.columns = [clean_column_name(c) for c in df.columns]
    df["STT"] = pd.to_numeric(df["STT"], errors="coerce").astype("Int64")
    df["BDS"] = pd.to_numeric(df["BDS"], errors="coerce").astype("Int64")
    for col in KHKD_CN_TEXT_COLUMNS:
        df[col] = df[col].astype(str)
    for col in [c for c in df.columns if c.startswith("KHKD")]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def khkd_cn_td(path: str = CN_PATH) -> pd.DataFrame:
    return khkd_cn_ht(path).iloc[:-15].reset_index(drop=True)


def _khkdcn_by_nhom_phu_trach_2026(
    required_substring: str, value_col: str, path: str = CN_PATH, excluded_substring: str = None,
) -> pd.DataFrame:
    """Branch(BDS)-level KHKD CN 2026 monthly plan, melted to (BDS, Nhóm phụ trách, Month,
    value_col). One column set per sản phẩm ("KHKD KDNT"/"KHKD HĐLS"/"KHKD TDPS"/... T1..T12),
    shared by khkdcn_mbnt_nhom_phu_trach_2026 and its HĐLS/TDPS siblings — only the substring
    (and, for KDNT alone, the "KDNT&PS" collision it needs to exclude) differs per product."""
    df = pd.read_excel(path, sheet_name="Sheet1")
    df.columns = [clean_column_name(c) for c in df.columns]
    df = df.drop(columns=KDNT_CB_COLUMNS, errors="ignore")

    columns_to_keep = [
        c for c in df.columns
        if c in ("BDS", "Nhóm phụ trách")
        or (
            required_substring in c
            and (excluded_substring is None or excluded_substring not in c)
            and get_month_number(c) is not None
        )
    ]
    df = df[columns_to_keep]

    value_cols = [c for c in df.columns if c not in ("BDS", "Nhóm phụ trách")]
    df_long = df.melt(
        id_vars=["BDS", "Nhóm phụ trách"], value_vars=value_cols,
        var_name="Attribute", value_name=value_col,
    )
    df_long["Month"] = df_long["Attribute"].apply(get_month_number)
    df_long = df_long.drop(columns=["Attribute"])
    df_long[value_col] = pd.to_numeric(df_long[value_col], errors="coerce") * 1_000_000
    df_long["BDS"] = pd.to_numeric(df_long["BDS"], errors="coerce").astype("Int64")
    return df_long


def khkdcn_mbnt_nhom_phu_trach_2026(path: str = CN_PATH) -> pd.DataFrame:
    return _khkdcn_by_nhom_phu_trach_2026(
        KDNT_REQUIRED_SUBSTRING, "KHKD KDNT", path, KDNT_EXCLUDED_SUBSTRING
    )


def khkdcn_hdls_nhom_phu_trach_2026(path: str = CN_PATH) -> pd.DataFrame:
    return _khkdcn_by_nhom_phu_trach_2026("KHKD HĐLS", "KHKD HDLS", path)


def khkdcn_tdps_nhom_phu_trach_2026(path: str = CN_PATH) -> pd.DataFrame:
    return _khkdcn_by_nhom_phu_trach_2026("KHKD TDPS", "KHKD TDPS", path)


def ke_hoach_ds_mbnt_pkkh_2026(path: str = PL02_PATH) -> pd.DataFrame:
    """Same sheet/layout as ke_hoach_ln_mbnt_pkkh_2026 below, just the "KẾ HOẠCH DOANH SỐ NĂM"
    block (B2:F8) instead of "KẾ HOẠCH LỢI NHUẬN NĂM" (B10:F16) — header row "PHÂN KHÚC, Toàn
    hệ thống, PTKD1, PTKD2, VPV" then 6 phân khúc rows (KHDNL/Midcom/FDI/SME+SSME/Cá nhân/ĐCTC).

    This block's header reads "(tỷ USD)", not "(tỷ đồng)" like the LN block — but that's not a
    unit mismatch to correct for: MBNT's Doanh số is USD-denominated everywhere in this
    dashboard already (silver_pvkh_DL_KH_luy_ke's own ds_mbnt_luy_ke_den_ngay_bc is raw USD, same
    convention noted in ds_ln_pshh.py for PSHH's Doanh số), so "tỷ USD" -> USD takes the exact
    same ×1_000_000_000 as "tỷ đồng" -> VND takes for LN below."""
    raw = pd.read_excel(path, sheet_name="So với Kế hoạch", header=None)
    raw = raw.iloc[1:8]
    raw = raw.iloc[:, 1:6]
    raw.columns = raw.iloc[0]
    df = raw.iloc[1:].reset_index(drop=True)
    df.columns = [clean_column_name(c) for c in df.columns]

    for col in ["Toàn hệ thống", "PTKD1", "PTKD2", "VPV"]:
        df[col] = pd.to_numeric(df[col], errors="coerce") * 1_000_000_000

    df["PHÂN KHÚC"] = df["PHÂN KHÚC"].astype(str)
    df["PHÂN KHÚC"] = df["PHÂN KHÚC"].str.replace("Midcom", "MIDCOM", regex=False)
    df["PHÂN KHÚC"] = df["PHÂN KHÚC"].str.replace("SME+SSME", "SME", regex=False)

    df = df.rename(columns={
        "PHÂN KHÚC": "ten_pkkh",
        "Toàn hệ thống": "THT",
        "PTKD1": "PTKD 1",
        "PTKD2": "PTKD 2",
    })
    df["ten_pkkh"] = df["ten_pkkh"].str.replace("ĐCTC", "DCTC", regex=False)

    df_long = df.melt(
        id_vars=["ten_pkkh"], value_vars=["THT", "PTKD 1", "PTKD 2", "VPV"],
        var_name="nhom_phu_trach", value_name="ke_hoach_ds_mbnt",
    )
    df_long["ten_pkkh"] = df_long["ten_pkkh"].str.replace("Cá nhân", "KHCN", regex=False)
    return df_long


def ke_hoach_ln_mbnt_pkkh_2026(path: str = PL02_PATH) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="So với Kế hoạch", header=None)
    raw = raw.iloc[9:]
    raw = raw.iloc[: len(raw) - 174]
    raw = raw.iloc[:, 1:6]
    raw.columns = raw.iloc[0]
    df = raw.iloc[1:].reset_index(drop=True)
    df.columns = [clean_column_name(c) for c in df.columns]

    for col in ["Toàn hệ thống", "PTKD1", "PTKD2", "VPV"]:
        df[col] = pd.to_numeric(df[col], errors="coerce") * 1_000_000_000

    df["PHÂN KHÚC"] = df["PHÂN KHÚC"].astype(str)
    df["PHÂN KHÚC"] = df["PHÂN KHÚC"].str.replace("Midcom", "MIDCOM", regex=False)
    df["PHÂN KHÚC"] = df["PHÂN KHÚC"].str.replace("SME+SSME", "SME", regex=False)

    df = df.rename(columns={
        "PHÂN KHÚC": "ten_pkkh",
        "Toàn hệ thống": "THT",
        "PTKD1": "PTKD 1",
        "PTKD2": "PTKD 2",
    })
    df["ten_pkkh"] = df["ten_pkkh"].str.replace("ĐCTC", "DCTC", regex=False)

    # Manual correction, per user: PTKD 2's DCTC plan is overstated by 110bn. THT is its own
    # independent column in this sheet (not a recomputed sum of PTKD1/2/VPV), so it needs the
    # same 110bn deducted separately or it would still reflect the overstated PTKD 2 figure.
    dctc_mask = df["ten_pkkh"] == "DCTC"
    df.loc[dctc_mask, "PTKD 2"] -= 110_000_000_000
    df.loc[dctc_mask, "THT"] -= 110_000_000_000

    df_long = df.melt(
        id_vars=["ten_pkkh"], value_vars=["THT", "PTKD 1", "PTKD 2", "VPV"],
        var_name="nhom_phu_trach", value_name="ke_hoach_ln_mbnt",
    )
    df_long["ten_pkkh"] = df_long["ten_pkkh"].str.replace("Cá nhân", "KHCN", regex=False)
    return df_long


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    ptkd = ke_hoach_theo_ptkd()
    print(ptkd.head(10))
    print(f"ke_hoach_theo_ptkd rows: {len(ptkd)}\n")

    cn = listbds()
    print(cn.head(10))
    print(f"listbds rows: {len(cn)}")