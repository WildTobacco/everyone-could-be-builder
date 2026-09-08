import functools
import os
import warnings
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from data_connect.excel_connect import listbds

load_dotenv()

# Every read_sql call here uses a raw psycopg2 connection (not a SQLAlchemy engine), which
# pandas warns about on every single call — this codebase has always talked to Postgres this
# way and it works fine; the warning is just noise that buries real errors in the logs.
warnings.filterwarnings(
    "ignore", message="pandas only supports SQLAlchemy connectable.*", category=UserWarning
)


def _df_cache(maxsize=64):
    """Like functools.lru_cache, but for functions returning pandas objects: hands back a
    fresh .copy() on every call so callers are free to mutate their result in place without
    corrupting the cached original. Every calculations/ module calls these DB-fetch functions
    directly (no shared inter-module cache), so the same date's raw table gets re-queried from
    Postgres many times over on a single page render.

    Series are copied as well as DataFrames — plenty of the by-nhóm measures return a Series,
    and handing the cached object back by reference would let one caller's in-place edit leak
    into every later reader.

    Note lru_cache hashes every argument, so only apply this to functions whose parameters are
    all hashable (str dates, Timestamps). A `group_cols` list argument raises TypeError."""
    def decorator(func):
        cached = functools.lru_cache(maxsize=maxsize)(func)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = cached(*args, **kwargs)
            return result.copy() if isinstance(result, (pd.DataFrame, pd.Series)) else result
        wrapper.cache_clear = cached.cache_clear
        return wrapper
    return decorator


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


# MBNT view's own output column names, as of the 2026-08-17 session — mapped back to the
# display-style names the rest of the codebase (top_kh_mbnt_tang_truong.py etc.) hardcodes.
# The view had display-style names ("Ngày", "Tên khách hàng", ...) earlier the same session
# and was rewritten mid-session to plain snake_case; kept as an explicit table (not a smart
# transform) so a future rename is a one-line fix here instead of a silent KeyError downstream.
_MBNT_VIEW_COLUMN_MAP = {
    "ngay": "Ngày",
    "ten_khach_hang": "Tên khách hàng",
    "loi_nhuan_2026_tr_vnd": "Lợi nhuận 2026 (tr VND)",
    "loi_nhuan_2025_tr_vnd": "Lợi nhuận 2025 (tr VND)",
    "tang_truong_loi_nhuan": "Tăng trưởng lợi nhuận",
    "tang_truong_loi_nhuan_pct": "Tăng trưởng lợi nhuận (%)",
    "doanh_so_2026_tr_usd": "Doanh số 2026 (tr USD)",
    "doanh_so_2025_tr_usd": "Doanh số 2025 (tr USD)",
    "tang_truong_doanh_so": "Tăng trưởng doanh số",
    "tang_truong_doanh_so_pct": "Tăng trưởng doanh số (%)",
    "nim_2026": "NIM 2026",
    "nim_2025": "NIM 2025",
    "tang_truong_nim": "Tăng trưởng NIM",
    "tang_truong_nim_pct": "Tăng trưởng NIM (%)",
}

# HDLS view's own output column names as of the 2026-08-17 17:37 export — until then it had
# kept the full display-style schema (including Chi nhánh/Nhóm phụ trách/Cán bộ phụ trách)
# while MBNT's had already been rewritten to snake_case; this export shows HDLS has now had the
# same rewrite applied, dropping those three enrichment columns too. Same shape as
# _MBNT_VIEW_COLUMN_MAP, kept as its own explicit table since the two views' column sets aren't
# identical (no NIM here; Số dư IRS/CCS bình quân instead).
_HDLS_VIEW_COLUMN_MAP = {
    "ngay": "Ngày",
    "ten_khach_hang": "Tên khách hàng",
    "phan_khuc_khach_hang": "Phân khúc khách hàng",
    "loi_nhuan_2026_tr_vnd": "Lợi nhuận 2026 (tr VND)",
    "loi_nhuan_2025_tr_vnd": "Lợi nhuận 2025 (tr VND)",
    "tang_truong_loi_nhuan": "Tăng trưởng lợi nhuận",
    "tang_truong_loi_nhuan_pct": "Tăng trưởng lợi nhuận (%)",
    "doanh_so_2026_tr_usd": "Doanh số 2026 (tr USD)",
    "doanh_so_2025_tr_usd": "Doanh số 2025 (tr USD)",
    "tang_truong_doanh_so": "Tăng trưởng doanh số",
    "tang_truong_doanh_so_pct": "Tăng trưởng doanh số (%)",
    "so_du_irs_binh_quan_nam": "Số dư IRS bình quân năm",
    "so_du_ccs_binh_quan_nam": "Số dư CCS bình quân năm",
}


# Static snapshots of bao_cao_ket_qua_mbnt/hdls_2025_2026_view, not a live DB query. The views
# themselves recompute from scratch on every call (a rolling 30-day window, cross-joined against
# a full year of customer×month history for the Y-1 approximation) and took 27-235s per fetch,
# with `latest_date()` alone hitting this on every single page load — that combination crashed
# the Flask dev server outright once (2026-08-17) when its auto-reloader restarted mid-query.
# A local file read is near-instant and immune to the view's own instability (its column names
# changed shape twice earlier this session), at the cost of freshness. Originally pointed at a
# manually re-exported copy in this project's own data/ folder, which went stale (stuck at
# 2026-08-31 while the live tables had already reached 2026-09-03) — switched to read the network
# share directly instead, where whatever process keeps these CSVs current writes them, so this
# path no longer needs a manual copy-in step to move forward.
_CSV_DIR = r"\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC PTKD\SQL"


@functools.lru_cache(maxsize=4)
def _load_bao_cao_csv(filename: str) -> pd.DataFrame:
    # Both exports carry a large block of rows with every identifying column (ngay/bds/cif/tên
    # khách hàng) null — the Y-1 side of the view's FULL JOIN with no 2026-side match on any
    # date. 23-24% of the 2026-08-17 17:35/17:37 exports were this (167k of 703k rows for
    # MBNT). They can never match a date_str filter so they're harmless, but they're pure
    # waste to hold in memory and are exactly why pandas raises a DtypeWarning on load (the
    # cif/ngay columns mix real values with NaN). Dropped here once, at load time, rather than
    # re-filtered out of every date's fetch.
    df = pd.read_csv(os.path.join(_CSV_DIR, filename), low_memory=False)
    date_col = next((c for c in ("Ngày", "ngay") if c in df.columns), None)
    return df.dropna(subset=[date_col]) if date_col else df


def _fetch_csv_for_date(filename: str, date_str: str) -> pd.DataFrame:
    df = _load_bao_cao_csv(filename).copy()
    date_col = next((c for c in ("Ngày", "ngay") if c in df.columns), None)
    if date_col is None:
        raise RuntimeError(f'{filename}: no "Ngày"/ngay column found in {list(df.columns)}.')
    return df[df[date_col] == date_str].copy()


def _enrich_customer_attributes(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    """Overwrites Chi nhánh / Nhóm phụ trách / Cán bộ phụ trách / Phân khúc khách hàng with
    independently-sourced lookups, instead of trusting whatever (if anything) the view/table
    itself supplies for them.

    The DB used to attach the first three via bronze_baocaotudong.customer_enrich_mapper, but
    the user dropped that table (2026-08-17); the MBNT view's 2026-08-17 rewrite dropped all
    four columns from its own output entirely. Re-deriving them here — listbds() for the first
    three (the same Excel-based bds -> {tencn, nhomphutrach, tencb} mapping every other measure
    in this codebase already merges) and pkkh_lookup() for phân khúc (cif -> pkkh, same as the
    TDPS dimension modules use) — makes the app independent of both sources' volatility.

    cán bộ phụ trách becomes bds-level (one per branch) rather than per-customer, since that is
    the only granularity listbds() has — consistent with how nhóm phụ trách is already handled
    everywhere else in this dashboard."""
    lb = listbds()[["bds", "tencn", "nhomphutrach", "tencb"]]
    df = df.drop(columns=["Chi nhánh", "Nhóm phụ trách", "Cán bộ phụ trách"], errors="ignore")
    df["bds"] = pd.to_numeric(df["bds"], errors="coerce").astype("Int64")
    df = df.merge(lb, on="bds", how="left")
    df = df.rename(columns={
        "tencn": "Chi nhánh", "nhomphutrach": "Nhóm phụ trách", "tencb": "Cán bộ phụ trách",
    })

    pkkh = pkkh_lookup(date_str)
    df = df.drop(columns=["Phân khúc khách hàng"], errors="ignore")
    df["cif"] = pd.to_numeric(df["cif"], errors="coerce").astype("Int64")
    pkkh["cif"] = pd.to_numeric(pkkh["cif"], errors="coerce").astype("Int64")
    df = df.merge(pkkh, on="cif", how="left")
    return df.rename(columns={"pkkh": "Phân khúc khách hàng"})


@_df_cache()
def bao_cao_ket_qua_mbnt_2025_2026(date_str: str) -> pd.DataFrame:
    """Reads data/bao_cao_ket_qua_mbnt_2025_2026.csv — see the module comment above
    _load_bao_cao_csv for why this isn't a live query. The CSV's own columns are the
    view's post-2026-08-17-rewrite snake_case names, missing Chi nhánh/Nhóm phụ trách/Cán bộ
    phụ trách/Phân khúc khách hàng entirely — renamed and re-enriched here the same way the
    live view fetch used to."""
    df = _fetch_csv_for_date("bao_cao_ket_qua_mbnt_2025_2026.csv", date_str)
    df = df.rename(columns=_MBNT_VIEW_COLUMN_MAP)
    df["bdscif"] = df["bds"].astype(str) + df["cif"].astype(str)
    return _enrich_customer_attributes(df, date_str)


@_df_cache()
def bao_cao_ket_qua_hdls_2025_2026(date_str: str) -> pd.DataFrame:
    """Reads data/bao_cao_ket_qua_hdls_2025_2026.csv — see bao_cao_ket_qua_mbnt_2025_2026 above.

    As of the 2026-08-17 17:37 export this CSV lost its Chi nhánh/Nhóm phụ trách/Cán bộ phụ
    trách columns too (earlier exports the same session had them fully populated per-customer,
    which is why this function used to skip enrichment entirely) — now renamed and re-enriched
    the same way MBNT's is. If a future export brings those columns back, this still works:
    _enrich_customer_attributes drops-then-rebuilds them unconditionally either way."""
    df = _fetch_csv_for_date("bao_cao_ket_qua_hdls_2025_2026.csv", date_str)
    df = df.rename(columns=_HDLS_VIEW_COLUMN_MAP)
    df["bdscif"] = df["bds"].astype(str) + df["cif"].astype(str)
    return _enrich_customer_attributes(df, date_str)


@_df_cache()
def _fx_or_pstc_merged(table: str, date_str: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT f.*, c.tenkh, c.mapkkh, p.tenpkkh AS pkkh
        FROM bronze_baocaotudong.{table} f
        LEFT JOIN (
            SELECT DISTINCT ON (cif) cif, mapkkh, tenkh
            FROM bronze_baocaotudong.pvkh_listcif
            WHERE EXTRACT(YEAR FROM monthyear) <= EXTRACT(YEAR FROM DATE '{date_str}')
            ORDER BY cif, monthyear DESC
        ) c ON f.cif = c.cif
        LEFT JOIN bronze_baocaotudong.pvkh_pkkh p
          ON c.mapkkh = p.mapkkh
        WHERE f.monthyear >= DATE_TRUNC('year', DATE '{date_str}')
          AND f.monthyear <= DATE '{date_str}';
        """,
        conn
    )
    conn.close()
    df.loc[df["pkkh"].str.contains("KHCN", na=False), "pkkh"] = "KHCN"
    return df.merge(listbds(), on="bds", how="left")


def pvkh_fx(date_str: str) -> pd.DataFrame:
    return _fx_or_pstc_merged("pvkh_fx", date_str)


def pvkh_pstc(date_str: str) -> pd.DataFrame:
    return _fx_or_pstc_merged("pvkh_pstc", date_str)


def pvkh_chiase(date_str: str) -> pd.DataFrame:
    return _fx_or_pstc_merged("pvkh_chiase", date_str)


def pvkh_pshh(date_str: str) -> pd.DataFrame:
    """Phái sinh hàng hóa (commodity derivatives) — sanpham is 'TLHH' or 'OTC', both counted
    as PSHH (there is no finer split in the KHKD plan, which only has one PSHH line). Same
    monthly-only shape as pvkh_pstc/pvkh_fx (no daily 2026 source), so both the 2026 actual and
    the Y-1 baseline go through the same Full + Partial × ProrationRatio approximation.

    Full dia_ban/nhom_phu_trach (via bds->listbds()) and pkkh (via cif->pvkh_listcif->mapkkh->
    pvkh_pkkh) — same shape as pvkh_fx/pvkh_pstc/pvkh_chiase. This module used to define
    pvkh_pshh twice: this version (delegating to _fx_or_pstc_merged, uncached) was silently
    shadowed by a second definition further down that only merged nhom_phu_trach (no dia_ban, no
    pkkh) — Python just keeps the last def of a given name — which is why a PSHH dia_ban/PKKH
    breakdown wasn't previously possible. Consolidated back into this one, correct definition."""
    return _fx_or_pstc_merged("pvkh_pshh", date_str)


@_df_cache()
def pvkh_dailyreport(date_str: str) -> pd.DataFrame:
    """One row per customer for a single report day, carrying nhom_phu_trach, dia_ban and pkkh
    on the row itself. The only customer-level source of số dư TDPS — every other so_du_tdps_*
    column in the warehouse sits on a pre-aggregated table (pvkh_pstc_dia_ban, _pkkh,
    _nhom_phu_trach) that holds one dimension each and so cannot be crossed with nhóm.

    Covers 2026 only (2026-01-01 onwards), so there is no Y-1 số dư to compare against."""
    conn = get_connection()
    df = pd.read_sql(
        f"SELECT * FROM bronze_baocaotudong.pvkh_dailyreport WHERE ngay = '{date_str}';",
        conn
    )
    conn.close()
    return df


@_df_cache()
def pvkh_dsdaily_temp(start_date: str, end_date: str) -> pd.DataFrame:
    """Daily, customer-level doanh số for TDPS / TLHH / OTC.

    Two things the schema hides: despite the name, `monthyear` holds a real transaction *date*
    (682 distinct values spanning 2024-01-02..2026-08-13, every day-of-month present), not a
    month start like every other pvkh_* table; and the figures are non-accumulative — one row
    is one day's business for a (bds, cif), so a period total is a plain SUM over the range.

    Covers 2026 only for reporting purposes — the 2025 TDPS doanh số baseline still comes from
    pvkh_pstc[doanhso] where sanpham='TDPS'. The two do track each other for 2025 (813.1M vs
    818.7M YTD to 11/08), but for 2026 pvkh_pstc is badly short (591.5M vs 2,180.4M), which is
    why the current-year measure was repointed here. See calculations/ds_tdps.py."""
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT * FROM bronze_baocaotudong.pvkh_dsdaily_temp
        WHERE monthyear >= DATE '{start_date}' AND monthyear <= DATE '{end_date}';
        """,
        conn
    )
    conn.close()
    df["monthyear"] = pd.to_datetime(df["monthyear"])
    df["bds"] = pd.to_numeric(df["bds"], errors="coerce").astype("Int64")
    return df.merge(listbds(), on="bds", how="left")


@_df_cache()
def pvkh_kdntps_nhom_phu_trach(date_str: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql(
        f"SELECT * FROM bronze_baocaotudong.pvkh_kdntps_nhom_phu_trach WHERE ngay = '{date_str}';",
        conn
    )
    conn.close()
    return df


@_df_cache()
def pvkh_pstc_nhom_phu_trach(date_str: str) -> pd.DataFrame:
    """Rows at the latest available ngay within date_str's year, on or before date_str
    (not necessarily date_str itself, in case that day has no snapshot yet)."""
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT * FROM bronze_baocaotudong.pvkh_pstc_nhom_phu_trach
        WHERE ngay = (
            SELECT MAX(ngay) FROM bronze_baocaotudong.pvkh_pstc_nhom_phu_trach
            WHERE ngay >= DATE_TRUNC('year', DATE '{date_str}') AND ngay <= DATE '{date_str}'
        );
        """,
        conn
    )
    conn.close()
    return df


@_df_cache()
def pvkh_pstc_dia_ban(date_str: str) -> pd.DataFrame:
    """Same shape/columns as pvkh_pstc_nhom_phu_trach, but pre-aggregated by dia_ban instead of
    nhom_phu_trach — carries no nhóm dimension at all, so it can't be crossed with nhóm (only
    usable where a chart pools every nhóm together, e.g. Tổng quan's Số dư TDPS/CCS/IRS theo
    địa bàn). Same latest-snapshot-on-or-before-date fallback as pvkh_pstc_nhom_phu_trach."""
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT * FROM bronze_baocaotudong.pvkh_pstc_dia_ban
        WHERE ngay = (
            SELECT MAX(ngay) FROM bronze_baocaotudong.pvkh_pstc_dia_ban
            WHERE ngay >= DATE_TRUNC('year', DATE '{date_str}') AND ngay <= DATE '{date_str}'
        );
        """,
        conn
    )
    conn.close()
    return df


@_df_cache()
def pvkh_pstc_pkkh(date_str: str) -> pd.DataFrame:
    """Same shape/columns as pvkh_pstc_nhom_phu_trach, but pre-aggregated by pkkh instead of
    nhom_phu_trach — see pvkh_pstc_dia_ban's docstring for why this has no nhóm dimension."""
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT * FROM bronze_baocaotudong.pvkh_pstc_pkkh
        WHERE ngay = (
            SELECT MAX(ngay) FROM bronze_baocaotudong.pvkh_pstc_pkkh
            WHERE ngay >= DATE_TRUNC('year', DATE '{date_str}') AND ngay <= DATE '{date_str}'
        );
        """,
        conn
    )
    conn.close()
    return df


@_df_cache()
def usd_vnd_rate(date_str: str) -> float | None:
    """USD/VND exchange rate (vndtom=d3) from bronze_reuter_domestic.daily_currency_domestic,
    the latest id_date on or before date_str with a non-null rate — FX data doesn't publish on
    weekends/holidays, same "most recent snapshot" fallback as pvkh_pstc_nhom_phu_trach.

    The IS NOT NULL filter matters: usd_vnd_rate_range's own docstring already documents that
    this table occasionally has a row present for a date with a null rate (e.g. 2026-01-10) —
    without it, MAX(id_date) can land on exactly such a row and this returns float(None), a
    TypeError, instead of falling back to the last genuinely known rate the way the range
    version already does via forward-fill."""
    target = int(pd.Timestamp(date_str).strftime("%Y%m%d"))
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT "vndtom=d3" FROM bronze_reuter_domestic.daily_currency_domestic
        WHERE id_date = (
            SELECT MAX(id_date) FROM bronze_reuter_domestic.daily_currency_domestic
            WHERE id_date <= {target} AND "vndtom=d3" IS NOT NULL
        );
        """,
        conn
    )
    conn.close()
    return float(df.iloc[0]["vndtom=d3"]) if not df.empty else None


@_df_cache()
def usd_vnd_rate_range(start_date: str, end_date: str) -> pd.Series:
    """USD/VND exchange rate (vndtom=d3) for every calendar day in [start_date, end_date],
    indexed by date. daily_currency_domestic has no rows on weekends/public holidays and
    occasionally a null rate on an otherwise-present row (e.g. 2026-01-10), so gaps are
    forward-filled from the latest known trading-day rate, with a backfill pass for any
    leading days before the window's first available rate (e.g. New Year's Day itself)."""
    start_id = int(pd.Timestamp(start_date).strftime("%Y%m%d"))
    end_id = int(pd.Timestamp(end_date).strftime("%Y%m%d"))
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT id_date, "vndtom=d3" AS rate
        FROM bronze_reuter_domestic.daily_currency_domestic
        WHERE id_date BETWEEN {start_id} AND {end_id}
        ORDER BY id_date;
        """,
        conn
    )
    conn.close()
    df["date"] = pd.to_datetime(df["id_date"].astype(str), format="%Y%m%d")
    series = df.set_index("date")["rate"]
    all_days = pd.date_range(start_date, end_date)
    return series.reindex(all_days).ffill().bfill()


@_df_cache()
def pvkh_pstc_nhom_phu_trach_range(start_date: str, end_date: str) -> pd.DataFrame:
    """Same table as pvkh_pstc_nhom_phu_trach, but a whole date range in one query — for
    building a multi-day trend chart instead of a single day's snapshot. Unlike the
    single-date version it does NOT collapse to the latest available ngay; every day in
    the window is returned so the chart keeps one column per day."""
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT * FROM bronze_baocaotudong.pvkh_pstc_nhom_phu_trach
        WHERE ngay BETWEEN '{start_date}' AND '{end_date}';
        """,
        conn
    )
    conn.close()
    return df


@_df_cache()
def pkkh_lookup(date_str: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT c.cif, p.tenpkkh AS pkkh
        FROM (
            SELECT DISTINCT ON (cif) cif, mapkkh
            FROM bronze_baocaotudong.pvkh_listcif
            WHERE EXTRACT(YEAR FROM monthyear) <= EXTRACT(YEAR FROM DATE '{date_str}')
            ORDER BY cif, monthyear DESC
        ) c
        LEFT JOIN bronze_baocaotudong.pvkh_pkkh p ON c.mapkkh = p.mapkkh;
        """,
        conn
    )
    conn.close()
    return df


@_df_cache()
def silver_pvkh_dl_kh_luy_ke(date_str: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql(
        f'SELECT * FROM silver."silver_pvkh_DL_KH_luy_ke" WHERE ngay = \'{date_str}\';',
        conn
    )
    conn.close()
    return df


@_df_cache()
def pvkh_mbnt_nhom_phu_trach(date_str: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql(
        f"SELECT * FROM bronze_baocaotudong.pvkh_mbnt_nhom_phu_trach WHERE ngay = '{date_str}';",
        conn
    )
    conn.close()
    return df


@_df_cache()
def pvkh_mbnt_nhom_phu_trach_range(start_date: str, end_date: str) -> pd.DataFrame:
    """Same table as pvkh_mbnt_nhom_phu_trach, but a whole date range in one query — for
    building a multi-day trend chart instead of a single day's snapshot."""
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT * FROM bronze_baocaotudong.pvkh_mbnt_nhom_phu_trach
        WHERE ngay BETWEEN '{start_date}' AND '{end_date}';
        """,
        conn
    )
    conn.close()
    return df


@_df_cache(maxsize=1)
def pvkh_kq_chinhanh() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM bronze_baocaotudong.pvkh_kq_chinhanh;", conn)
    conn.close()
    df["ngay"] = pd.to_datetime(df["ngay"]).dt.date
    return df[df["chi_nhanh"] != "TOTAL"].reset_index(drop=True)

# def pvkh_listcif() -> pd.DataFrame:
#     conn = get_connection()
#     df = pd.read_sql("SELECT * FROM bronze_baocaotudong.pvkh_listcif;", conn)
#     conn.close()
#     return df