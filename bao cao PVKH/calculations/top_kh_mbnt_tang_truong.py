import pandas as pd
from data_connect.db_connect import bao_cao_ket_qua_mbnt_2025_2026

COL_GROWTH = "Tăng trưởng lợi nhuận (%)"
COL_LN_2025 = "Lợi nhuận 2025 (tr VND)"
LN_2025_THRESHOLD = 2000  # tr VND — matches bao_cao_ket_qua_mbnt_2025_2026_view's own
# WHERE COALESCE(y25.ln_tr_dong, 0) > 2000, applied explicitly here so the % growth ranking
# doesn't depend on the upstream data (view, or now a CSV export of it) already being filtered.
# % growth from a near-zero 2025 base is misleading (a jump to 100tr reads as +9900%), so this
# only gates the PERCENT ranking, not the absolute (▲LN) one — a small % of a large base can
# still be a materially large absolute figure and deserves to stay visible there.

COLUMN_RENAME = {
    "Tên khách hàng": "Tên khách hàng",
    "Chi nhánh": "Chi nhánh",
    "Cán bộ phụ trách": "Cán bộ phụ trách",
    "Lợi nhuận 2026 (tr VND)": "LN (tr VND)",
    "Tăng trưởng lợi nhuận (%)": "▲LN%",
    "Doanh số 2026 (tr USD)": "DS (tr USD)",
    "Tăng trưởng doanh số (%)": "▲DS%",
    "NIM 2026": "NIM",
    "Tăng trưởng NIM (%)": "▲NIM%",
}
OUTPUT_COLS = list(COLUMN_RENAME.keys())

COL_GROWTH_ABS = "Tăng trưởng lợi nhuận"

COLUMN_RENAME_ABS = {
    "Tên khách hàng": "Tên khách hàng",
    "Chi nhánh": "Chi nhánh",
    "Cán bộ phụ trách": "Cán bộ phụ trách",
    "Lợi nhuận 2026 (tr VND)": "LN (tr VND)",
    "Tăng trưởng lợi nhuận": "▲LN",
    "Doanh số 2026 (tr USD)": "DS (tr USD)",
    "Tăng trưởng doanh số": "▲DS",
    "NIM 2026": "NIM",
    "Tăng trưởng NIM": "▲NIM",
}
OUTPUT_COLS_ABS = list(COLUMN_RENAME_ABS.keys())

# Fixed, not derived from df["Nhóm phụ trách"].unique() — that dynamic form rendered an
# unintended "TSC" card once the raw data stopped being pre-filtered to LN 2025 > 2000 (every
# TSC-attributed row had happened to fall below that threshold, so TSC never appeared before).
# build_sections() in web_app.py renders one card per dict key with no group allowlist of its
# own, so an unexpected key here becomes an unexpected card on the page. Matches
# top_kh_hdls_tang_truong.py's ALL_GROUPS, which already used a fixed list for this reason.
ALL_GROUPS = ["PTKD 1", "PTKD 2", "VPV"]


TEXT_COLUMNS = {"Tên khách hàng", "Chi nhánh", "Cán bộ phụ trách"}


def _format_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Every column except the customer/branch/officer identifiers is a numeric value, displayed
    as a rounded whole number (###,###,###) in the Khách hàng tab's top/bottom ranking tables."""
    for col in df.columns:
        if col not in TEXT_COLUMNS:
            df[col] = df[col].map(lambda v: f"{v:,.0f}")
    return df


def _split_top_bottom(df_group: pd.DataFrame, col: str, output_cols: list, rename_map: dict, n: int = 5):
    """Top n: highest growth among positive-growth rows only.
    Bottom n: lowest growth among all rows (negatives included)."""
    top = df_group[df_group[col] > 0].sort_values(col, ascending=False).head(n)
    bottom = df_group.sort_values(col, ascending=True).head(n)

    top = _format_numeric_columns(top[output_cols].rename(columns=rename_map))
    bottom = _format_numeric_columns(bottom[output_cols].rename(columns=rename_map))
    return top, bottom


def _group_slice(df: pd.DataFrame, group: str) -> pd.DataFrame:
    """"Tất cả" pools every nhóm into one ranking (all customers competing together), not a
    per-nhóm table shown alongside the other three — the frontend used to just display every
    group's card at once when "Tất cả" was selected, which read as four separate tables rather
    than one combined ranking."""
    df_group = df if group == "Tất cả" else df[df["Nhóm phụ trách"] == group]
    return df_group.drop_duplicates(subset="bdscif")


def get_top_bottom_by_group(df: pd.DataFrame, n: int = 5):
    """Ranks each Nhóm phụ trách (plus a pooled "Tất cả") by Tăng trưởng lợi nhuận (%),
    restricted to customers whose 2025 lợi nhuận exceeds LN_2025_THRESHOLD — see the constant's
    comment for why."""
    results = {}
    for group in ALL_GROUPS + ["Tất cả"]:
        df_group = _group_slice(df, group)
        df_group = df_group[df_group[COL_LN_2025].fillna(0) > LN_2025_THRESHOLD]
        results[group] = _split_top_bottom(df_group, COL_GROWTH, OUTPUT_COLS, COLUMN_RENAME, n)
    return results


def get_top_bottom_by_group_abs(df: pd.DataFrame, n: int = 5):
    """Ranks each Nhóm phụ trách (plus a pooled "Tất cả") by Tăng trưởng lợi nhuận (absolute
    amount, not %)."""
    results = {}
    for group in ALL_GROUPS + ["Tất cả"]:
        df_group = _group_slice(df, group)
        results[group] = _split_top_bottom(df_group, COL_GROWTH_ABS, OUTPUT_COLS_ABS, COLUMN_RENAME_ABS, n)
    return results


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    from date_table import latest_date
    df = bao_cao_ket_qua_mbnt_2025_2026(latest_date())

    by_group_pct = get_top_bottom_by_group(df)
    for group, (top5, bottom5) in by_group_pct.items():
        print(f"\n=== {group} — Top 5 by {COL_GROWTH} ===")
        print(top5)
        print(f"\n=== {group} — Bottom 5 by {COL_GROWTH} ===")
        print(bottom5)

    by_group_abs = get_top_bottom_by_group_abs(df)
    for group, (top5, bottom5) in by_group_abs.items():
        print(f"\n=== {group} — Top 5 by {COL_GROWTH_ABS} ===")
        print(top5)
        print(f"\n=== {group} — Bottom 5 by {COL_GROWTH_ABS} ===")
        print(bottom5)