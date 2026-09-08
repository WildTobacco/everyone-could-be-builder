import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import base64
import colorsys
import math
import pandas as pd
from flask import Flask, request

LOGO_PATH = r"C:\Users\hieupg\Downloads\logo moi.png"
with open(LOGO_PATH, "rb") as f:
    LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
from data_connect.db_connect import bao_cao_ket_qua_mbnt_2025_2026, bao_cao_ket_qua_hdls_2025_2026
from calculations.top_kh_mbnt_tang_truong import (
    get_top_bottom_by_group as get_top_bottom_by_group_mbnt,
    get_top_bottom_by_group_abs as get_top_bottom_by_group_abs_mbnt,
)
from calculations.top_kh_hdls_tang_truong import (
    get_top_bottom_by_group as get_top_bottom_by_group_hdls,
    get_top_bottom_by_group_abs as get_top_bottom_by_group_abs_hdls,
)
from calculations.tong_ln_nhom import tong_ln_nhom
from calculations.ln_luy_ke_kdntps import ln_luy_ke_kdntps_by_nhom
from calculations.ht_thang_nam import compute_ht_thang_nam
from calculations.tong_ds_mbnt_ytd import tong_ds_mbnt_ytd_by_nhom
from calculations.tong_ln_mbnt_ytd import tong_ln_mbnt_ytd_by_nhom
from calculations.y1_tong_ds_mbnt_nhom import compute_y1_tong_ds_mbnt_nhom
from calculations.y1_tong_ln_mbnt_nhom import compute_y1_tong_ln_mbnt_nhom
from calculations.ht_ds_mbnt_nam import ke_hoach_ds_mbnt_nam
from calculations.ht_ln_mbnt_nam import ke_hoach_ln_mbnt_nam
from calculations.y1_nim_mbnt_nhom_diaban_pkkh import y1_nim_mbnt_nhom_diaban_pkkh, y1_nim_by_nhom_diaban, y1_nim_by_nhom_pkkh
from calculations.y_nim_mbnt_nhom_diaban_pkkh import y_nim_mbnt_nhom_diaban_pkkh, y_nim_by_nhom_diaban, y_nim_by_nhom_pkkh
from calculations.y1_ln_mbnt_nhom_diaban_pkkh import y1_ln_mbnt_by_nhom_diaban, y1_ln_mbnt_by_nhom_pkkh
from calculations.y_ln_mbnt_nhom_diaban_pkkh import y_ln_mbnt_by_nhom_diaban, y_ln_mbnt_by_nhom_pkkh
from calculations.KH_mbnt_nhom_dia_ban_2026 import kh_mbnt_by_nhom_diaban
from calculations.KH_mbnt_pkkh_2026 import kh_mbnt_by_nhom_pkkh
from calculations.y1_ds_mbnt_nhom_diaban_pkkh import y1_ds_mbnt_by_nhom_diaban, y1_ds_mbnt_by_nhom_pkkh
from calculations.y_ds_mbnt_nhom_diaban_pkkh import y_ds_mbnt_by_nhom_diaban, y_ds_mbnt_by_nhom_pkkh
from calculations.tong_ds_hdls_ytd_nhom import tong_ds_hdls_ytd_by_nhom
from calculations.tong_ln_hdls_ytd_nhom import tong_ln_hdls_ytd_by_nhom
from calculations.y1_ds_hdls_nhom_diaban_pkkh import ds_hdls_pct_change_by_nhom
from calculations.y1_ln_hdls_nhom_diaban_pkkh import ln_hdls_pct_change_by_nhom
from calculations.ds_hdls_hoan_thanh import ds_hdls_hoan_thanh
from calculations.ln_hdls_hoan_thanh import ln_hdls_hoan_thanh
from calculations.y1_ln_hdls_nhom_diaban_pkkh import y1_ln_hdls_by_nhom_diaban, y1_ln_hdls_by_nhom_pkkh
from calculations.y_ln_hdls_nhom_diaban_pkkh import y_ln_hdls_by_nhom_diaban, y_ln_hdls_by_nhom_pkkh
from calculations.y1_ds_hdls_nhom_diaban_pkkh import y1_ds_hdls_by_nhom_diaban, y1_ds_hdls_by_nhom_pkkh
from calculations.y_ds_hdls_nhom_diaban_pkkh import y_ds_hdls_by_nhom_diaban, y_ds_hdls_by_nhom_pkkh
from calculations.date_table import get_date_table, latest_date, same_day_last_year
from calculations.cn_trong_diem_scorecard import branch_table
from calculations.cn_canbo_scorecard import staff_table

app = Flask(__name__)

GROWTH_COLUMNS_PCT = {"▲LN%", "▲DS%", "▲NIM%"}
GROWTH_COLUMNS_ABS = {"▲LN", "▲DS", "▲NIM"}
HIGHLIGHT_COLUMNS = {"KQ KDNT&PS (tr đồng)": "#E9EDB5"}

GREEN_LIGHT_START = "D7FFD7"
GREEN_LIGHT_END = "00FF14"
RED_LIGHT_START = "FF0000"
RED_LIGHT_END = "FFC8C8"

GREEN_DARK_START = "12331F"
GREEN_DARK_END = "1F8B4C"
RED_DARK_START = "8B1E1E"
RED_DARK_END = "3D1A1A"

ALL_GROUPS = ["PTKD 1", "PTKD 2", "VPV"]
KPI_LABELS = {"PTKD 1": "PTKD 1", "PTKD 2": "PTKD 2", "VPV": "VPV", "TOTAL": "Toàn Hệ Thống"}
CHART_TARGET_WIDTH = 620  # approx usable width of one chart-card when 2 charts sit side by side
PKKH_EXCLUDED = {"KH ao", "KH vang lai", "KHCN", "KHACH HANG KHAC"}

THEME_CSS = """
table.data-table td.pos { color: var(--up); font-weight: 600; }
table.data-table td.neg { color: var(--down); font-weight: 600; }
.gradient-cell { background-color: var(--cell-bg-light); color: #1a1c18; }
.dark .gradient-cell { background-color: var(--cell-bg-dark); color: #e6efed; }
:root {
  --background: #f5f3ef; --foreground: #1a1c18;
  --card: #fefdfb; --card-foreground: #1a1c18;
  --muted: #ece9e3; --muted-foreground: #5c5a54;
  --border: #ddd9d3;
  --primary: #0d5d56; --primary-foreground: #ffffff;
  --up: #0d8a5f; --down: #c0392b;
  --radius: 0.5rem;
  --ribbon-teal: #006d68; --ribbon-teal-text: #ffc72c;
  --ribbon-gold: #ffc72c; --ribbon-gold-text: #006d68;
}
.dark {
  --background: #0b1413; --foreground: #e6efed;
  --card: #111c1a; --card-foreground: #e6efed;
  --muted: #1a2725; --muted-foreground: #8aa39e;
  --border: #223330;
  --primary: #36a695; --primary-foreground: #06211e;
  --up: #34d399; --down: #f87171;
  --ribbon-teal: #0a3d3a; --ribbon-teal-text: #d9a93a;
  --ribbon-gold: #a8791f; --ribbon-gold-text: #0e2a27;
}
body {
  background: var(--background); color: var(--foreground);
  font-family: system-ui, sans-serif; margin: 30px; padding: 24px;
  border: 10px solid var(--ribbon-teal);
  border-radius: 16px;
  box-sizing: border-box;
}
.filter-row {
  display: flex;
  gap: 24px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.charts-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  background: var(--card);
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: 14px 14px 0 0;
  padding: 8px 16px;
}
.charts-panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 24px;
  overflow: hidden;
}
.charts-panel .charts-toolbar {
  border: none;
  border-bottom: 1px solid var(--border);
  border-radius: 0;
}
.charts-panel .chart-card {
  border: none;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
  margin-bottom: 0;
}
.charts-panel .chart-card + .chart-card {
  border-left: 1px solid var(--border);
}
.charts-panel .filter-row {
  margin-bottom: 0;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border);
  align-items: center;
}
.charts-panel .table-card {
  border: none;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
  margin-bottom: 0;
}
.filter-group-compact {
  display: flex;
  align-items: center;
  gap: 6px;
}
.filter-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--primary);
}
.filter-select {
  background: var(--card);
  color: var(--foreground);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 10px;
  font-size: 12px;
  min-width: 120px;
  cursor: pointer;
}
.kpi-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.kpi-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 16px 20px;
  flex: 1;
  min-width: 220px;
}
.kpi-title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--primary);
  text-align: center;
  margin: 0 0 12px 0;
}
.kpi-row-inner {
  display: flex;
  align-items: center;
}
.kpi-metric {
  flex: 1;
  text-align: center;
}
.kpi-divider {
  width: 1px;
  align-self: stretch;
  background: var(--border);
  margin: 0 12px;
}
.kpi-big {
  font-size: 26px;
  font-weight: 800;
  color: var(--foreground);
}
.kpi-big.pos { color: var(--up); }
.kpi-big.neg { color: var(--down); }
.kpi-sub {
  font-size: 13px;
  color: var(--muted-foreground);
  margin-top: 4px;
}
.kpi-footer {
  display: flex;
  border-top: 1px solid var(--border);
  margin-top: 12px;
  padding-top: 10px;
}
.kpi-split {
  display: flex;
  align-items: stretch;
}
.kpi-col {
  flex: 1;
  text-align: center;
}
.kpi-footer-metric {
  flex: 1;
  text-align: center;
  font-size: 15px;
  font-weight: 700;
  color: var(--foreground);
  white-space: nowrap;
}
.table-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 16px;
}
.table-card h2 {
  margin: 20px 0 10px 0;
  padding: 0;
  color: var(--primary);
}
.table-card h2:first-child {
  margin-top: 0;
}
.chart-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 16px;
}
.chart-card h2 {
  margin: 0 0 10px 0;
  padding: 0;
  color: var(--primary);
}
.table-frame {
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow-x: auto;
}
table.data-table {
  border-collapse: collapse; width: 100%; margin-bottom: 0;
  background: var(--card); color: var(--card-foreground);
}
table.data-table th, table.data-table td {
  border: 1px solid var(--border); padding: 6px 10px; font-size: 13px; color: var(--card-foreground);
}
table.data-table td { white-space: nowrap; }
table.data-table th { background-color: var(--primary); color: var(--primary-foreground); white-space: normal; }
.toggle-btn {
  padding: 6px 14px; border-radius: var(--radius); border: 1px solid var(--border);
  background: var(--card); color: var(--foreground); cursor: pointer;
}
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}
.header-logo {
  flex-shrink: 0;
}
.header-logo-img {
  height: 80px;
  width: auto;
  display: block;
}
.header-title-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.report-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--ribbon-teal);
  margin: 0;
  text-align: center;
}
.date-pill {
  background: var(--card);
  color: var(--foreground);
  border: none;
  border-bottom: 1px solid var(--border);
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 13px;
  text-align: center;
  cursor: pointer;
}
.ribbon {
  text-align: center;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.5px;
  padding: 8px 0;
  border-radius: 6px;
  margin: 0 auto 10px auto;
}
.ribbon-1 { width: 70%; background: var(--ribbon-teal); color: var(--ribbon-teal-text); margin-bottom: 10px; }
.ribbon-2 { width: 70%; background: var(--ribbon-teal); color: var(--ribbon-teal-text); }
.ribbon-3 { width: 40%; background: var(--ribbon-gold); color: var(--ribbon-gold-text); margin-bottom: 10px; }
"""

THEME_JS = """
function applyStoredTheme() {
  const stored = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (stored === 'dark' || (!stored && prefersDark)) {
    document.documentElement.classList.add('dark');
  }
}
function toggleTheme() {
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
}

let mbntRankingGroup = 'PTKD 1';
let mbntRanking = 'pct';
let hdlsRankingGroup = 'PTKD 1';
let hdlsRanking = 'pct';

function updateMbntRankingView() {
  ['mbnt-pct-sections', 'mbnt-abs-sections'].forEach(id => {
    document.getElementById(id).style.display = 'none';
  });
  const activeSection = document.getElementById('mbnt-' + mbntRanking + '-sections');
  activeSection.style.display = 'block';
  activeSection.querySelectorAll('.table-card').forEach(card => {
    card.style.display = (card.dataset.group === mbntRankingGroup) ? 'block' : 'none';
  });
}
function updateHdlsRankingView() {
  ['hdls-pct-sections', 'hdls-abs-sections'].forEach(id => {
    document.getElementById(id).style.display = 'none';
  });
  const activeSection = document.getElementById('hdls-' + hdlsRanking + '-sections');
  activeSection.style.display = 'block';
  activeSection.querySelectorAll('.table-card').forEach(card => {
    card.style.display = (card.dataset.group === hdlsRankingGroup) ? 'block' : 'none';
  });
}

function onMbntRankingGroupChange(value) {
  mbntRankingGroup = value;
  updateMbntRankingView();
}
function onMbntRankingChange(value) {
  mbntRanking = value;
  updateMbntRankingView();
}
function onHdlsRankingGroupChange(value) {
  hdlsRankingGroup = value;
  updateHdlsRankingView();
}
function onHdlsRankingChange(value) {
  hdlsRanking = value;
  updateHdlsRankingView();
}
function onDateChange(value) {
  const url = new URL(window.location.href);
  url.searchParams.set('date', value);
  window.location.href = url.toString();
}
function onCnTrongDiemNhomChange(value) {
  const url = new URL(window.location.href);
  url.searchParams.set('cn_trong_diem_nhom', value);
  window.location.href = url.toString();
}
function onCnCanboNhomChange(value) {
  const url = new URL(window.location.href);
  url.searchParams.set('cn_canbo_nhom', value);
  window.location.href = url.toString();
}
function onChartNhomChange(value) {
  const url = new URL(window.location.href);
  url.searchParams.set('chart_nhom', value);
  window.location.href = url.toString();
}
function onChartMetricChange(value) {
  ['chart-ds', 'chart-nim', 'chart-ln'].forEach(id => {
    document.getElementById(id).style.display = 'none';
  });
  document.getElementById('chart-' + value).style.display = 'flex';
}
function onHdlsChartNhomChange(value) {
  const url = new URL(window.location.href);
  url.searchParams.set('hdls_chart_nhom', value);
  window.location.href = url.toString();
}
function onHdlsChartMetricChange(value) {
  ['hdls-chart-ds', 'hdls-chart-ln'].forEach(id => {
    document.getElementById(id).style.display = 'none';
  });
  document.getElementById('hdls-chart-' + value).style.display = 'flex';
}

applyStoredTheme();
document.addEventListener('DOMContentLoaded', () => {
  updateMbntRankingView();
  updateHdlsRankingView();
});
"""


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return '#{:02X}{:02X}{:02X}'.format(*(round(c) for c in rgb))


def interpolate_color(start_hex, end_hex, fraction):
    fraction = max(0.0, min(1.0, fraction))
    start_rgb = hex_to_rgb(start_hex)
    end_rgb = hex_to_rgb(end_hex)
    rgb = tuple(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * fraction for i in range(3))
    return rgb_to_hex(rgb)


def compute_row_colors(df, rank_col, gradient):
    """Returns {idx: (light_hex, dark_hex)} for each row's rank_col value,
    scaled between the min/max of that column within this table."""
    if rank_col not in df.columns:
        return {}
    values = df[rank_col].dropna()
    if values.empty:
        return {}
    vmin, vmax = values.min(), values.max()
    colors = {}
    for idx, val in df[rank_col].items():
        if pd.isna(val):
            continue
        fraction = 0.5 if vmax == vmin else (val - vmin) / (vmax - vmin)
        if gradient == "top":
            light = interpolate_color(GREEN_LIGHT_START, GREEN_LIGHT_END, fraction)
            dark = interpolate_color(GREEN_DARK_START, GREEN_DARK_END, fraction)
        else:
            light = interpolate_color(RED_LIGHT_START, RED_LIGHT_END, fraction)
            dark = interpolate_color(RED_DARK_START, RED_DARK_END, fraction)
        colors[idx] = (light, dark)
    return colors


def compute_stt_gradient_colors(df, col="STT"):
    """Returns {idx: (light_hex, dark_hex)} for each row's (numeric) STT rank,
    scaled green (best/lowest rank) -> yellow -> red (worst/highest rank)."""
    numeric = pd.to_numeric(df[col], errors="coerce")
    values = numeric.dropna()
    if values.empty:
        return {}
    vmin, vmax = values.min(), values.max()
    colors = {}
    for idx, val in numeric.items():
        if pd.isna(val):
            continue
        fraction = 0.5 if vmax == vmin else (val - vmin) / (vmax - vmin)
        hue = (1 - fraction) * (120 / 360)
        light_rgb = colorsys.hls_to_rgb(hue, 0.55, 0.75)
        dark_rgb = colorsys.hls_to_rgb(hue, 0.28, 0.55)
        light = rgb_to_hex(tuple(c * 255 for c in light_rgb))
        dark = rgb_to_hex(tuple(c * 255 for c in dark_rgb))
        colors[idx] = (light, dark)
    return colors


def render_table(df, rank_col=None, gradient=None, stt_colors=None):
    headers = "".join(
        f"<th>{col.replace(' (tr đồng)', '<br>(tr đồng)')}</th>" for col in df.columns
    )

    row_colors = {}
    if rank_col and gradient:
        row_colors = compute_row_colors(df, rank_col, gradient)

    rows_html = []
    for idx, row in df.iterrows():
        color_pair = row_colors.get(idx)
        stt_pair = stt_colors.get(idx) if stt_colors else None
        cells = []
        for col in df.columns:
            value = row[col]

            if col == "Tên khách hàng" and color_pair:
                light_color, dark_color = color_pair
                cell_style = f' style="--cell-bg-light: #{light_color.lstrip("#")}; --cell-bg-dark: #{dark_color.lstrip("#")};" class="gradient-cell"'
            elif col == "STT" and stt_pair:
                light_color, dark_color = stt_pair
                cell_style = f' style="--cell-bg-light: #{light_color.lstrip("#")}; --cell-bg-dark: #{dark_color.lstrip("#")};" class="gradient-cell"'
            elif col in HIGHLIGHT_COLUMNS:
                cell_style = f' style="background-color:{HIGHLIGHT_COLUMNS[col]}; color:#1a1c18;"'
            else:
                cell_style = ""

            if col in GROWTH_COLUMNS_PCT or col in GROWTH_COLUMNS_ABS:
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    numeric_value = None

                if numeric_value is not None and not pd.isna(numeric_value):
                    css_class = "pos" if numeric_value >= 0 else "neg"
                    suffix = " %" if col in GROWTH_COLUMNS_PCT else ""
                    cells.append(f'<td class="{css_class}"{cell_style}>{value}{suffix}</td>')
                else:
                    cells.append(f"<td{cell_style}>{value}</td>")
            elif isinstance(value, str) and (value.startswith("▲") or value.startswith("▼")):
                css_class = "pos" if value.startswith("▲") else "neg"
                cells.append(f'<td class="{css_class}"{cell_style}>{value}</td>')
            else:
                cells.append(f"<td{cell_style}>{value}</td>")

        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    table_html = f'<table class="data-table"><thead><tr>{headers}</tr></thead><tbody>{"".join(rows_html)}</tbody></table>'
    return f'<div class="table-frame">{table_html}</div>'


def build_sections(by_group, rank_col, title_top, title_bottom):
    sections = []
    for group, (top5, bottom5) in by_group.items():
        sections.append(
            f'<div class="table-card" data-group="{group}">'
            f'<h2>{title_top}</h2>'
            f'{render_table(top5, rank_col=rank_col, gradient="top")}'
            f'<h2>{title_bottom}</h2>'
            f'{render_table(bottom5, rank_col=rank_col, gradient="bottom")}'
            f'</div>'
        )
    return sections


def build_kpi_row(selected_date: str, date_2025: str):
    kdntps = ln_luy_ke_kdntps_by_nhom(selected_date)

    baseline = tong_ln_nhom(date_2025)
    ht = compute_ht_thang_nam(kdntps, selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        value = kdntps.get(key, 0.0)
        base = baseline.get(key, 0.0)
        pct = (value - base) / base * 100 if base else 0.0
        arrow = "▲" if pct >= 0 else "▼"
        css_class = "pos" if pct >= 0 else "neg"
        value_bn = value / 1_000_000_000

        ht_thang = ht.loc[key, "ht_thang"] * 100 if pd.notna(ht.loc[key, "ht_thang"]) else 0.0
        ht_nam = ht.loc[key, "ht_nam"] * 100 if pd.notna(ht.loc[key, "ht_nam"]) else 0.0

        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{value_bn:,.0f}bn</div>
                    <div class="kpi-sub">LN KDNTPS</div>
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big {css_class}">{arrow} {abs(pct):.1f}%</div>
                    <div class="kpi-sub">so với cùng kỳ</div>
                </div>
            </div>
            <div class="kpi-footer">
                <div class="kpi-footer-metric">HT tháng: <b>{ht_thang:.1f}%</b></div>
                <div class="kpi-footer-metric">HT năm: <b>{ht_nam:.1f}%</b></div>
            </div>
        </div>
        ''')
    return cards


def build_ds_mbnt_row(selected_date: str, date_2025: str):
    ds = tong_ds_mbnt_ytd_by_nhom(selected_date)
    ln = tong_ln_mbnt_ytd_by_nhom(selected_date)
    ds_baseline = compute_y1_tong_ds_mbnt_nhom(date_2025)
    ln_baseline = compute_y1_tong_ln_mbnt_nhom(date_2025)
    ds_ke_hoach_nam = ke_hoach_ds_mbnt_nam()
    ln_ke_hoach_nam = ke_hoach_ln_mbnt_nam()
    nim_2025 = y1_nim_mbnt_nhom_diaban_pkkh(date_2025)
    nim_2026 = y_nim_mbnt_nhom_diaban_pkkh(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_val, ln_val = ds.get(key, 0.0), ln.get(key, 0.0)
        ds_base, ln_base = ds_baseline.get(key, 0.0), ln_baseline.get(key, 0.0)
        ds_pct = (ds_val - ds_base) / ds_base * 100 if ds_base else 0.0
        ln_pct = (ln_val - ln_base) / ln_base * 100 if ln_base else 0.0
        ds_arrow, ln_arrow = ("▲" if ds_pct >= 0 else "▼"), ("▲" if ln_pct >= 0 else "▼")
        ds_css, ln_css = ("pos" if ds_pct >= 0 else "neg"), ("pos" if ln_pct >= 0 else "neg")
        ds_bn, ln_bn = ds_val / 1_000_000_000, ln_val / 1_000_000_000

        ds_ht_nam = ds_val / ds_ke_hoach_nam.get(key, 0.0) * 100 if ds_ke_hoach_nam.get(key, 0.0) else 0.0
        ln_ht_nam = ln_val / ln_ke_hoach_nam.get(key, 0.0) * 100 if ln_ke_hoach_nam.get(key, 0.0) else 0.0
        nim25_val = nim_2025.get(key, 0.0)
        nim26_val = nim_2026.get(key, 0.0)

        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{ds_bn:,.2f}bn</div>
                    <div class="kpi-sub">Doanh số</div>
                    <div class="kpi-big {ds_css}" style="font-size:18px;margin-top:8px;">{ds_arrow} {abs(ds_pct):.1f}%</div>
                    <div class="kpi-sub">so với cùng kỳ</div>
                </div>
                <div class="kpi-metric">
                    <div class="kpi-big">{ln_bn:,.2f}bn</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    <div class="kpi-big {ln_css}" style="font-size:18px;margin-top:8px;">{ln_arrow} {abs(ln_pct):.1f}%</div>
                    <div class="kpi-sub">so với cùng kỳ</div>
                </div>
            </div>
            <div class="kpi-footer">
                <div class="kpi-footer-metric">HT năm: <b>{ds_ht_nam:.2f}%</b></div>
                <div class="kpi-footer-metric">HT năm: <b>{ln_ht_nam:.2f}%</b></div>
            </div>
            <div class="kpi-row-inner" style="margin-top:12px;">
                <div class="kpi-metric">
                    <div class="kpi-big">{nim25_val:,.2f}</div>
                    <div class="kpi-sub">NIM 2025</div>
                </div>
                <div class="kpi-metric">
                    <div class="kpi-big">{nim26_val:,.2f}</div>
                    <div class="kpi-sub">NIM 2026</div>
                </div>
            </div>
        </div>
        ''')
    return cards


def _fmt_bn_m(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}bn"
    return f"{value / 1_000_000:,.2f}M"


def build_ds_hdls_row(selected_date: str):
    ds = tong_ds_hdls_ytd_by_nhom(selected_date)
    ln = tong_ln_hdls_ytd_by_nhom(selected_date)
    ds_pct_all = ds_hdls_pct_change_by_nhom(selected_date)
    ln_pct_all = ln_hdls_pct_change_by_nhom(selected_date)
    ds_ht_all = ds_hdls_hoan_thanh(selected_date)
    ln_ht_all = ln_hdls_hoan_thanh(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_val, ln_val = ds.get(key, 0.0), ln.get(key, 0.0)
        ds_pct = ds_pct_all.get(key, 0.0) or 0.0
        ln_pct = ln_pct_all.get(key, 0.0) or 0.0
        ds_arrow, ln_arrow = ("▲" if ds_pct >= 0 else "▼"), ("▲" if ln_pct >= 0 else "▼")
        ds_css, ln_css = ("pos" if ds_pct >= 0 else "neg"), ("pos" if ln_pct >= 0 else "neg")
        ds_ht = (ds_ht_all.get(key, 0.0) or 0.0) * 100
        ln_ht = (ln_ht_all.get(key, 0.0) or 0.0) * 100

        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    <div class="kpi-big {ds_css}" style="font-size:18px;margin-top:8px;">{ds_arrow} {abs(ds_pct):.1f}%</div>
                    <div class="kpi-sub">so với cùng kỳ</div>
                </div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    <div class="kpi-big {ln_css}" style="font-size:18px;margin-top:8px;">{ln_arrow} {abs(ln_pct):.1f}%</div>
                    <div class="kpi-sub">so với cùng kỳ</div>
                </div>
            </div>
            <div class="kpi-footer">
                <div class="kpi-footer-metric">HT năm: <b>{ds_ht:.2f}%</b></div>
                <div class="kpi-footer-metric">HT năm: <b>{ln_ht:.2f}%</b></div>
            </div>
        </div>
        ''')
    return cards


def _nice_step(max_val: float) -> float:
    if max_val <= 0:
        return 1
    raw_step = max_val / 5
    magnitude = 10 ** math.floor(math.log10(raw_step))
    for m in (1, 2, 5, 10):
        step = m * magnitude
        if step >= raw_step:
            return step
    return raw_step


def _build_clustered_chart(df_2025: pd.DataFrame, df_2026: pd.DataFrame, dim_col: str, value_col: str,
                            scale: float, unit: str, legend_label: str, nhom_filter: str = None,
                            target_series: pd.Series = None) -> str:
    merged = pd.merge(
        df_2025, df_2026, on=["nhom_phu_trach", dim_col], how="outer", suffixes=("_2025", "_2026")
    ).fillna(0)
    merged = merged[merged["nhom_phu_trach"] != "TSC"]
    merged = merged[merged[f"{value_col}_2025"] != 0]
    # scale is fixed to the full (unfiltered) dataset's max so the y-axis doesn't rescale when filtering
    # (also factors in target_series, or a target line taller than every bar would render off-screen)
    target_vals = (target_series.dropna() / scale).tolist() if target_series is not None else []
    max_val = max(
        (merged[f"{value_col}_2026"] / scale).tolist()
        + (merged[f"{value_col}_2025"] / scale).tolist()
        + target_vals
        + [1]
    )
    if nhom_filter:
        merged = merged[merged["nhom_phu_trach"] == nhom_filter]
    merged = merged.sort_values(["nhom_phu_trach", dim_col]).reset_index(drop=True)

    groups = merged["nhom_phu_trach"].tolist()
    dia_bans = merged[dim_col].tolist()
    vals_2026 = (merged[f"{value_col}_2026"] / scale).tolist()
    vals_2025 = (merged[f"{value_col}_2025"] / scale).tolist()
    step = _nice_step(max_val)
    grid_max = step
    while grid_max < max_val:
        grid_max += step

    chart_h, left_pad, top_pad, bottom_pad, right_pad = 150, 45, 30, 50, 10
    n = len(dia_bans)
    # bar width scales to fill CHART_TARGET_WIDTH regardless of column count, avoiding leftover blank space
    available = max(CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    bar_w = round(max(8, available / (n * 3.83 - 1.67)) if n else 18, 1)
    bar_gap, group_gap = round(bar_w * 0.17, 1), round(bar_w * 1.67, 1)
    group_w = bar_w * 2 + bar_gap
    width = round(left_pad + n * group_w + max(n - 1, 0) * group_gap + right_pad, 1)
    height = chart_h + top_pad + bottom_pad

    grid_lines = []
    n_ticks = int(round(grid_max / step))
    for i in range(n_ticks + 1):
        v = i * step
        y = top_pad + chart_h - (chart_h * v / grid_max if grid_max else 0)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - 10}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.0f}{unit}</text>')

    bars = []
    hover_rects = []
    group_ticks = []
    nhom_labels = []
    bar_ranges = []
    prev_group = None
    group_start_x = left_pad
    for i, (g, db, v26, v25) in enumerate(zip(groups, dia_bans, vals_2026, vals_2025)):
        x = left_pad + i * (group_w + group_gap)
        h26 = chart_h * v26 / grid_max if grid_max else 0
        h25 = chart_h * v25 / grid_max if grid_max else 0
        y26, y25 = top_pad + chart_h - h26, top_pad + chart_h - h25
        bars.append(f'<rect x="{x}" y="{y26:.1f}" width="{bar_w}" height="{h26:.1f}" fill="#006d68" rx="2" />')
        bars.append(f'<rect x="{x + bar_w + bar_gap}" y="{y25:.1f}" width="{bar_w}" height="{h25:.1f}" fill="#ffc72c" rx="2" />')
        bars.append(f'<text x="{x + group_w / 2}" y="{top_pad + chart_h + 14}" font-size="10" text-anchor="middle" fill="var(--foreground)">{db}</text>')
        bar_ranges.append((x, x + group_w, g, db))

        # summarized tooltip on a wide invisible overlay, so hovering anywhere near the group works
        tv = target_series.get((g, db)) if target_series is not None else None
        target_line = f"\nKHKD 2026: {tv / scale:,.2f}{unit}" if tv is not None and not pd.isna(tv) else ""
        summary = f"{g} - {db}\n{legend_label} 2026: {v26:,.2f}{unit}\n{legend_label} 2025: {v25:,.2f}{unit}{target_line}"
        hover_rects.append(
            f'<rect x="{x - bar_gap / 2:.1f}" y="{top_pad}" width="{group_w + bar_gap:.1f}" height="{chart_h}" '
            f'fill="transparent"><title>{summary}</title></rect>'
        )

        if g != prev_group:
            if prev_group is not None:
                mid = (group_start_x + x - group_gap) / 2
                nhom_labels.append((mid, prev_group))
                group_ticks.append(x - group_gap / 2)
            group_start_x = x
            prev_group = g
    last_x = left_pad + n * (group_w + group_gap)
    mid = (group_start_x + last_x - group_gap) / 2
    nhom_labels.append((mid, prev_group))

    nhom_html = "".join(
        f'<text x="{mid}" y="{top_pad + chart_h + 32}" font-size="11" font-weight="700" text-anchor="middle" fill="var(--foreground)">{name}</text>'
        for mid, name in nhom_labels
    )
    tick_html = "".join(
        f'<line x1="{tx}" y1="{top_pad + chart_h}" x2="{tx}" y2="{top_pad + chart_h + 6}" stroke="var(--border)" />'
        for tx in group_ticks
    )

    target_html = ""
    if target_series is not None:
        segments = []
        for bx1, bx2, gname, dname in bar_ranges:
            tv = target_series.get((gname, dname))
            if tv is None or pd.isna(tv):
                continue
            tv_scaled = tv / scale
            ty = top_pad + chart_h - (chart_h * tv_scaled / grid_max if grid_max else 0)
            segments.append(
                f'<line x1="{bx1:.1f}" y1="{ty:.1f}" x2="{bx2:.1f}" y2="{ty:.1f}" '
                f'stroke="#c0392b" stroke-width="2" stroke-dasharray="6,3" />'
            )
        target_html = "".join(segments)

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; height:auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{top_pad + chart_h}" x2="{width - 10}" y2="{top_pad + chart_h}" stroke="var(--foreground)" />
        {''.join(bars)}
        {target_html}
        {tick_html}
        {nhom_html}
        {''.join(hover_rects)}
    </svg>
    <div style="display:flex; gap:20px; justify-content:center; margin-top:8px; font-size:12px;">
        <span><span style="display:inline-block;width:10px;height:10px;background:#006d68;margin-right:6px;"></span>{legend_label} 2026</span>
        {'<span><span style="display:inline-block;width:14px;height:0;border-top:2px dashed #c0392b;margin-right:6px;"></span>KHKD 2026</span>' if target_series is not None else ''}
        <span><span style="display:inline-block;width:10px;height:10px;background:#ffc72c;margin-right:6px;"></span>{legend_label} 2025</span>
    </div>
    '''


def build_ds_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    return _build_clustered_chart(
        y1_ds_mbnt_by_nhom_diaban(date_2025), y_ds_mbnt_by_nhom_diaban(selected_date), "dia_ban",
        "doanh_so", 1_000_000_000, "bn", "Doanh Số", nhom_filter
    )


def build_ds_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    df_2025 = y1_ds_mbnt_by_nhom_pkkh(date_2025)
    df_2026 = y_ds_mbnt_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED)]
    return _build_clustered_chart(df_2025, df_2026, "pkkh", "doanh_so", 1_000_000_000, "bn", "Doanh Số", nhom_filter)


def build_nim_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    return _build_clustered_chart(
        y1_nim_by_nhom_diaban(date_2025), y_nim_by_nhom_diaban(selected_date), "dia_ban",
        "nim", 1, "", "NIM", nhom_filter
    )


def build_nim_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    df_2025 = y1_nim_by_nhom_pkkh(date_2025)
    df_2026 = y_nim_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED)]
    return _build_clustered_chart(df_2025, df_2026, "pkkh", "nim", 1, "", "NIM", nhom_filter)


def build_ln_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    target = kh_mbnt_by_nhom_diaban(selected_date)
    return _build_clustered_chart(
        y1_ln_mbnt_by_nhom_diaban(date_2025), y_ln_mbnt_by_nhom_diaban(selected_date), "dia_ban",
        "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, target_series=target
    )


def build_ln_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    df_2025 = y1_ln_mbnt_by_nhom_pkkh(date_2025)
    df_2026 = y_ln_mbnt_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED)]
    target = kh_mbnt_by_nhom_pkkh(selected_date)
    return _build_clustered_chart(
        df_2025, df_2026, "pkkh", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, target_series=target
    )


def build_ln_hdls_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    return _build_clustered_chart(
        y1_ln_hdls_by_nhom_diaban(date_2025), y_ln_hdls_by_nhom_diaban(selected_date), "dia_ban",
        "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter
    )


def build_ln_hdls_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    df_2025 = y1_ln_hdls_by_nhom_pkkh(date_2025)
    df_2026 = y_ln_hdls_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED)]
    return _build_clustered_chart(df_2025, df_2026, "pkkh", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter)


def build_ds_hdls_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    return _build_clustered_chart(
        y1_ds_hdls_by_nhom_diaban(date_2025), y_ds_hdls_by_nhom_diaban(selected_date), "dia_ban",
        "doanh_so", 1_000_000, "M", "Doanh Số", nhom_filter
    )


def build_ds_hdls_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None) -> str:
    df_2025 = y1_ds_hdls_by_nhom_pkkh(date_2025)
    df_2026 = y_ds_hdls_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED)]
    return _build_clustered_chart(df_2025, df_2026, "pkkh", "doanh_so", 1_000_000, "M", "Doanh Số", nhom_filter)


CN_TRONG_DIEM_COLUMNS = [
    "STT", "Chi nhánh", "Cán bộ phụ trách", "KH KDNTPS 2026 (tr đồng)",
    "KQ MBNT (tr đồng)", "KQ HDLS (tr đồng)", "KQ TDPS (tr đồng)",
    "KQ PSHH (tr đồng)", "KQ KDNT&PS (tr đồng)", "% tháng", "% năm",
]
CN_TRONG_DIEM_VALUE_COLUMNS = [
    "KH KDNTPS 2026 (tr đồng)", "KQ MBNT (tr đồng)", "KQ HDLS (tr đồng)",
    "KQ TDPS (tr đồng)", "KQ PSHH (tr đồng)", "KQ KDNT&PS (tr đồng)",
]
CN_TRONG_DIEM_PCT_COLUMNS = ["% tháng", "% năm"]


def build_cn_trong_diem_table(selected_date: str, nhom: str) -> str:
    df = branch_table(selected_date)
    sub = df[df["Nhóm phụ trách"] == nhom].sort_values("STT")[CN_TRONG_DIEM_COLUMNS].copy()
    sub = sub[sub["KQ KDNT&PS (tr đồng)"].fillna(0) != 0]
    stt_colors = compute_stt_gradient_colors(sub)
    sub["STT"] = sub["STT"].map(lambda v: f"{v:.0f}" if pd.notna(v) else "")
    for col in CN_TRONG_DIEM_VALUE_COLUMNS:
        sub[col] = sub[col].map(lambda v: f"{v:,.2f}" if pd.notna(v) else "")
    for col in CN_TRONG_DIEM_PCT_COLUMNS:
        sub[col] = sub[col].map(lambda v: f"{v * 100:,.2f}%" if pd.notna(v) else "")
    return render_table(sub, stt_colors=stt_colors)


CN_CANBO_COLUMNS = [
    "STT", "Thay đổi (m/m)", "Cán bộ", "KH KDNT&PS 2026 (tr đồng)",
    "KQ MBNT (tr đồng)", "KQ HĐLS (tr đồng)", "KQ TDPS (tr đồng)",
    "KQ PSHH (tr đồng)", "KQ KDNT&PS (tr đồng)", "% tháng", "% năm",
]
CN_CANBO_VALUE_COLUMNS = [
    "KH KDNT&PS 2026 (tr đồng)", "KQ MBNT (tr đồng)", "KQ HĐLS (tr đồng)",
    "KQ TDPS (tr đồng)", "KQ PSHH (tr đồng)", "KQ KDNT&PS (tr đồng)",
]
CN_CANBO_PCT_COLUMNS = ["% tháng", "% năm"]


def build_cn_canbo_table(selected_date: str, nhom: str) -> str:
    df = staff_table(selected_date)
    sub = df[df["Nhóm phụ trách"] == nhom].sort_values("STT")[CN_CANBO_COLUMNS].copy()
    sub = sub[sub["KQ KDNT&PS (tr đồng)"].fillna(0) != 0]
    stt_colors = compute_stt_gradient_colors(sub)
    sub["STT"] = sub["STT"].map(lambda v: f"{v:.0f}" if pd.notna(v) else "")
    sub["Thay đổi (m/m)"] = sub["Thay đổi (m/m)"].fillna("")
    for col in CN_CANBO_VALUE_COLUMNS:
        sub[col] = sub[col].map(lambda v: f"{v:,.2f}" if pd.notna(v) else "")
    for col in CN_CANBO_PCT_COLUMNS:
        sub[col] = sub[col].map(lambda v: f"{v * 100:,.2f}%" if pd.notna(v) else "")
    return render_table(sub, stt_colors=stt_colors)


@app.route("/")
def show_table():
    selected_date = request.args.get("date") or latest_date()
    date_2025 = same_day_last_year(selected_date)
    chart_nhom = request.args.get("chart_nhom", "PTKD 1")
    hdls_chart_nhom = request.args.get("hdls_chart_nhom", "PTKD 1")
    cn_trong_diem_nhom = request.args.get("cn_trong_diem_nhom", "PTKD 1")
    cn_canbo_nhom = request.args.get("cn_canbo_nhom", "PTKD 1")

    mbnt_df = bao_cao_ket_qua_mbnt_2025_2026(selected_date)
    hdls_df = bao_cao_ket_qua_hdls_2025_2026(selected_date)

    kpi_cards = build_kpi_row(selected_date, date_2025)
    ds_mbnt_cards = build_ds_mbnt_row(selected_date, date_2025)
    ds_hdls_cards = build_ds_hdls_row(selected_date)
    chart_nhom_arg = chart_nhom
    ds_diaban_chart = build_ds_diaban_chart(selected_date, date_2025, nhom_filter=chart_nhom_arg)
    ds_pkkh_chart = build_ds_pkkh_chart(selected_date, date_2025, nhom_filter=chart_nhom_arg)
    nim_diaban_chart = build_nim_diaban_chart(selected_date, date_2025, nhom_filter=chart_nhom_arg)
    nim_pkkh_chart = build_nim_pkkh_chart(selected_date, date_2025, nhom_filter=chart_nhom_arg)
    ln_diaban_chart = build_ln_diaban_chart(selected_date, date_2025, nhom_filter=chart_nhom_arg)
    ln_pkkh_chart = build_ln_pkkh_chart(selected_date, date_2025, nhom_filter=chart_nhom_arg)
    hdls_chart_nhom_arg = hdls_chart_nhom
    ln_hdls_diaban_chart = build_ln_hdls_diaban_chart(selected_date, date_2025, nhom_filter=hdls_chart_nhom_arg)
    ln_hdls_pkkh_chart = build_ln_hdls_pkkh_chart(selected_date, date_2025, nhom_filter=hdls_chart_nhom_arg)
    ds_hdls_diaban_chart = build_ds_hdls_diaban_chart(selected_date, date_2025, nhom_filter=hdls_chart_nhom_arg)
    ds_hdls_pkkh_chart = build_ds_hdls_pkkh_chart(selected_date, date_2025, nhom_filter=hdls_chart_nhom_arg)

    mbnt_pct_sections = build_sections(
        get_top_bottom_by_group_mbnt(mbnt_df), "▲LN%",
        "Top KH tăng trưởng LN cao nhất", "Top KH tăng trưởng LN thấp nhất"
    )
    mbnt_abs_sections = build_sections(
        get_top_bottom_by_group_abs_mbnt(mbnt_df), "▲LN",
        "Top KH tăng trưởng LN tuyệt đối cao nhất", "Top KH tăng trưởng LN tuyệt đối thấp nhất"
    )
    hdls_pct_sections = build_sections(
        get_top_bottom_by_group_hdls(hdls_df), "▲LN%",
        "Top KH tăng trưởng LN cao nhất", "Top KH tăng trưởng LN thấp nhất"
    )
    hdls_abs_sections = build_sections(
        get_top_bottom_by_group_abs_hdls(hdls_df), "▲LN",
        "Top KH tăng trưởng LN tuyệt đối cao nhất", "Top KH tăng trưởng LN tuyệt đối thấp nhất"
    )

    cn_trong_diem_table = build_cn_trong_diem_table(selected_date, cn_trong_diem_nhom)
    cn_canbo_table = build_cn_canbo_table(selected_date, cn_canbo_nhom)

    date_table_df = get_date_table()
    date_options = "".join(
        f'<option value="{iso}"{" selected" if iso == selected_date else ""}>{display}</option>'
        for iso, display in zip(
            date_table_df["date"].dt.strftime("%Y-%m-%d"),
            date_table_df["date"].dt.strftime("%A, %B %d, %Y"),
        )
    )

    return f"""
    <html>
    <head>
        <title>Bao Cao MBNT & HDLS 2025-2026</title>
        <style>{THEME_CSS}</style>
        <script>{THEME_JS}</script>
    </head>
    <body>
        <div class="header-row">
            <div class="header-logo">
                <img src="{LOGO_DATA_URI}" alt="BIDV Global Markets" class="header-logo-img" />
            </div>
            <div class="header-title-area">
                <h1 class="report-title">Báo cáo chi tiết Phát triển kinh doanh</h1>
                <select class="date-pill" onchange="onDateChange(this.value)">
                    {date_options}
                </select>
            </div>
            <button class="toggle-btn" onclick="toggleTheme()">☀/☾</button>
        </div>

        <div class="ribbon ribbon-1">Kết quả mua bán ngoại tệ và phái sinh</div>

        <div class="kpi-row">{''.join(kpi_cards)}</div>

        <div class="ribbon ribbon-2">Mua bán ngoại tệ</div>
        <div class="ribbon ribbon-3">Theo nhóm phụ trách</div>

        <div class="kpi-row">{''.join(ds_mbnt_cards)}</div>

        <div style="position:relative; margin-bottom:10px;">
            <div style="position:absolute; left:0; top:50%; transform:translateY(-50%); font-style:italic; font-size:12px; color:var(--primary); text-decoration:underline;">*Doanh số và lợi nhuận của mua bán ngoại tệ sau chia sẻ</div>
            <div class="ribbon ribbon-3" style="margin:0 auto;">Theo địa bàn và phân khúc khách hàng</div>
        </div>

        <div class="charts-panel">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Nhóm phụ trách</label>
                    <select class="filter-select" onchange="onChartNhomChange(this.value)">
                        <option value="PTKD 1"{" selected" if chart_nhom == "PTKD 1" else ""}>PTKD 1</option>
                        <option value="PTKD 2"{" selected" if chart_nhom == "PTKD 2" else ""}>PTKD 2</option>
                        <option value="VPV"{" selected" if chart_nhom == "VPV" else ""}>VPV</option>
                    </select>
                </div>
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="nim">NIM</option>
                        <option value="ln">Lợi Nhuận</option>
                    </select>
                </div>
            </div>

            <div id="chart-ds" style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Doanh số của mua bán ngoại tệ theo địa bàn</h2>
                    {ds_diaban_chart}
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Doanh số của mua bán ngoại tệ theo PKKH</h2>
                    {ds_pkkh_chart}
                </div>
            </div>

            <div id="chart-nim" style="display:none; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">NIM của mua bán ngoại tệ theo địa bàn</h2>
                    {nim_diaban_chart}
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">NIM của mua bán ngoại tệ theo PKKH</h2>
                    {nim_pkkh_chart}
                </div>
            </div>

            <div id="chart-ln" style="display:none; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Lợi nhuận của mua bán ngoại tệ theo địa bàn</h2>
                    {ln_diaban_chart}
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Lợi nhuận của mua bán ngoại tệ theo PKKH</h2>
                    {ln_pkkh_chart}
                </div>
            </div>
        </div>

        <div style="position:relative; margin-bottom:10px;">
            <div style="position:absolute; left:0; top:50%; transform:translateY(-50%); font-style:italic; font-size:12px; color:var(--primary); text-decoration:underline;">*Bảng tính chỉ hiện thị những địa bàn và PKKH có phát sinh giao dịch</div>
            <div class="ribbon ribbon-3" style="margin:0 auto;">Theo Top khách hàng</div>
        </div>
        <div class="charts-panel">
            <div class="filter-row">
                <div class="filter-group">
                    <label class="filter-label">Nhóm phụ trách</label>
                    <select class="filter-select" onchange="onMbntRankingGroupChange(this.value)">
                        <option value="PTKD 1">PTKD 1</option>
                        <option value="PTKD 2">PTKD 2</option>
                        <option value="VPV">VPV</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label class="filter-label">Loại tăng trưởng</label>
                    <select class="filter-select" onchange="onMbntRankingChange(this.value)">
                        <option value="pct">Phần trăm</option>
                        <option value="abs">Tuyệt đối</option>
                    </select>
                </div>
            </div>

            <div id="mbnt-pct-sections">{''.join(mbnt_pct_sections)}</div>
            <div id="mbnt-abs-sections" style="display:none;">{''.join(mbnt_abs_sections)}</div>
        </div>

        <div class="ribbon ribbon-2">Hoán đổi lãi suất</div>
        <div class="ribbon ribbon-3">Theo nhóm phụ trách</div>

        <div class="kpi-row">{''.join(ds_hdls_cards)}</div>

        <div style="position:relative; margin-bottom:10px;">
            <div style="position:absolute; left:0; top:50%; transform:translateY(-50%); font-style:italic; font-size:12px; color:var(--primary); text-decoration:underline;">*Doanh số và lợi nhuận của hoán đổi lãi suất sau chia sẻ</div>
            <div class="ribbon ribbon-3" style="margin:0 auto;">Theo địa bàn và phân khúc khách hàng</div>
        </div>

        <div class="charts-panel">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Nhóm phụ trách</label>
                    <select class="filter-select" onchange="onHdlsChartNhomChange(this.value)">
                        <option value="PTKD 1"{" selected" if hdls_chart_nhom == "PTKD 1" else ""}>PTKD 1</option>
                        <option value="PTKD 2"{" selected" if hdls_chart_nhom == "PTKD 2" else ""}>PTKD 2</option>
                        <option value="VPV"{" selected" if hdls_chart_nhom == "VPV" else ""}>VPV</option>
                    </select>
                </div>
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onHdlsChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                    </select>
                </div>
            </div>

            <div id="hdls-chart-ds" style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Doanh số của hoán đổi lãi suất theo địa bàn</h2>
                    {ds_hdls_diaban_chart}
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Doanh số của hoán đổi lãi suất theo PKKH</h2>
                    {ds_hdls_pkkh_chart}
                </div>
            </div>

            <div id="hdls-chart-ln" style="display:none; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Lợi nhuận của hoán đổi lãi suất theo địa bàn</h2>
                    {ln_hdls_diaban_chart}
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Lợi nhuận của hoán đổi lãi suất theo PKKH</h2>
                    {ln_hdls_pkkh_chart}
                </div>
            </div>
        </div>

        <div style="position:relative; margin-bottom:10px;">
            <div style="position:absolute; left:0; top:50%; transform:translateY(-50%); font-style:italic; font-size:12px; color:var(--primary); text-decoration:underline;">*Bảng tính chỉ hiện thị những địa bàn và PKKH có phát sinh giao dịch</div>
            <div class="ribbon ribbon-3" style="margin:0 auto;">Theo Top khách hàng</div>
        </div>
        <div class="charts-panel">
            <div class="filter-row">
                <div class="filter-group">
                    <label class="filter-label">Nhóm phụ trách</label>
                    <select class="filter-select" onchange="onHdlsRankingGroupChange(this.value)">
                        <option value="PTKD 1">PTKD 1</option>
                        <option value="PTKD 2">PTKD 2</option>
                        <option value="VPV">VPV</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label class="filter-label">Loại tăng trưởng</label>
                    <select class="filter-select" onchange="onHdlsRankingChange(this.value)">
                        <option value="pct">Phần trăm</option>
                        <option value="abs">Tuyệt đối</option>
                    </select>
                </div>
            </div>

            <div id="hdls-pct-sections">{''.join(hdls_pct_sections)}</div>
            <div id="hdls-abs-sections" style="display:none;">{''.join(hdls_abs_sections)}</div>
        </div>

        <div class="ribbon ribbon-1">Kết quả KDNT&amp;PS của các chi nhánh trọng điểm</div>
        <div class="charts-panel">
            <div class="filter-row">
                <div class="filter-group">
                    <label class="filter-label">Nhóm phụ trách</label>
                    <select class="filter-select" onchange="onCnTrongDiemNhomChange(this.value)">
                        <option value="PTKD 1"{" selected" if cn_trong_diem_nhom == "PTKD 1" else ""}>PTKD 1</option>
                        <option value="PTKD 2"{" selected" if cn_trong_diem_nhom == "PTKD 2" else ""}>PTKD 2</option>
                        <option value="VPV"{" selected" if cn_trong_diem_nhom == "VPV" else ""}>VPV</option>
                    </select>
                </div>
            </div>
            <div class="table-card">{cn_trong_diem_table}</div>
        </div>

        <div class="ribbon ribbon-1">Kết quả KDNT&amp;PS của cán bộ PTKD</div>
        <div class="charts-panel">
            <div class="filter-row">
                <div class="filter-group">
                    <label class="filter-label">Nhóm phụ trách</label>
                    <select class="filter-select" onchange="onCnCanboNhomChange(this.value)">
                        <option value="PTKD 1"{" selected" if cn_canbo_nhom == "PTKD 1" else ""}>PTKD 1</option>
                        <option value="PTKD 2"{" selected" if cn_canbo_nhom == "PTKD 2" else ""}>PTKD 2</option>
                        <option value="VPV"{" selected" if cn_canbo_nhom == "VPV" else ""}>VPV</option>
                    </select>
                </div>
            </div>
            <div class="table-card">{cn_canbo_table}</div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)