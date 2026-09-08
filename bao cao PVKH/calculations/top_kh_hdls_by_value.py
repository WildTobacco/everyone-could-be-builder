"""Top 10 KH by raw Doanh số / Lợi nhuận value (not growth) — same table shape and per-nhóm
+ "Tất cả" pooling as top_kh_hdls_tang_truong.py, just ranked by the 2026 value itself instead
of tăng trưởng, and with no LN-2025 threshold (that gate only makes sense for the % growth
ranking, not a plain value ranking)."""

import pandas as pd

COL_LN = "Lợi nhuận 2026 (tr VND)"
COL_DS = "Doanh số 2026 (tr USD)"

COLUMN_RENAME = {
    "Tên khách hàng": "Tên khách hàng",
    "Chi nhánh": "Chi nhánh",
    "Cán bộ phụ trách": "Cán bộ phụ trách",
    "Lợi nhuận 2026 (tr VND)": "LN (tr VND)",
    "Tăng trưởng lợi nhuận (%)": "▲LN%",
    "Doanh số 2026 (tr USD)": "DS (tr USD)",
    "Tăng trưởng doanh số (%)": "▲DS%",
    "Số dư IRS bình quân năm": "Số dư IRS BQ",
    "Số dư CCS bình quân năm": "Số dư CCS BQ",
}
OUTPUT_COLS = list(COLUMN_RENAME.keys())

TEXT_COLUMNS = {"Tên khách hàng", "Chi nhánh", "Cán bộ phụ trách"}

ALL_GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
# Raw Số dư values are absolute VND, not the tr-VND/tr-USD scale the rest of the table uses —
# scale down to match before display.
SODU_COLUMNS = {"Số dư IRS BQ", "Số dư CCS BQ"}


def _format_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in SODU_COLUMNS:
        if col in df.columns:
            df[col] = df[col] / 1_000_000
    for col in df.columns:
        if col not in TEXT_COLUMNS:
            df[col] = df[col].map(lambda v: f"{v:,.0f}")
    return df


def _group_slice(df: pd.DataFrame, group: str) -> pd.DataFrame:
    df_group = df if group == "Tất cả" else df[df["Nhóm phụ trách"] == group]
    df_group = df_group[df_group["Tên khách hàng"].notna()]
    return df_group.drop_duplicates(subset="bdscif")


def _split_top_bottom(df_group: pd.DataFrame, col: str, n: int = 10):
    top = df_group.sort_values(col, ascending=False).head(n)
    bottom = df_group.sort_values(col, ascending=True).head(n)

    top = _format_numeric_columns(top[OUTPUT_COLS].rename(columns=COLUMN_RENAME))
    bottom = _format_numeric_columns(bottom[OUTPUT_COLS].rename(columns=COLUMN_RENAME))
    return top, bottom


def get_top_bottom_by_group_ds(df: pd.DataFrame, n: int = 10):
    """Ranks each Nhóm phụ trách (plus a pooled "Tất cả") by Doanh số 2026 (tr USD)."""
    return {group: _split_top_bottom(_group_slice(df, group), COL_DS, n) for group in ALL_GROUPS + ["Tất cả"]}


def get_top_bottom_by_group_ln(df: pd.DataFrame, n: int = 10):
    """Ranks each Nhóm phụ trách (plus a pooled "Tất cả") by Lợi nhuận 2026 (tr VND)."""
    return {group: _split_top_bottom(_group_slice(df, group), COL_LN, n) for group in ALL_GROUPS + ["Tất cả"]}


# ---- Trong ngày (single-day) variant ----
# No growth-%/Số dư columns here — a single day's own DS/LN has no "so với 2025" baseline to
# grow from, and Số dư bình quân năm is a year-long average, not something a single day differs
# meaningfully against — so both simply don't apply to this leaner table.
IDENTITY_COLUMNS = ["bdscif", "Tên khách hàng", "Chi nhánh", "Cán bộ phụ trách", "Nhóm phụ trách"]
COLUMN_RENAME_DAILY = {
    "Tên khách hàng": "Tên khách hàng",
    "Chi nhánh": "Chi nhánh",
    "Cán bộ phụ trách": "Cán bộ phụ trách",
    "Lợi nhuận 2026 (tr VND)": "LN (tr VND)",
    "Doanh số 2026 (tr USD)": "DS (tr USD)",
}
OUTPUT_COLS_DAILY = list(COLUMN_RENAME_DAILY.keys())


def daily_customer_df(df_today: pd.DataFrame, df_yesterday: pd.DataFrame | None) -> pd.DataFrame:
    """Per-customer trong-ngày DS/LN: today's lũy kế minus yesterday's, joined on bdscif — same
    cumulative(d) - cumulative(previous report day) convention as daily_diaban_pkkh.py's _diff.
    A customer with no prior-day row (new today) keeps their whole today figure as the day's
    movement. A customer missing today (present only yesterday) ends up with a negative "day"
    value from the 0-fill and sorts to the bottom of a top-N-highest ranking on its own, so no
    separate filtering is needed for that edge case. df_yesterday is None at the earliest date
    on record, when there is nothing to difference against — the lũy kế figure is used as-is."""
    value_cols = [COL_DS, COL_LN]
    today = df_today[IDENTITY_COLUMNS + value_cols]
    if df_yesterday is None:
        return today.copy()

    yesterday = df_yesterday[IDENTITY_COLUMNS + value_cols]
    merged = pd.merge(today, yesterday, on="bdscif", how="outer", suffixes=("_t", "_y"))

    for col in value_cols:
        merged[col] = merged[f"{col}_t"].fillna(0.0) - merged[f"{col}_y"].fillna(0.0)
    for col in ["Tên khách hàng", "Chi nhánh", "Cán bộ phụ trách", "Nhóm phụ trách"]:
        merged[col] = merged[f"{col}_t"].fillna(merged[f"{col}_y"])

    return merged[IDENTITY_COLUMNS + value_cols]


def _split_top_bottom_daily(df_group: pd.DataFrame, col: str, n: int = 10):
    top = df_group.sort_values(col, ascending=False).head(n)
    bottom = df_group.sort_values(col, ascending=True).head(n)

    top = top[OUTPUT_COLS_DAILY].rename(columns=COLUMN_RENAME_DAILY)
    bottom = bottom[OUTPUT_COLS_DAILY].rename(columns=COLUMN_RENAME_DAILY)
    for frame in (top, bottom):
        for col_name in frame.columns:
            if col_name not in TEXT_COLUMNS:
                frame[col_name] = frame[col_name].map(lambda v: f"{v:,.2f}")
    return top, bottom


def get_top_bottom_by_group_ds_daily(daily_df: pd.DataFrame, n: int = 10):
    """Trong-ngày version of get_top_bottom_by_group_ds — ranks by that day's own Doanh số."""
    return {group: _split_top_bottom_daily(_group_slice(daily_df, group), COL_DS, n) for group in ALL_GROUPS + ["Tất cả"]}


def get_top_bottom_by_group_ln_daily(daily_df: pd.DataFrame, n: int = 10):
    """Trong-ngày version of get_top_bottom_by_group_ln — ranks by that day's own Lợi nhuận."""
    return {group: _split_top_bottom_daily(_group_slice(daily_df, group), COL_LN, n) for group in ALL_GROUPS + ["Tất cả"]}
