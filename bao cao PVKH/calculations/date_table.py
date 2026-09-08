from data_connect.db_connect import _df_cache, _load_bao_cao_csv
import pandas as pd


def get_date_table() -> pd.DataFrame:
    """Distinct report dates (desc), each paired with its same-day-last-year date.

    Reads data/bao_cao_ket_qua_mbnt_2025_2026.csv — a static export of
    bao_cao_ket_qua_mbnt_2025_2026_view, not a live query. The base table this used to read
    batch-refreshes on its own schedule and stalled at 11/08 while bronze was already at 16/08;
    the view tracked the true latest date but recomputed from scratch on every call (27-235s
    observed) and querying it on every page load crashed the Flask dev server outright
    (2026-08-17) when its auto-reloader restarted mid-query. The CSV is instant and immune to
    both problems, at the cost of freshness: it only advances when the file is manually
    re-exported and replaced — see the comment above _load_bao_cao_csv in db_connect.py. Its
    ~30-day range is still well above DATE_OPTIONS_WORKING_DAYS's 10, so nothing here is
    starved for dates."""
    df = _load_bao_cao_csv("bao_cao_ket_qua_mbnt_2025_2026.csv")
    dates = df[["ngay"]].rename(columns={"ngay": "date"}).drop_duplicates()
    dates["date"] = pd.to_datetime(dates["date"])
    dates = dates.sort_values("date", ascending=False).reset_index(drop=True)
    dates["date_last_year"] = dates["date"] - pd.DateOffset(years=1)
    return dates


def latest_date() -> str:
    return get_date_table()["date"].iloc[0].strftime("%Y-%m-%d")


@_df_cache()
def same_day_last_year(date_str: str) -> str:
    return (pd.to_datetime(date_str) - pd.DateOffset(years=1)).strftime("%Y-%m-%d")


@_df_cache()
def previous_date(date_str: str) -> str | None:
    """The previous *trading* date before date_str, for day-over-day differencing.

    Weekend rows do exist in the date table (they repeat Friday's cumulative unchanged), so
    they are filtered out the same way the date dropdown filters them — otherwise a Monday
    would difference against Sunday. That yields the right number only as long as the weekend
    snapshot is a faithful copy of Friday's; a stale or partial weekend row would silently
    corrupt Monday's figure. Holidays need no special handling: they have no snapshot at all,
    so walking the table's own dates skips them.

    None when date_str is the earliest date on record."""
    dates = get_date_table()["date"]  # already sorted newest first
    dates = dates[dates.dt.dayofweek < 5]
    earlier = dates[dates < pd.to_datetime(date_str)]
    return None if earlier.empty else earlier.iloc[0].strftime("%Y-%m-%d")