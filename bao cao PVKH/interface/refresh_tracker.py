"""Refresh tracker — a small standalone page showing how fresh each source table is.

Runs separately from web_app.py (its own Flask app, port 5001) so a stale-data check never
depends on the dashboard rendering successfully:

    python -m interface.refresh_tracker

Each row is one table the dashboard reads, with the newest date it holds and how far that is
behind the freshest tracked table. The date column differs per table — the daily snapshots use
`ngay`, the bronze monthly extracts use `monthyear`, and the two silver báo cáo tables use the
Vietnamese `"Ngày"` — so it is declared per entry rather than guessed.

This exists because a truncated table is silent: pvkh_pstc stops at 2026-03-01, which made its
2026 TDPS doanh số read 591M against a real 2,180M with no error anywhere. Anything that feeds
a figure on the dashboard is worth watching here.
"""

from datetime import datetime, timedelta

import pandas as pd
from flask import Flask, render_template_string

from data_connect.db_connect import get_connection

app = Flask(__name__)

# The page re-queries itself on this cycle so it can be left open on a monitor. Twice a day is
# matched to how the sources actually move — the daily snapshots land once per business day, so
# polling harder would only add load without catching anything sooner.
REFRESH_HOURS = 12

# (schema, table, date column, what it feeds). Order is the display order.
TRACKED = [
    ("bronze_baocaotudong", "pvkh_dailyreport", "ngay", "Số dư TDPS theo địa bàn/PKKH"),
    ("bronze_baocaotudong", "pvkh_dsdaily_temp", "monthyear", "Doanh số TDPS 2026"),
    ("bronze_baocaotudong", "pvkh_pstc_nhom_phu_trach", "ngay", "Scorecard HĐLS/TDPS"),
    ("bronze_baocaotudong", "pvkh_pstc_dia_ban", "ngay", "PSTC theo địa bàn"),
    ("bronze_baocaotudong", "pvkh_pstc_pkkh", "ngay", "PSTC theo PKKH"),
    ("bronze_baocaotudong", "pvkh_mbnt_nhom_phu_trach", "ngay", "Scorecard MBNT"),
    ("bronze_baocaotudong", "pvkh_kq_chinhanh", "ngay", "Kết quả chi nhánh"),
    ("bronze_baocaotudong", "pvkh_kq_canbo", "ngay", "Kết quả cán bộ"),
    ("silver", "silver_pvkh_DL_KH_luy_ke", "ngay", "Biểu đồ địa bàn/PKKH (lũy kế)"),
    # The _view tables were tried as a fresher source but reverted (2026-08-17): their column
    # names changed mid-session, meaning they're being actively redefined in the database right
    # now and aren't safe to depend on yet. The app reads the base tables again, so that's what
    # this tracks — see bao_cao_ket_qua_mbnt_2025_2026 in db_connect.py.
    ("silver", "bao_cao_ket_qua_mbnt_2025_2026", "Ngày", "Kỳ báo cáo (danh sách ngày)"),
    ("silver", "bao_cao_ket_qua_hdls_2025_2026", "Ngày", "Top khách hàng HĐLS"),
    # Not in the original list, but both feed live figures and both are monthly, so they lag by
    # design — worth seeing next to the daily tables rather than being assumed current.
    ("bronze_baocaotudong", "pvkh_pstc", "monthyear", "Cơ sở so sánh 2025 (Y-1)"),
    ("bronze_baocaotudong", "pvkh_chiase", "monthyear", "Chia sẻ lợi nhuận MBNT"),
]


def collect() -> tuple[pd.DataFrame, str | None]:
    """One row per tracked table, plus a connection-level error if there is one.

    A table that errors is reported rather than dropped — a missing table is exactly the kind
    of failure this page exists to surface. The same goes for the database being unreachable:
    this page's whole job is to say whether data is arriving, so it has to render and explain
    itself when Postgres is down rather than returning a 500 that says nothing."""
    try:
        conn = get_connection()
    except Exception as exc:                          # noqa: BLE001 - surfaced in the UI
        blank = pd.DataFrame([
            {"schema": s, "table": t, "date_col": c, "feeds": f,
             "max_date": pd.NaT, "rows": 0, "error": "—"}
            for s, t, c, f in TRACKED
        ])
        blank["lag_days"] = pd.NA
        return blank, str(exc).strip().splitlines()[0][:160]

    rows = []
    for schema, table, col, feeds in TRACKED:
        try:
            df = pd.read_sql(
                f'SELECT MAX("{col}") AS max_date, COUNT(*) AS n FROM {schema}."{table}";', conn
            )
            rows.append({
                "schema": schema, "table": table, "date_col": col, "feeds": feeds,
                "max_date": pd.to_datetime(df["max_date"][0]), "rows": int(df["n"][0]),
                "error": None,
            })
        except Exception as exc:                      # noqa: BLE001 - surfaced in the UI
            conn.rollback()
            rows.append({
                "schema": schema, "table": table, "date_col": col, "feeds": feeds,
                "max_date": pd.NaT, "rows": 0, "error": str(exc).splitlines()[0][:120],
            })
    conn.close()

    df = pd.DataFrame(rows)
    newest = df["max_date"].max()
    df["lag_days"] = (newest - df["max_date"]).dt.days
    return df, None


PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"><title>Theo dõi cập nhật dữ liệu</title>
<style>
  :root { --primary:#006d68; --border:#e3e6e6; --card:#fff; --bg:#f5f7f7; --muted:#6b7280; }
  * { box-sizing:border-box; }
  body { margin:0; padding:28px; background:var(--bg); color:#111;
         font-family:'Segoe UI',system-ui,sans-serif; }
  h1 { margin:0 0 4px; font-size:20px; color:var(--primary); }
  .sub { color:var(--muted); font-size:13px; margin-bottom:20px; }
  .card { background:var(--card); border:1px solid var(--border); border-radius:12px;
          box-shadow:0 1px 4px rgba(0,0,0,.06); overflow:hidden; max-width:1100px; }
  table { border-collapse:collapse; width:100%; font-size:13px; }
  th { background:var(--primary); color:#fff; text-align:left; padding:10px 14px; font-weight:600; }
  td { padding:9px 14px; border-top:1px solid var(--border); }
  tr:hover td { background:#f0f7f6; }
  .mono { font-family:Consolas,monospace; }
  .num { text-align:right; font-variant-numeric:tabular-nums; }
  .pill { display:inline-block; padding:2px 9px; border-radius:999px; font-size:12px; font-weight:600; }
  .ok   { background:#e6f4ea; color:#116b32; }
  .warn { background:#fef4e5; color:#8a5300; }
  .bad  { background:#fdeaea; color:#a01b1b; }
  .err { color:#a01b1b; font-size:12px; }
  .foot { margin-top:14px; font-size:12px; color:var(--muted); }
  a.btn { display:inline-block; margin-bottom:18px; padding:7px 16px; border-radius:8px;
          background:var(--primary); color:#fff; text-decoration:none; font-size:13px; }
  .banner { background:#fdeaea; border:1px solid #f3c2c2; color:#7a1616; border-radius:10px;
            padding:11px 14px; margin:0 0 16px; font-size:13px; max-width:1100px; }
  .banner-detail { margin-top:5px; font-family:Consolas,monospace; font-size:12px; opacity:.85; }
  .auto { margin-left:12px; font-size:13px; color:var(--muted); }
  .auto b { color:var(--primary); font-variant-numeric:tabular-nums; }
  .dim { opacity:.75; }
</style>
</head>
<body>
  <h1>Theo dõi cập nhật dữ liệu</h1>
  <div class="sub">Ngày mới nhất của từng bảng nguồn &mdash; kiểm tra lúc {{ checked_at }}</div>
  <a class="btn" href="/">↻ Kiểm tra lại</a>
  <span class="auto">Tự động kiểm tra lại sau <b id="countdown">&mdash;</b>
    <span class="dim">(lúc {{ next_check }})</span></span>
  {% if conn_error %}
  <div class="banner">
    <b>Không kết nối được cơ sở dữ liệu.</b>
    Các số liệu bên dưới chưa kiểm tra được &mdash; trang sẽ tự thử lại.
    <div class="banner-detail">{{ conn_error }}</div>
  </div>
  {% endif %}
  <div class="card">
  <table>
    <tr>
      <th>Bảng</th><th>Cột ngày</th><th>Dùng cho</th>
      <th>Ngày mới nhất</th><th class="num">Số dòng</th><th>Độ trễ</th>
    </tr>
    {% for r in rows %}
    <tr>
      <td class="mono">{{ r.schema }}.{{ r.table }}</td>
      <td class="mono">{{ r.date_col }}</td>
      <td>{{ r.feeds }}</td>
      <td class="mono">{{ r.max_date }}</td>
      <td class="num">{{ r.rows }}</td>
      <td>
        {% if r.error %}<span class="err">{{ r.error }}</span>
        {% else %}<span class="pill {{ r.cls }}">{{ r.lag_label }}</span>{% endif %}
      </td>
    </tr>
    {% endfor %}
  </table>
  </div>
  <div class="foot">
    Độ trễ tính so với bảng mới nhất ({{ newest }}). Các bảng theo tháng (monthyear) trễ theo
    thiết kế. Cột &ldquo;Dùng cho&rdquo; ghi phần dashboard phụ thuộc vào bảng đó.
  </div>
<script>
  // Count down to a fixed deadline rather than trusting a single long setTimeout: a laptop
  // that sleeps for part of the window would otherwise fire late by however long it slept.
  // On wake the remaining time is recomputed from the clock and reloads immediately if due.
  var DEADLINE = Date.now() + {{ refresh_ms }};
  function tick() {
    var left = DEADLINE - Date.now();
    if (left <= 0) { location.reload(); return; }
    var h = Math.floor(left / 3600000),
        m = Math.floor((left % 3600000) / 60000),
        s = Math.floor((left % 60000) / 1000);
    document.getElementById('countdown').textContent =
      h + 'h ' + String(m).padStart(2, '0') + 'm ' + String(s).padStart(2, '0') + 's';
  }
  tick();
  setInterval(tick, 1000);
</script>
</body>
</html>
"""


def _lag_label(lag, date_col):
    """Daily and monthly tables are judged on different scales, but both are judged — a monthly
    extract sitting two months behind is still broken, it just isn't broken at a daily
    threshold. The bands are set so pvkh_pstc's 165-day gap reads red: that is the failure this
    page was built to catch, and treating "monthly" as an automatic pass would hide it."""
    if pd.isna(lag):
        return "—", "bad"
    lag = int(lag)
    if lag == 0:
        return "mới nhất", "ok"
    # a monthly table normally trails by up to the previous month-end plus reporting delay
    ok_days, warn_days = (62, 92) if date_col == "monthyear" else (0, 2)
    if lag <= ok_days:
        return f"trễ {lag} ngày", "ok"
    if lag <= warn_days:
        return f"trễ {lag} ngày", "warn"
    return f"trễ {lag} ngày", "bad"


@app.route("/")
def index():
    df, conn_error = collect()
    newest = df["max_date"].max()
    rows = []
    for _, r in df.iterrows():
        label, cls = _lag_label(r["lag_days"], r["date_col"])
        rows.append({
            "schema": r["schema"], "table": r["table"], "date_col": r["date_col"],
            "feeds": r["feeds"], "error": r["error"], "rows": f"{r['rows']:,}",
            "max_date": "—" if pd.isna(r["max_date"]) else r["max_date"].strftime("%d/%m/%Y"),
            "lag_label": label, "cls": cls,
        })
    now = datetime.now()
    return render_template_string(
        PAGE, rows=rows, conn_error=conn_error,
        newest="—" if pd.isna(newest) else newest.strftime("%d/%m/%Y"),
        checked_at=now.strftime("%H:%M:%S %d/%m/%Y"),
        next_check=(now + timedelta(hours=REFRESH_HOURS)).strftime("%H:%M %d/%m"),
        refresh_ms=REFRESH_HOURS * 3600 * 1000,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
