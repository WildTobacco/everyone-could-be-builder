import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import base64
import calendar
import colorsys
import glob
import math
import os
import subprocess
import tempfile
from urllib.parse import quote

import numpy as np
import pandas as pd
import pymupdf
from flask import Flask, jsonify, request
from PIL import Image, ImageChops

LOGO_PATH = str(Path(__file__).resolve().parent / "logo moi.png")
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
from calculations.top_kh_mbnt_by_value import (
    get_top_bottom_by_group_ds as get_top_bottom_by_value_ds_mbnt,
    get_top_bottom_by_group_ln as get_top_bottom_by_value_ln_mbnt,
    daily_customer_df as mbnt_daily_customer_df,
    get_top_bottom_by_group_ds_daily as get_top_bottom_by_value_ds_mbnt_daily,
    get_top_bottom_by_group_ln_daily as get_top_bottom_by_value_ln_mbnt_daily,
)
from calculations.top_kh_hdls_by_value import (
    get_top_bottom_by_group_ds as get_top_bottom_by_value_ds_hdls,
    get_top_bottom_by_group_ln as get_top_bottom_by_value_ln_hdls,
    daily_customer_df as hdls_daily_customer_df,
    get_top_bottom_by_group_ds_daily as get_top_bottom_by_value_ds_hdls_daily,
    get_top_bottom_by_group_ln_daily as get_top_bottom_by_value_ln_hdls_daily,
)
from calculations.tong_ln_nhom import tong_ln_nhom
from calculations.ln_luy_ke_kdntps import ln_luy_ke_kdntps_by_nhom
from calculations.ht_thang_nam import compute_ht_thang_nam
from calculations.tong_ds_mbnt_ytd import tong_ds_mbnt_ytd_by_nhom
from calculations.tong_ln_mbnt_ytd import tong_ln_mbnt_ytd_by_nhom
from calculations.ds_mbnt_ngay_by_nhom import ds_mbnt_ngay_by_nhom
from calculations.ln_mbnt_ngay_by_nhom import ln_mbnt_ngay_by_nhom
from calculations.nim_mbnt_spot_ngay_by_nhom import nim_mbnt_buy_spot_by_nhom, nim_mbnt_sell_spot_by_nhom, nim_mbnt_ngay_by_nhom
from calculations.daily_stacked import (
    ds_mbnt_stacked, ln_mbnt_stacked, ds_hdls_stacked, ln_hdls_stacked,
    ln_tdps_stacked, ds_tdps_stacked,
)
from calculations.tdps_ngay_by_nhom import (
    ln_tdps_ngay_by_nhom, so_du_tdps_ngay_by_nhom, so_du_tdps_binh_quan_by_nhom,
    so_du_irs_binh_quan_by_nhom, so_du_ccs_binh_quan_by_nhom,
)
from calculations.so_du_hdls_ngay_by_nhom import (
    so_du_hdls_ngay_by_nhom, so_du_ccs_ngay_by_nhom, so_du_irs_ngay_by_nhom,
    so_du_hdls_binh_quan_by_nhom, so_du_ccs_binh_quan_by_nhom, so_du_irs_binh_quan_by_nhom,
)
from calculations.hoanthanh_kh_ln_tdps import (
    hoanthanh_kh_ln_tdps, ke_hoach_ln_tdps_thang, ke_hoach_ln_tdps_nam, ht_thang_ln_tdps_pct,
    _ln_current_and_kh_per_day as _ln_tdps_current_and_kh_per_day,
)
from calculations.ln_tdps_luy_ke_by_nhom import ln_tdps_luy_ke_by_nhom
from calculations.ds_ln_pshh import (
    ds_pshh_tlhh_luy_ke, ds_pshh_otc_luy_ke, ln_pshh_luy_ke,
    y1_ds_pshh_tlhh, y1_ds_pshh_otc, y1_ln_pshh,
)
from calculations.ke_hoach_ln_pshh import ke_hoach_ln_pshh_nam, ke_hoach_ln_pshh_thang
from calculations.y_pshh_nhom_diaban_pkkh import (
    ds_pshh_tlhh_by_nhom, ds_pshh_otc_by_nhom, ln_pshh_by_nhom,
    ds_pshh_tlhh_by_nhom_diaban, ds_pshh_tlhh_by_nhom_pkkh,
    ds_pshh_otc_by_nhom_diaban, ds_pshh_otc_by_nhom_pkkh,
    ln_pshh_by_nhom_diaban, ln_pshh_by_nhom_pkkh,
)
from calculations.y1_pshh_nhom_diaban_pkkh import (
    y1_ds_pshh_tlhh_by_nhom, y1_ds_pshh_otc_by_nhom, y1_ln_pshh_by_nhom,
    y1_ds_pshh_tlhh_by_nhom_diaban, y1_ds_pshh_tlhh_by_nhom_pkkh,
    y1_ds_pshh_otc_by_nhom_diaban, y1_ds_pshh_otc_by_nhom_pkkh,
    y1_ln_pshh_by_nhom_diaban, y1_ln_pshh_by_nhom_pkkh,
)
from calculations.daily_pshh_nhom_diaban_pkkh import (
    daily_ds_pshh_tlhh_by_nhom, daily_ds_pshh_otc_by_nhom, daily_ln_pshh_by_nhom,
    daily_ds_pshh_tlhh_by_nhom_diaban, daily_ds_pshh_tlhh_by_nhom_pkkh,
    daily_ds_pshh_otc_by_nhom_diaban, daily_ds_pshh_otc_by_nhom_pkkh,
    daily_ln_pshh_by_nhom_diaban, daily_ln_pshh_by_nhom_pkkh,
)
from calculations.ds_tdps import (
    ds_tdps_ngay_by_nhom, ds_tdps_luy_ke_by_nhom, ds_tdps_pct_change_by_nhom,
)
from calculations.y1_ln_tdps_by_nhom import ln_tdps_pct_change_by_nhom, y1_ln_tdps_by_nhom
from calculations.ds_hdls_ngay_by_nhom import ds_hdls_ngay_by_nhom
from calculations.ln_hdls_ngay_by_nhom import ln_hdls_ngay_by_nhom
from calculations.hoanthanh_kh_ds_hdls import (
    hoanthanh_kh_ds_hdls, ht_thang_ds_hdls_pct, _ds_current_and_kh_per_day as _ds_hdls_current_and_kh_per_day,
)
from calculations.hoanthanh_kh_ln_hdls import (
    hoanthanh_kh_ln_hdls, ht_thang_ln_hdls_pct, _ln_current_and_kh_per_day as _ln_hdls_current_and_kh_per_day,
)
from calculations.hoanthanh_kh_ds_mbnt import (
    hoanthanh_kh_ds_mbnt, _fmt_gap_value, ht_thang_ds_mbnt_pct,
    _ds_current_and_kh_per_day as _ds_mbnt_current_and_kh_per_day,
)
from calculations.hoanthanh_kh_ln_mbnt import (
    hoanthanh_kh_ln_mbnt, ht_thang_ln_mbnt_pct, _ln_current_and_kh_per_day as _ln_mbnt_current_and_kh_per_day,
)
from calculations.y1_tong_ds_mbnt_nhom import compute_y1_tong_ds_mbnt_nhom
from calculations.y1_tong_ln_mbnt_nhom import compute_y1_tong_ln_mbnt_nhom
from calculations.ht_ds_mbnt_nam import ke_hoach_ds_mbnt_nam, ke_hoach_ds_mbnt_thang
from calculations.working_days_ytd import working_days_ytd
from calculations.ht_ln_mbnt_nam import ke_hoach_ln_mbnt_nam, ke_hoach_ln_mbnt_thang
from calculations.mbnt_forecast_end_of_month import (
    hoanthanh_kh_ds_mbnt_forecast_gap, hoanthanh_kh_ln_mbnt_forecast_gap,
    ds_mbnt_forecast_end_of_month_by_nhom, ln_mbnt_forecast_end_of_month_by_nhom,
)
from calculations.hdls_forecast_end_of_month import (
    hoanthanh_kh_ds_hdls_forecast_gap, hoanthanh_kh_ln_hdls_forecast_gap,
    ds_hdls_forecast_end_of_month_by_nhom, ln_hdls_forecast_end_of_month_by_nhom,
)
from calculations.tdps_forecast_end_of_month import (
    hoanthanh_kh_ln_tdps_forecast_gap, ln_tdps_forecast_end_of_month_by_nhom,
    ds_tdps_forecast_end_of_month_by_nhom,
)
from calculations.y1_nim_mbnt_nhom_diaban_pkkh import (
    y1_nim_mbnt_nhom_diaban_pkkh, y1_nim_by_nhom_diaban, y1_nim_by_nhom_pkkh,
    y1_nim_diaban_pooled, y1_nim_pkkh_pooled,
)
from calculations.y_nim_mbnt_nhom_diaban_pkkh import (
    y_nim_mbnt_nhom_diaban_pkkh, y_nim_by_nhom_diaban, y_nim_by_nhom_pkkh,
    y_nim_diaban_pooled, y_nim_pkkh_pooled,
    y_doanhso_by_nhom, y_loinhuan_by_nhom,
)
from calculations.y1_ln_mbnt_nhom_diaban_pkkh import y1_ln_mbnt_by_nhom_diaban, y1_ln_mbnt_by_nhom_pkkh
from calculations.y_ln_mbnt_nhom_diaban_pkkh import y_ln_mbnt_by_nhom_diaban, y_ln_mbnt_by_nhom_pkkh
from calculations.KH_mbnt_nhom_dia_ban_2026 import kh_mbnt_by_nhom_diaban
from calculations.KH_hdls_nhom_dia_ban_2026 import kh_hdls_by_nhom_diaban
from calculations.KH_tdps_nhom_dia_ban_2026 import kh_tdps_by_nhom_diaban
from calculations.KH_mbnt_pkkh_2026 import kh_mbnt_by_nhom_pkkh, kh_ds_mbnt_by_nhom_pkkh
from calculations.y1_ds_mbnt_nhom_diaban_pkkh import y1_ds_mbnt_by_nhom_diaban, y1_ds_mbnt_by_nhom_pkkh
from calculations.y_ds_mbnt_nhom_diaban_pkkh import y_ds_mbnt_by_nhom_diaban, y_ds_mbnt_by_nhom_pkkh
from calculations.tong_ds_hdls_ytd_nhom import tong_ds_hdls_ytd_by_nhom
from calculations.tong_ln_hdls_ytd_nhom import tong_ln_hdls_ytd_by_nhom
from calculations.nim_hdls_binh_quan_nhom import nim_hdls_binh_quan_by_nhom
from calculations.nim_tdps_binh_quan_nhom import nim_tdps_binh_quan_by_nhom
from calculations.nim_hdls_ngay_nhom import nim_hdls_ngay_by_nhom
from calculations.nim_tdps_ngay_nhom import nim_tdps_ngay_by_nhom
from calculations.y1_ds_hdls_nhom_diaban_pkkh import ds_hdls_pct_change_by_nhom, y1_ds_hdls_by_nhom
from calculations.y1_ln_hdls_nhom_diaban_pkkh import ln_hdls_pct_change_by_nhom, y1_ln_hdls_by_nhom
from calculations.ds_hdls_hoan_thanh import ds_hdls_hoan_thanh, _ke_hoach_ds_hdls_nam, ke_hoach_ds_hdls_thang
from calculations.ln_hdls_hoan_thanh import ln_hdls_hoan_thanh, ke_hoach_ln_hdls_thang, _ke_hoach_ln_hdls_nam
from calculations.y1_ln_hdls_nhom_diaban_pkkh import y1_ln_hdls_by_nhom_diaban, y1_ln_hdls_by_nhom_pkkh
from calculations.y_ln_hdls_nhom_diaban_pkkh import y_ln_hdls_by_nhom_diaban, y_ln_hdls_by_nhom_pkkh
from calculations.y1_ds_hdls_nhom_diaban_pkkh import (
    y1_ds_hdls_by_nhom_diaban, y1_ds_hdls_by_nhom_pkkh,
    y1_ds_hdls_irs_ccs_by_nhom_diaban, y1_ds_hdls_irs_ccs_by_nhom_pkkh,
)
from calculations.y_ds_hdls_nhom_diaban_pkkh import (
    y_ds_hdls_by_nhom_diaban, y_ds_hdls_by_nhom_pkkh,
    y_ds_hdls_irs_ccs_by_nhom_diaban, y_ds_hdls_irs_ccs_by_nhom_pkkh,
)
from calculations.daily_diaban_pkkh import (
    daily_ds_mbnt_by_nhom_diaban, daily_ds_mbnt_by_nhom_pkkh,
    daily_ln_mbnt_by_nhom_diaban, daily_ln_mbnt_by_nhom_pkkh,
    daily_nim_by_nhom_diaban, daily_nim_by_nhom_pkkh,
    daily_nim_diaban_pooled, daily_nim_pkkh_pooled,
    daily_ds_hdls_by_nhom_diaban, daily_ds_hdls_by_nhom_pkkh,
    daily_ds_hdls_irs_ccs_by_nhom_diaban, daily_ds_hdls_irs_ccs_by_nhom_pkkh,
    daily_ln_hdls_by_nhom_diaban, daily_ln_hdls_by_nhom_pkkh,
    daily_ds_tdps_by_nhom_diaban, daily_ds_tdps_by_nhom_pkkh,
    daily_ln_tdps_by_nhom_diaban, daily_ln_tdps_by_nhom_pkkh,
)
from calculations.tdps_diaban_pkkh import (
    y_ds_tdps_by_nhom_diaban, y_ds_tdps_by_nhom_pkkh,
    y_ln_tdps_by_nhom_diaban, y_ln_tdps_by_nhom_pkkh,
    y1_ds_tdps_by_nhom_diaban, y1_ds_tdps_by_nhom_pkkh,
    y1_ln_tdps_by_nhom_diaban, y1_ln_tdps_by_nhom_pkkh,
    so_du_tdps_by_nhom_diaban, so_du_tdps_by_nhom_pkkh,
    so_du_tdps_luy_ke_by_nhom_diaban, so_du_tdps_luy_ke_by_nhom_pkkh,
)
from calculations.so_du_hdls_diaban_pkkh import (
    so_du_hdls_irs_ccs_ngay_by_nhom_diaban, so_du_hdls_irs_ccs_ngay_by_nhom_pkkh,
    so_du_hdls_irs_ccs_luy_ke_by_nhom_diaban, so_du_hdls_irs_ccs_luy_ke_by_nhom_pkkh,
    so_du_hdls_luy_ke_by_nhom_diaban, so_du_hdls_luy_ke_by_nhom_pkkh,
)
from calculations.so_du_pstc_diaban_pkkh import (
    so_du_tdps_pstc_by_diaban, so_du_tdps_pstc_by_pkkh,
    so_du_hdls_pstc_by_diaban, so_du_hdls_pstc_by_pkkh,
    so_du_hdls_stack_pstc_by_diaban, so_du_hdls_stack_pstc_by_pkkh,
    so_du_ccs_pstc_by_diaban, so_du_ccs_pstc_by_pkkh,
    so_du_irs_pstc_by_diaban, so_du_irs_pstc_by_pkkh,
    so_du_tdps_pstc_ngay_by_diaban, so_du_tdps_pstc_ngay_by_pkkh,
    so_du_hdls_pstc_ngay_by_diaban, so_du_hdls_pstc_ngay_by_pkkh,
    so_du_ccs_pstc_ngay_by_diaban, so_du_ccs_pstc_ngay_by_pkkh,
    so_du_irs_pstc_ngay_by_diaban, so_du_irs_pstc_ngay_by_pkkh,
)
from calculations.nim_hdls_diaban_pkkh import (
    nim_hdls_by_nhom_diaban, nim_hdls_by_nhom_pkkh, nim_hdls_diaban_pooled, nim_hdls_pkkh_pooled,
)
from calculations.nim_tdps_diaban_pkkh import (
    nim_tdps_by_nhom_diaban, nim_tdps_by_nhom_pkkh, nim_tdps_diaban_pooled, nim_tdps_pkkh_pooled,
)
from calculations.nim_hdls_ngay_diaban_pkkh import (
    nim_hdls_ngay_by_nhom_diaban, nim_hdls_ngay_by_nhom_pkkh,
    nim_hdls_ngay_diaban_pooled, nim_hdls_ngay_pkkh_pooled,
)
from calculations.nim_tdps_ngay_diaban_pkkh import (
    nim_tdps_ngay_by_nhom_diaban, nim_tdps_ngay_by_nhom_pkkh,
    nim_tdps_ngay_diaban_pooled, nim_tdps_ngay_pkkh_pooled,
)
from calculations.date_table import get_date_table, latest_date, same_day_last_year, previous_date
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
# Single canonical per-nhóm color, used everywhere a chart draws one bar/ring/line per nhóm
# phụ trách (as opposed to charts that color-encode something else, like year in the 2025-vs-
# 2026 clustered charts) — PTKD 1/2/VPV picked by the user, TOTAL a distinct navy so it doesn't
# collide with PTKD 1's teal, PTKD 2's gold, or VPV's grey.
NHOM_COLORS = {"PTKD 1": "#006d68", "PTKD 2": "#ffc72c", "VPV": "#33500F", "TOTAL": "#2E5F8C"}
HT_RING_COLORS = [NHOM_COLORS["PTKD 1"], NHOM_COLORS["PTKD 2"], NHOM_COLORS["VPV"], NHOM_COLORS["TOTAL"]]
# 2025 counterpart for the same "color=nhóm, opacity=year" clustered charts — a literal override
# color/opacity pair for nhóm with one set, instead of the shared base-color-at-55%-opacity
# convention every other nhóm still uses. Currently just VPV, per user request.
NHOM_COLORS_Y1_OVERRIDE = {"VPV": "#AEC3A2"}


def _y1_bar_fill_attrs(nhom: str, base_color: str) -> str:
    """SVG fill (+ opacity, if applicable) attributes for a nhóm's 2025 bar in the clustered
    dia_ban/pkkh and NIM charts."""
    override = NHOM_COLORS_Y1_OVERRIDE.get(nhom)
    return f'fill="{override}"' if override else f'fill="{base_color}" opacity="0.55"'
CHART_TARGET_WIDTH = 620  # approx usable width of one chart-card when 2 charts sit side by side

DATE_OPTIONS_WORKING_DAYS = 10  # Kỳ báo cáo shows the last 2 working weeks
# An export holds one day's figures and has no server to re-render, so Kỳ báo cáo cannot
# actually filter there: picking another date reloaded the static file and snapped straight
# back to the exported one. The dropdown is therefore cut to the single exported date and
# disabled, so it reads as the report date rather than a control that silently does nothing.
DATE_OPTIONS_EXPORT_WORKING_DAYS = 1
# Dates kept in Kỳ báo cáo regardless of the last-10-working-days window, e.g. a specific past
# report date someone still needs to pull up without having to bookmark/URL it in.
DATE_OPTIONS_PINNED = {"2026-07-31"}

# pandas dayofweek: Monday=0 .. Sunday=6, matching Vietnamese Thứ 2 .. Chủ nhật
WEEKDAY_LABELS = {
    0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5",
    4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật",
}
PKKH_EXCLUDED = {"KH ao", "KH vang lai", "KHCN", "KHACH HANG KHAC"}
# MBNT's own PKKH charts keep "KH vang lai" and "KHCN" — every other product still drops all 4.
PKKH_EXCLUDED_MBNT = PKKH_EXCLUDED - {"KH vang lai", "KHCN"}

NAV_ICON_BARCHART = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<line x1="18" y1="20" x2="18" y2="10"></line>'
    '<line x1="12" y1="20" x2="12" y2="4"></line>'
    '<line x1="6" y1="20" x2="6" y2="14"></line>'
    '</svg>'
)
NAV_ICON_BRIEFCASE = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>'
    '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>'
    '</svg>'
)
NAV_ICON_USERS = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>'
    '<circle cx="9" cy="7" r="4"></circle>'
    '<path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>'
    '<path d="M16 3.13a4 4 0 0 1 0 7.75"></path>'
    '</svg>'
)
NAV_ICON_TRENDING = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>'
    '<polyline points="17 6 23 6 23 12"></polyline>'
    '</svg>'
)

NAV_TABS = [
    ("sanpham", NAV_ICON_BARCHART, "Tổng quan"),
    ("nhom_pt", NAV_ICON_TRENDING, "Nhóm phụ trách"),
    ("nhomphutrach", NAV_ICON_BRIEFCASE, "Kết quả chi nhánh/cán bộ"),
    ("khachhang", NAV_ICON_USERS, "Khách hàng"),
]

THEME_CSS = """
* { box-sizing: border-box; }
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
  --section-gap: 14px;
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
html, body { height: 100%; margin: 0; padding: 0; }
body {
  background: var(--background); color: var(--foreground);
  font-family: system-ui, sans-serif;
}

.app-shell { display: flex; height: 100vh; overflow: hidden; }
.sidebar {
  width: 220px; flex-shrink: 0;
  height: 100vh; overflow-y: auto;
  background: var(--card);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  padding: 20px 0;
}
.sidebar-brand { padding: 0 20px 24px 20px; display: flex; align-items: center; gap: 10px; }
.sidebar-brand-logo { height: 48px; width: auto; display: block; }
.sidebar-brand-title { font-size: 16px; font-weight: 800; color: var(--primary); line-height: 1.2; }
.sidebar-brand-sub { font-size: 9px; letter-spacing: 1px; color: var(--muted-foreground); margin-top: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 10px; width: 100%; text-align: left;
  padding: 12px 20px; border: none; background: transparent;
  color: var(--foreground); font-size: 14px; font-weight: 700; cursor: pointer;
  border-left: 3px solid transparent;
}
.nav-item-icon { display: flex; align-items: center; flex-shrink: 0; }
.nav-item:hover { background: var(--muted); }
.nav-item.active {
  background: var(--muted);
  border-left-color: var(--primary);
  color: var(--primary);
  font-weight: 700;
}
.main { flex: 1; min-width: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.topbar {
  display: flex; flex-direction: column; gap: 16px; flex-shrink: 0;
  padding: 20px 32px; border-bottom: 1px solid var(--border);
  background: var(--card);
}
.topbar-row {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.topbar-title { font-size: 22px; font-weight: 800; margin: 0; }
.topbar-sub { font-size: 12px; color: var(--muted-foreground); margin-top: 4px; }
.topbar-actions { display: flex; align-items: center; gap: 12px; }
.topbar-filters { display: flex; align-items: flex-end; gap: 24px; flex-wrap: wrap; }
.topbar-filter-group { display: flex; flex-direction: column; gap: 6px; }
.content { padding: 24px 32px; flex: 1; overflow-y: auto; }
.tab-page { display: block; }

.filter-row {
  display: flex;
  gap: 24px;
  margin-bottom: var(--section-gap);
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
.ribbon {
  text-align: center;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.5px;
  padding: 8px 0;
  border-radius: 6px;
  margin: 0 auto var(--section-gap) auto;
}
.ribbon-1 { width: 70%; background: var(--ribbon-teal); color: var(--ribbon-teal-text); }
.charts-panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: var(--section-gap);
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
  margin-bottom: var(--section-gap);
  flex-wrap: wrap;
}
.kpi-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 14px 20px;
  flex: 1;
  min-width: 300px;
  position: relative;
  /* Clips ::before to the card's own rounded shape exactly (a manually-matched radius on the
     ribbon itself couldn't keep up with the card's curve right at the corner — the ribbon's own
     radius gets shrunk by the browser to fit its 3px height, so it stayed squarer than the
     card's 14px curve and visibly poked past it). Pace-row content used to get clipped by this
     too; since then it's been tightened to a fixed single line with ellipsis overflow, so it no
     longer runs past the card's bottom edge. */
  overflow: hidden;
}
/* Gradient accent line from the scorecard mockup — every kpi-card in the app (Tổng quan and
   Nhóm phụ trách alike) uses the same teal->gold->transparent gradient; this used to be a
   teal->gold variant reserved for data-tone="hdls" only, now applied everywhere so every
   scorecard reads as one consistent style. */
.kpi-card::before {
  content: "";
  /* top:0/left:0/right:0 on an absolutely-positioned child align to the card's padding edge,
     not its border edge — with the card's own 1px border, that left a 1px sliver of the card's
     plain border color showing above and beside the ribbon. Extending by the border width
     (-1px) pulls the ribbon flush to the card's actual outer edge; overflow:hidden above (not
     the ribbon's own border-radius) is what keeps it clipped to the card's curve. */
  position: absolute; top: -1px; left: -1px; right: -1px; height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--ribbon-gold) 65%, transparent);
}
/* Nhóm phụ trách's rows hold 4 cards (PTKD 1/2, VPV, Toàn hệ thống) vs Tổng quan's 3, and each
   now carries the HT tháng/HT năm pace bars too — the shared padding/gaps/font sizes were
   sized for Tổng quan's roomier 3-card row and made 4 cramped/overflowing side by side, so a
   2x2 wrap was tried first. All 4 on one row was asked for instead, so this tightens spacing
   and shrinks the pace-bar text just for Nhóm phụ trách, freeing enough width to keep 4 cards
   on one row at common desktop widths without clipping anything.*/
#tab-nhom_pt .kpi-card { min-width: 200px; padding: 10px 12px; }
#tab-nhom_pt .kpi-row-inner { gap: 8px; }
#tab-nhom_pt .kpi-divider { margin: 0 3px; }
#tab-nhom_pt .kpi-big { font-size: 19.5px !important; }
#tab-nhom_pt .kpi-sub { font-size: 12.5px; }
#tab-nhom_pt .kpi-paces { margin-top: 8px; gap: 5px; }
#tab-nhom_pt .pace-row { gap: 3px; }
/* HT tháng/HT năm (no gap number) stack label above value — narrow enough on its own to need
   the room. "HT so với KH/ngày" (which does carry a gap number) puts label + gap on one row
   via .pace-head-inline, then drops the % to its own line underneath (.pace-value-row) —
   label + gap + % all on one line didn't fit even at the smallest legible font. */
#tab-nhom_pt .pace-head { flex-direction: column; align-items: flex-start; gap: 1px; }
#tab-nhom_pt .pace-head.pace-head-inline {
  flex-direction: row; flex-wrap: nowrap; align-items: baseline;
  justify-content: space-between; gap: 4px;
}
#tab-nhom_pt .pace-head.pace-head-inline .pace-label {
  font-size: 9px; letter-spacing: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
#tab-nhom_pt .pace-head.pace-head-inline .pace-gap { font-size: 10px; flex-shrink: 0; }
#tab-nhom_pt .pace-value-row { font-size: 11.5px; }
#tab-nhom_pt .pace-label { font-size: 10.5px; }
#tab-nhom_pt .pace-value { font-size: 12.5px; }
#tab-nhom_pt .pace-gap { font-size: 11.5px; }
/* Completion pace bars — used by Tổng quan's scorecards (HT tháng/HT năm under each metric)
   and Nhóm phụ trách's HT panels (replacing the old semi-circle gauges). */
.kpi-paces {
  display: flex; flex-direction: column; gap: 10px;
  text-align: left; margin-top: 14px;
}
.pace-row { display: flex; flex-direction: column; gap: 6px; }
.pace-head { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.pace-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
  color: var(--muted-foreground); white-space: nowrap;
}
/* pace-gap sits next to the label in the pace-head row — the absolute so-với-KH/ngày number,
   same ▲/▼ pos/neg coloring as the lũy kế cards' so-với-cùng-kỳ figure. The % value drops to
   its own line (.pace-value-row) underneath when a gap is shown. */
.pace-gap {
  font-variant-numeric: tabular-nums;
  font-size: 12px; font-weight: 700; white-space: nowrap;
}
.pace-gap.pos { color: var(--up); }
.pace-gap.neg { color: var(--down); }
.pace-value-row { text-align: left; }
.kpi-forecast-label {
  text-align: center; font-size: 11px; font-weight: 600;
  color: var(--muted-foreground); margin-top: 6px;
}
.kpi-forecast-title {
  text-align: center; font-size: 13px; font-weight: 800;
  color: var(--down); margin-top: 10px; padding-top: 10px;
  border-top: 1px solid var(--border);
}
.pace-track {
  position: relative; height: 8px; border-radius: 4px;
  background: var(--muted); overflow: hidden;
}
.pace-fill { position: absolute; top: 0; left: 0; bottom: 0; border-radius: 4px; background: var(--up); }
.pace-fill.behind { background: var(--ribbon-gold); }
.pace-fill.low { background: var(--down); }
.pace-value {
  font-variant-numeric: tabular-nums;
  font-size: 13px; font-weight: 700;
  color: var(--foreground); white-space: nowrap;
}
/* NIM/Số dư value blocks (_value_block) — scorecard scope only, ~15% bigger than the HT
   tháng/HT năm pace-bar rows they share styling with, since these are plain figures with no
   track/marker competing for attention in the same row. Label stacks above value instead of
   sharing a row (unlike the pace-bar rows) — long labels like "Số dư B/Q TDPS" next to a
   value on one space-between line overflowed the card width and got clipped by its
   overflow:hidden (needed for the gradient accent line). */
.value-block .pace-head { flex-direction: column; align-items: center; gap: 2px; }
.value-block .pace-label { font-size: 11.5px; }
.value-block .pace-value { font-size: 15px; }
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
  gap: 20px;
}
.kpi-metric {
  flex: 1;
  /* Without this, a flex item won't shrink below its own content's min-content width — an
     unbreakable long value (e.g. Lợi nhuận's "1,840.64bn" vs Doanh số's shorter "34.67bn")
     forced its column wider than its equal share, pushing the row past the card's width and
     getting silently clipped by .kpi-card's overflow:hidden (the HT tháng/HT năm % values lost
     their trailing digits/% on narrower screens). min-width:0 lets both columns actually share
     the row equally; .kpi-big's own overflow-wrap then lets an oversized value wrap instead. */
  min-width: 0;
  text-align: center;
}
.kpi-divider {
  width: 1px;
  align-self: stretch;
  background: var(--border);
  margin: 0 12px;
}
.kpi-big {
  /* 26px let a long unbroken value (Lợi nhuận's "1,826.61bn" vs Doanh số's shorter "34.40bn")
     wrap mid-string at narrow card widths — smaller text keeps the longest values from the
     sản phẩm cards on one line instead. */
  font-size: 20px;
  font-weight: 800;
  color: var(--foreground);
  white-space: nowrap;
  overflow-wrap: break-word;
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
  margin-bottom: var(--section-gap);
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
  margin-bottom: var(--section-gap);
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 16px;
}
.chart-card h2 {
  margin: 0 0 6px 0;
  padding: 0;
  /* the browser default of 24px is oversized for a chart caption and, with six charts on the
     Nhóm phụ trách tab, was a meaningful part of why that tab needed scrolling */
  font-size: 16px;
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
.date-pill {
  background: var(--card);
  color: var(--foreground);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 12px;
  font-size: 13px;
  text-align: center;
  cursor: pointer;
}

@media print {
  /* keep a panel/card whole on one page, so the JPEG export doesn't split a chart away
     from its own heading when the print pagination falls mid-panel */
  .charts-panel, .kpi-card, .chart-card, .table-card {
    break-inside: avoid; page-break-inside: avoid;
  }
  .app-shell, .main { height: auto !important; overflow: visible !important; }
  .sidebar { height: auto !important; overflow: visible !important; }
  .content { overflow: visible !important; height: auto !important; }
  .sidebar, .topbar-actions, .topbar-filters { display: none !important; }
  /* the export button now sits inside the Tổng quan content, so it would otherwise appear
     in its own output */
  #export-image-btn { display: none !important; }
}
/* Same "just the content" layout as @media print, but usable in normal screen rendering
   too — for the headless-browser JPEG export, which renders under screen media. */
html.export-mode .app-shell, html.export-mode .main { height: auto !important; overflow: visible !important; }
html.export-mode .sidebar { height: auto !important; overflow: visible !important; }
html.export-mode .content { overflow: visible !important; height: auto !important; }
html.export-mode .sidebar, html.export-mode .topbar-actions, html.export-mode .topbar-filters { display: none !important; }
html.export-mode #export-image-btn { display: none !important; }

.sidebar-toggle-btn { display: none; }
@media (max-width: 768px) {
  /* Sidebar becomes an off-canvas drawer instead of a permanent 220px column — desktop layout
     otherwise has zero responsive behavior (only @media print exists elsewhere), so this is
     scoped narrowly to just the sidebar, not a full mobile redesign. */
  .sidebar {
    position: fixed; top: 0; left: 0; z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: 2px 0 12px rgba(0,0,0,0.15);
  }
  .sidebar.mobile-open { transform: translateX(0); }
  .sidebar-backdrop {
    display: none;
    position: fixed; inset: 0; z-index: 999;
    background: rgba(0,0,0,0.4);
  }
  .sidebar-backdrop.mobile-open { display: block; }
  .sidebar-toggle-btn {
    display: inline-flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--card);
    color: var(--foreground); font-size: 18px; cursor: pointer;
    margin-right: 10px;
  }
  .topbar-row { align-items: center; }
}
"""

def build_theme_js(nhom: str, active_tab: str = "sanpham") -> str:
    return f"""
function applyStoredTheme() {{
  const stored = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (stored === 'dark' || (!stored && prefersDark)) {{
    document.documentElement.classList.add('dark');
  }}
}}
function updateThemeIcon() {{
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = document.documentElement.classList.contains('dark') ? '☾' : '☀';
}}
function toggleTheme() {{
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
  updateThemeIcon();
}}

// Mobile-only off-canvas sidebar (desktop keeps its permanent 220px column via CSS — the
// mobile-open class only has any visual effect inside the max-width:768px media query).
function toggleSidebar() {{
  document.getElementById('app-sidebar').classList.toggle('mobile-open');
  document.getElementById('sidebar-backdrop').classList.toggle('mobile-open');
}}
function closeSidebar() {{
  document.getElementById('app-sidebar').classList.remove('mobile-open');
  document.getElementById('sidebar-backdrop').classList.remove('mobile-open');
}}

async function exportHtml() {{
  const btn = document.getElementById('export-html-btn');
  const original = btn.textContent;
  const clone = document.documentElement.cloneNode(true);
  clone.querySelector('#export-html-btn')?.remove();
  clone.querySelector('#export-image-btn')?.remove();
  // The exported file should always open on Tổng quan (tab id "sanpham"), regardless of which
  // tab was active in the browser when the export button was clicked.
  clone.querySelectorAll('.tab-page').forEach(el => {{
    el.style.display = (el.id === 'tab-sanpham') ? 'block' : 'none';
  }});
  clone.querySelectorAll('.nav-item').forEach(el => {{
    el.classList.toggle('active', el.dataset.tab === 'sanpham');
  }});
  const topbarTitleEl = clone.querySelector('#topbar-title');
  if (topbarTitleEl) topbarTitleEl.textContent = TAB_TITLES['sanpham'];
  // The export carries one day's figures and no server, so Kỳ báo cáo cannot filter in it —
  // changing it just reloaded the static file and snapped back to the exported date. Cut the
  // dropdown to that single date and disable it so it reads as the report date instead. The
  // JPEG path gets the same treatment server-side via DATE_OPTIONS_EXPORT_WORKING_DAYS.
  const dateSel = clone.querySelector('#header-date-select');
  if (dateSel) {{
    Array.from(dateSel.options).forEach(o => {{ if (!o.selected) o.remove(); }});
    dateSel.setAttribute('disabled', 'disabled');
  }}
  // Runs before the main script's currentTab IIFE, so opening the exported file always lands
  // on Tổng quan regardless of which tab was showing when the export button was clicked. Also
  // forces Nhóm phụ trách's own Sản phẩm/Loại số liệu to Tất cả/Lũy kế for whenever that tab
  // is opened afterward, regardless of what was selected (and persisted in localStorage) at
  // export time — read by restoreFilters().
  const forcedTabScript = clone.ownerDocument.createElement('script');
  forcedTabScript.textContent =
    "window.__EXPORT_FORCED_TAB__ = 'sanpham';" +
    "window.__EXPORT_FORCED_SANPHAM__ = 'all';" +
    "window.__EXPORT_FORCED_AGG__ = 'ytd';";
  clone.querySelector('head').insertBefore(forcedTabScript, clone.querySelector('head').firstChild);
  const html = '<!DOCTYPE html>\\n' + clone.outerHTML;
  const dateSelect = document.getElementById('header-date-select');
  const dateStr = dateSelect ? dateSelect.value : new Date().toISOString().slice(0, 10);
  btn.textContent = 'Đang lưu...';
  btn.disabled = true;
  try {{
    const resp = await fetch('/save_html_export?date=' + encodeURIComponent(dateStr), {{
      method: 'POST',
      headers: {{'Content-Type': 'text/html; charset=utf-8'}},
      body: html,
    }});
    const data = await resp.json();
    if (data.status === 'ok') {{
      alert('Đã lưu file HTML vào thư mục Gửi đi tài liệu:\\n' + data.filename);
    }} else {{
      alert('Lỗi khi lưu file HTML:\\n' + data.message);
    }}
  }} catch (e) {{
    alert('Lỗi khi lưu file HTML:\\n' + e.message);
  }} finally {{
    btn.textContent = original;
    btn.disabled = false;
  }}
}}

async function exportTongQuanImage() {{
  const btn = document.getElementById('export-image-btn');
  const original = btn.textContent;
  const dateSelect = document.getElementById('header-date-select');
  const nhomSelect = document.getElementById('header-nhom-select');
  const date = dateSelect ? dateSelect.value : '';
  const nhom = nhomSelect ? nhomSelect.value : 'PTKD 1';
  btn.textContent = 'Đang xuất...';
  btn.disabled = true;
  try {{
    const resp = await fetch('/export_image', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: new URLSearchParams({{date, nhom}}),
    }});
    const data = await resp.json();
    if (data.status === 'ok') {{
      alert('Đã lưu ảnh vào thư mục Gửi đi JPEG:\\n' + data.filename);
    }} else {{
      alert('Lỗi khi xuất ảnh:\\n' + data.message);
    }}
  }} catch (e) {{
    alert('Lỗi khi xuất ảnh:\\n' + e.message);
  }} finally {{
    btn.textContent = original;
    btn.disabled = false;
  }}
}}

async function exportExcelKhachHang() {{
  const btn = document.getElementById('export-excel-btn');
  const original = btn.textContent;
  const dateSelect = document.getElementById('header-date-select');
  const date = dateSelect ? dateSelect.value : '';
  btn.textContent = 'Đang xuất...';
  btn.disabled = true;
  try {{
    const resp = await fetch('/export_excel_khachhang?date=' + encodeURIComponent(date), {{
      method: 'POST',
    }});
    const data = await resp.json();
    if (data.status === 'ok') {{
      alert('Đã lưu file Excel vào thư mục Gửi đi tài liệu:\\n' + data.filename);
    }} else {{
      alert('Lỗi khi xuất Excel:\\n' + data.message);
    }}
  }} catch (e) {{
    alert('Lỗi khi xuất Excel:\\n' + e.message);
  }} finally {{
    btn.textContent = original;
    btn.disabled = false;
  }}
}}

const TAB_TITLES = {{
  sanpham: 'Tổng quan',
  nhom_pt: 'Nhóm phụ trách',
  nhomphutrach: 'Kết quả chi nhánh/cán bộ',
  khachhang: 'Khách hàng',
}};
// Nhóm phụ trách is one global filter (single URL param) shared by every tab that has it
const TABS_WITH_NHOM_FILTER = new Set(['nhomphutrach', 'khachhang']);
// Sản phẩm (MBNT/HĐLS) is likewise one shared client-side filter across every tab that has it
const TABS_WITH_SANPHAM_FILTER = new Set(['nhom_pt', 'khachhang']);
// Read the tab from the URL rather than trusting the server-rendered value alone. In an
// exported HTML file that value is frozen at export time, so any control that navigates
// (Nhóm phụ trách, Kỳ báo cáo) would reload the static file and land on the exported tab
// instead of the one you were on — e.g. changing nhóm on Kết quả chi nhánh/cán bộ
// ('nhomphutrach') would jump to Nhóm phụ trách ('nhom_pt').
let currentTab = (function () {{
  if (window.__EXPORT_FORCED_TAB__) return window.__EXPORT_FORCED_TAB__;
  const t = new URLSearchParams(window.location.search).get('tab');
  return Object.prototype.hasOwnProperty.call(TAB_TITLES, t) ? t : '{active_tab}';
}})();

function showTab(name) {{
  currentTab = name;
  document.querySelectorAll('.tab-page').forEach(el => {{ el.style.display = 'none'; }});
  document.getElementById('tab-' + name).style.display = 'block';
  document.querySelectorAll('.nav-item').forEach(el => {{
    el.classList.toggle('active', el.dataset.tab === name);
  }});
  closeSidebar();
  document.getElementById('topbar-title').textContent = TAB_TITLES[name];
  document.getElementById('header-nhom-group').style.display = TABS_WITH_NHOM_FILTER.has(name) ? 'flex' : 'none';
  document.getElementById('header-sanpham-group').style.display = TABS_WITH_SANPHAM_FILTER.has(name) ? 'flex' : 'none';
  // Khách hàng has no TDPS/PSHH ranking tables, so don't offer them there — and if one was left
  // selected from the Nhóm phụ trách tab, fall back rather than showing an empty tab
  const sanphamSelect = document.getElementById('header-sanpham-select');
  const tdpsOption = document.getElementById('sanpham-option-tdps');
  const allOption = document.getElementById('sanpham-option-all');
  const pshhOption = document.getElementById('sanpham-option-pshh');
  if (tdpsOption) tdpsOption.hidden = (name === 'khachhang');
  if (allOption) allOption.hidden = (name === 'khachhang');
  if (pshhOption) pshhOption.hidden = (name === 'khachhang');
  if (name === 'khachhang' && ['tdps', 'all', 'pshh'].includes(sanphamSelect.value)) {{
    sanphamSelect.value = 'mbnt';
    onHeaderSanPhamChange('mbnt');
  }}
  // Loại số liệu only applies to the Nhóm phụ trách tab's scorecards, not Khách hàng's tables
  updateAggGroupVisibility();
  // Tổng quan's own Lũy kế/Trong ngày control — a separate topbar group from header-agg-group
  // above (that one drives Nhóm phụ trách's per-product AGG_HANDLER dispatch; this one just
  // re-runs onTqChartFilterChange(), which already reads tq-loai-select directly)
  document.getElementById('header-tq-loai-group').style.display = (name === 'sanpham') ? 'flex' : 'none';
  // the JPEG export only ever captures Tổng quan, so don't offer it from other tabs
  document.getElementById('header-export-image-group').style.display = (name === 'sanpham') ? 'flex' : 'none';
  document.getElementById('header-khtablemode-group').style.display = (name === 'khachhang') ? 'flex' : 'none';
  document.getElementById('header-loaitangtruong-group').style.display = (name === 'khachhang' && khTableMode === 'tangtruong') ? 'flex' : 'none';
  document.getElementById('header-khtop10-agg-group').style.display = (name === 'khachhang' && khTableMode === 'top10') ? 'flex' : 'none';
  document.getElementById('header-export-excel-group').style.display = (name === 'khachhang') ? 'flex' : 'none';
  document.getElementById('header-kqkd-group').style.display = (name === 'nhomphutrach') ? 'flex' : 'none';
  // Switching tabs is DOM-only, so without this the address bar keeps whatever ?tab= it was
  // loaded with and F5 throws you back to that tab. replaceState (not pushState) keeps the
  // browser's Back button meaning "previous page", not "previous tab". Sản phẩm and Loại số
  // liệu already survive a refresh via localStorage in restoreFilters().
  const tabUrl = new URL(window.location.href);
  if (tabUrl.searchParams.get('tab') !== name) {{
    tabUrl.searchParams.set('tab', name);
    history.replaceState(null, '', tabUrl.toString());
  }}
}}
// Every nhóm-dependent chart and table is rendered once per nhóm and stacked (see
// nhom_variants in web_app.py), so switching is a client-side swap. It used to reload the page
// with ?nhom=..., which is inert in an exported HTML file — there is no server to re-render,
// so the static file reloaded itself and the numbers never changed.
const NHOM_SELECT_IDS = ['header-nhom-select',
  'mbnt-nhom-select', 'mbnt-nhom-select-daily', 'hdls-nhom-select', 'hdls-nhom-select-daily',
  'tdps-nhom-select', 'tdps-nhom-select-daily', 'all-nhom-select', 'all-nhom-select-daily',
  'pshh-nhom-select', 'pshh-nhom-select-daily'];
function onHeaderNhomChange(value) {{
  document.querySelectorAll('.nhom-variant').forEach(el => {{
    el.style.display = (el.dataset.nhom === value) ? 'block' : 'none';
  }});
  // keep the topbar select and all six in-panel selects showing the same nhóm
  NHOM_SELECT_IDS.forEach(id => {{
    const sel = document.getElementById(id);
    if (sel && sel.value !== value) sel.value = value;
  }});
  // Khách hàng's ranking tables filter their own cards by group rather than using variants
  mbntRankingGroup = value;
  hdlsRankingGroup = value;
  updateMbntRankingView();
  updateHdlsRankingView();
  saveFilter('nhom', value);
  const url = new URL(window.location.href);
  url.searchParams.set('nhom', value);
  history.replaceState(null, '', url.toString());
}}
// Sản phẩm and each product's Loại số liệu are client-side-only view toggles, so a page
// reload (date/nhóm change, which do round-trip the server) would otherwise snap them back
// to their default option. Persisted separately per product so MBNT and HĐLS each keep
// their own Lũy kế/Trong ngày choice independently.
function saveFilter(key, value) {{
  try {{ localStorage.setItem(key, value); }} catch (e) {{}}
}}
function restoreFilter(key, selectId, handler, fallback, forced) {{
  const sel = document.getElementById(selectId);
  if (!sel) return;
  let value;
  if (forced) {{
    value = forced;
  }} else {{
    let stored;
    try {{ stored = localStorage.getItem(key); }} catch (e) {{}}
    value = stored || fallback;
  }}
  sel.value = value;
  handler(value);
}}
function readFilter(key, fallback) {{
  let stored;
  try {{ stored = localStorage.getItem(key); }} catch (e) {{}}
  return stored || fallback;
}}
// One topbar Loại số liệu control, and one shared setting: it applies the SAME Lũy kế/Trong
// ngày choice to whichever Sản phẩm is shown, and switching Sản phẩm keeps that choice as-is
// rather than resetting it to some other saved-per-product value.
const AGG_STORAGE_KEY = 'nhomPtAgg';
const AGG_HANDLER = {{mbnt: v => onMbntAggChange(v), hdls: v => onHdlsAggChange(v), tdps: v => onTdpsAggChange(v), all: v => onAllAggChange(v), pshh: v => onPshhAggChange(v)}};
function onHeaderAggChange(value) {{
  const product = document.getElementById('header-sanpham-select').value;
  AGG_HANDLER[product](value);
  saveFilter(AGG_STORAGE_KEY, value);
}}
function restoreFilters() {{
  // An exported HTML file should always open its Nhóm phụ trách tab at Sản phẩm=Tất cả,
  // Loại số liệu=Lũy kế — regardless of whatever was last selected/persisted in localStorage
  // on whichever machine opens the file. __EXPORT_FORCED_SANPHAM__/__EXPORT_FORCED_AGG__ are
  // only ever set in the exported file itself (see exportHtml()), so this has no effect on
  // the live dashboard, which keeps restoring each viewer's own last choice as before.
  restoreFilter('sanpham', 'header-sanpham-select', onHeaderSanPhamChange, 'mbnt', window.__EXPORT_FORCED_SANPHAM__);
  // nhóm now lives in the URL (or localStorage on an exported file opened without one) rather
  // than being baked into the served HTML, so re-apply it to the stacked variants on load
  onHeaderNhomChange(new URLSearchParams(window.location.search).get('nhom')
                     || readFilter('nhom', '{nhom}'));
  // apply the one shared agg value to every product's panels regardless of which is visible
  const aggValue = window.__EXPORT_FORCED_AGG__ || readFilter(AGG_STORAGE_KEY, 'ytd');
  document.getElementById('header-agg-select').value = aggValue;
  Object.keys(AGG_HANDLER).forEach(p => AGG_HANDLER[p](aggValue));
}}

const PRODUCTS = ['mbnt', 'hdls', 'tdps', 'all', 'pshh'];
// TDPS has no TDPS section on the Khách hàng tab, but (like MBNT/HĐLS/Tất cả) does have both a
// lũy kế and a Trong ngày scorecard row on Nhóm phụ trách, so Loại số liệu applies to it too.
function updateAggGroupVisibility(product) {{
  document.getElementById('header-agg-group').style.display = (currentTab === 'nhom_pt') ? 'flex' : 'none';
}}
function onHeaderSanPhamChange(value) {{
  PRODUCTS.forEach(p => {{
    const section = document.getElementById('product-' + p);
    if (section) section.style.display = (p === value) ? 'block' : 'none';
    const khachhang = document.getElementById('khachhang-' + p);
    if (khachhang) khachhang.style.display = (p === value) ? 'block' : 'none';
  }});
  saveFilter('sanpham', value);
  // re-apply the current (shared, unchanged) Loại số liệu value to the newly shown product —
  // the header-agg-select itself doesn't need to change, only which product it's driving
  AGG_HANDLER[value](document.getElementById('header-agg-select').value);
  updateAggGroupVisibility(value);
}}
function onHeaderKqkdChange(value) {{
  document.getElementById('kqkd-chinhanh').style.display = value === 'chinhanh' ? 'block' : 'none';
  document.getElementById('kqkd-canbo').style.display = value === 'canbo' ? 'block' : 'none';
}}
// Trong ngày swaps the scorecards AND the địa bàn / PKKH charts: each panel has a lũy kế
// version (2026 vs 2025 clustered) and a daily one (today's cumulative minus yesterday's).
let mbntHtAgg = 'ytd';
function onMbntAggChange(value) {{
  document.getElementById('mbnt-kpi-ytd').style.display = value === 'ytd' ? 'flex' : 'none';
  document.getElementById('mbnt-kpi-daily').style.display = value === 'ngay' ? 'flex' : 'none';
  document.getElementById('mbnt-dim-charts').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('mbnt-dim-charts-daily').style.display = value === 'ngay' ? 'block' : 'none';
  // the chia sẻ footnote now lives inside each panel's own toolbar, so it toggles with it
  mbntHtAgg = value;
  // NIM panel: lũy kế shows one combined 2026/2025 clustered chart, Trong ngày shows Spot
  // Mua/Bán as its own clustered chart next to NIM ngày.
  onMbntNimRender();
}}
let hdlsHtAgg = 'ytd';
function onHdlsAggChange(value) {{
  document.getElementById('hdls-kpi-ytd').style.display = value === 'ytd' ? 'flex' : 'none';
  document.getElementById('hdls-kpi-daily').style.display = value === 'ngay' ? 'flex' : 'none';
  document.getElementById('hdls-dim-charts').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('hdls-dim-charts-daily').style.display = value === 'ngay' ? 'block' : 'none';
  hdlsHtAgg = value;
  // NIM panel has exactly one chart per agg mode — no filter to drive, just swap on agg change.
  document.getElementById('hdls-nim-chart-binhquan').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('hdls-nim-chart-ngay').style.display = value === 'ngay' ? 'block' : 'none';
  document.getElementById('hdls-nim-title-binhquan').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('hdls-nim-title-ngay').style.display = value === 'ngay' ? 'block' : 'none';
  onHdlsSoDuRender();
}}
function onTdpsAggChange(value) {{
  document.getElementById('tdps-kpi-ytd').style.display = value === 'ytd' ? 'flex' : 'none';
  document.getElementById('tdps-kpi-daily').style.display = value === 'ngay' ? 'flex' : 'none';
  document.getElementById('tdps-dim-charts').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('tdps-dim-charts-daily').style.display = value === 'ngay' ? 'block' : 'none';
  document.getElementById('tdps-nim-chart-binhquan').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('tdps-nim-chart-ngay').style.display = value === 'ngay' ? 'block' : 'none';
  document.getElementById('tdps-nim-title-binhquan').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('tdps-nim-title-ngay').style.display = value === 'ngay' ? 'block' : 'none';
  document.getElementById('tdps-sodu-chart-binhquan').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('tdps-sodu-chart-ngay').style.display = value === 'ngay' ? 'block' : 'none';
  document.getElementById('tdps-sodu-title-binhquan').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('tdps-sodu-title-ngay').style.display = value === 'ngay' ? 'block' : 'none';
}}
function onPshhAggChange(value) {{
  document.getElementById('pshh-kpi-ytd').style.display = value === 'ytd' ? 'flex' : 'none';
  document.getElementById('pshh-kpi-daily').style.display = value === 'ngay' ? 'flex' : 'none';
  document.getElementById('pshh-dim-charts').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('pshh-dim-charts-daily').style.display = value === 'ngay' ? 'block' : 'none';
}}
function onAllAggChange(value) {{
  document.getElementById('all-kpi-ytd').style.display = value === 'ytd' ? 'flex' : 'none';
  document.getElementById('all-kpi-daily').style.display = value === 'ngay' ? 'flex' : 'none';
  document.getElementById('all-dim-charts').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('all-dim-charts-daily').style.display = value === 'ngay' ? 'block' : 'none';
  document.getElementById('all-contrib-charts').style.display = value === 'ngay' ? 'none' : 'block';
  document.getElementById('all-contrib-charts-daily').style.display = value === 'ngay' ? 'block' : 'none';
}}
function onAllChartMetricChange(value) {{
  onChartMetricChange('all-diaban-chart', value);
  onChartMetricChange('all-pkkh-chart', value);
}}
function onAllDailyChartMetricChange(value) {{
  onChartMetricChange('all-diaban-chart-daily', value);
  onChartMetricChange('all-pkkh-chart-daily', value);
}}

// Khách hàng tab's Top khách hàng ranking tables share the global Nhóm phụ trách filter, plus
// a Loại bảng toggle between "Top 10 KH tăng trưởng" (growth ranking, Phần trăm/Tuyệt đối) and
// "Top 10 KH" (raw-value ranking — Doanh số and Lợi nhuận both shown together). "Top 10 KH"
// has its own Loại số liệu toggle (Lũy kế/Trong ngày) — Trong ngày ranks by that single day's
// own DS/LN instead of the YTD total, and has no growth-% columns (a single day has no "so
// với 2025" baseline), so it's a separate rendered table, not just a re-filter of the lũy kế one.
let khTableMode = 'tangtruong';
let khTop10Agg = 'ytd';
let mbntRankingGroup = '{nhom}';
let mbntRanking = 'pct';
let hdlsRankingGroup = '{nhom}';
let hdlsRanking = 'pct';

function updateMbntRankingView() {{
  document.getElementById('mbnt-tangtruong-wrap').style.display = (khTableMode === 'tangtruong') ? 'block' : 'none';
  document.getElementById('mbnt-top10-wrap').style.display = (khTableMode === 'top10') ? 'block' : 'none';
  ['mbnt-pct-sections', 'mbnt-abs-sections',
   'mbnt-ds-sections', 'mbnt-ln-sections', 'mbnt-ds-sections-daily', 'mbnt-ln-sections-daily'].forEach(id => {{
    document.getElementById(id).style.display = 'none';
  }});
  // "Tất cả" is now its own pooled-ranking card (data-group="Tất cả"), not "show every nhóm's
  // card at once" — so this matches exactly like any specific nhóm, no special case.
  if (khTableMode === 'tangtruong') {{
    const activeSection = document.getElementById('mbnt-' + mbntRanking + '-sections');
    activeSection.style.display = 'block';
    activeSection.querySelectorAll('.table-card').forEach(card => {{
      card.style.display = (card.dataset.group === mbntRankingGroup) ? 'block' : 'none';
    }});
  }} else {{
    const suffix = (khTop10Agg === 'ngay') ? '-daily' : '';
    ['mbnt-ds-sections' + suffix, 'mbnt-ln-sections' + suffix].forEach(id => {{
      const section = document.getElementById(id);
      section.style.display = 'block';
      section.querySelectorAll('.table-card').forEach(card => {{
        card.style.display = (card.dataset.group === mbntRankingGroup) ? 'block' : 'none';
      }});
    }});
  }}
}}
function updateHdlsRankingView() {{
  document.getElementById('hdls-tangtruong-wrap').style.display = (khTableMode === 'tangtruong') ? 'block' : 'none';
  document.getElementById('hdls-top10-wrap').style.display = (khTableMode === 'top10') ? 'block' : 'none';
  ['hdls-pct-sections', 'hdls-abs-sections',
   'hdls-ds-sections', 'hdls-ln-sections', 'hdls-ds-sections-daily', 'hdls-ln-sections-daily'].forEach(id => {{
    document.getElementById(id).style.display = 'none';
  }});
  if (khTableMode === 'tangtruong') {{
    const activeSection = document.getElementById('hdls-' + hdlsRanking + '-sections');
    activeSection.style.display = 'block';
    activeSection.querySelectorAll('.table-card').forEach(card => {{
      card.style.display = (card.dataset.group === hdlsRankingGroup) ? 'block' : 'none';
    }});
  }} else {{
    const suffix = (khTop10Agg === 'ngay') ? '-daily' : '';
    ['hdls-ds-sections' + suffix, 'hdls-ln-sections' + suffix].forEach(id => {{
      const section = document.getElementById(id);
      section.style.display = 'block';
      section.querySelectorAll('.table-card').forEach(card => {{
        card.style.display = (card.dataset.group === hdlsRankingGroup) ? 'block' : 'none';
      }});
    }});
  }}
}}

function onKhachHangTableModeChange(value) {{
  khTableMode = value;
  document.getElementById('header-loaitangtruong-group').style.display = (value === 'tangtruong') ? 'flex' : 'none';
  document.getElementById('header-khtop10-agg-group').style.display = (value === 'top10') ? 'flex' : 'none';
  updateMbntRankingView();
  updateHdlsRankingView();
}}
function onKhachHangTop10AggChange(value) {{
  khTop10Agg = value;
  updateMbntRankingView();
  updateHdlsRankingView();
}}
function onKhachHangRankingChange(value) {{
  mbntRanking = value;
  hdlsRanking = value;
  updateMbntRankingView();
  updateHdlsRankingView();
}}
function onDateChange(value) {{
  const url = new URL(window.location.href);
  url.searchParams.set('date', value);
  url.searchParams.set('tab', currentTab);
  window.location.href = url.toString();
}}
function onChartMetricChange(prefix, value) {{
  // 'sodu' exists only on the TDPS Trong ngày panel; 'ds_tlhh'/'ds_otc' only on PSHH's — the
  // loop skips ids that aren't there for whichever product/panel called this.
  ['ds', 'ds_tlhh', 'ds_otc', 'nim', 'ln', 'sodu'].forEach(metric => {{
    const el = document.getElementById(prefix + '-' + metric);
    if (el) el.style.display = 'none';
  }});
  document.getElementById(prefix + '-' + value).style.display = 'block';
}}
function onMbntChartMetricChange(value) {{
  onChartMetricChange('mbnt-diaban-chart', value);
  onChartMetricChange('mbnt-pkkh-chart', value);
  onChartMetricChange('mbnt-diaban-contrib-chart', value);
  onChartMetricChange('mbnt-pkkh-contrib-chart', value);
}}
// Tổng quan's dia_ban/PKKH charts: all sản phẩm x chỉ tiêu combinations that exist are baked
// into the page (no nhóm selector on this tab, so no per-nhóm variant to also toggle), and
// these two selects together pick which one is visible. MBNT has no Số Dư measure, so that
// option is disabled (and the selection bounced back to Doanh Số) whenever MBNT is chosen.
const TQ_CHART_KEYS = [
  'mbnt-ds', 'mbnt-ln', 'mbnt-nim',
  'hdls-ds', 'hdls-ln', 'hdls-nim', 'hdls-sodu',
  'tdps-ds', 'tdps-ln', 'tdps-nim', 'tdps-sodu',
];
function onTqChartFilterChange() {{
  const sanphamSelect = document.getElementById('tq-sanpham-select');
  const chitieuSelect = document.getElementById('tq-chitieu-select');
  const loaiSelect = document.getElementById('tq-loai-select');
  const sanpham = sanphamSelect.value;
  const loai = loaiSelect.value;  // 'ytd' | 'ngay'
  const suffix = loai === 'ngay' ? '-daily' : '';

  document.getElementById('sanpham-kpi-row-ytd').style.display = loai === 'ngay' ? 'none' : 'flex';
  document.getElementById('sanpham-kpi-row-daily').style.display = loai === 'ngay' ? 'flex' : 'none';

  const soduOption = chitieuSelect.querySelector('option[value="sodu"]');
  const mbntSelected = (sanpham === 'mbnt');
  soduOption.disabled = mbntSelected;
  soduOption.hidden = mbntSelected;
  if (mbntSelected && chitieuSelect.value === 'sodu') {{
    chitieuSelect.value = 'ds';
  }}

  const key = sanpham + '-' + chitieuSelect.value;
  // Every lũy kế AND trong ngày div gets hidden first, then only the one combination that
  // matches all three selects (Sản phẩm × Chỉ tiêu × Loại số liệu) is shown — simpler than
  // tracking which suffix was previously visible.
  TQ_CHART_KEYS.forEach(k => {{
    ['', '-daily'].forEach(sfx => {{
      const diaban = document.getElementById('tq-diaban-' + k + sfx);
      const pkkh = document.getElementById('tq-pkkh-' + k + sfx);
      if (diaban) diaban.style.display = 'none';
      if (pkkh) pkkh.style.display = 'none';
    }});
  }});
  document.getElementById('tq-diaban-' + key + suffix).style.display = 'block';
  document.getElementById('tq-pkkh-' + key + suffix).style.display = 'block';

  // Tỷ trọng đóng góp panel follows Sản phẩm, Chỉ tiêu, AND Loại số liệu — NIM has no "tỷ
  // trọng" variant (a ratio can't be expressed as a share of a whole) in either lũy kế or
  // trong ngày, so the whole panel hides itself when Chỉ tiêu = NIM instead of showing
  // something meaningless.
  const contribChitieu = chitieuSelect.value;
  const contribPanel = document.getElementById('tq-contrib-panel');
  if (contribChitieu === 'nim') {{
    contribPanel.style.display = 'none';
  }} else {{
    contribPanel.style.display = 'block';
    const contribKey = sanpham + '-' + contribChitieu;
    ['mbnt-ds', 'mbnt-ln', 'hdls-ds', 'hdls-ln', 'hdls-sodu', 'tdps-ds', 'tdps-ln', 'tdps-sodu'].forEach(k => {{
      ['', '-daily'].forEach(sfx => {{
        const diaban = document.getElementById('tq-diaban-contrib-' + k + sfx);
        const pkkh = document.getElementById('tq-pkkh-contrib-' + k + sfx);
        if (diaban) diaban.style.display = 'none';
        if (pkkh) pkkh.style.display = 'none';
      }});
    }});
    document.getElementById('tq-diaban-contrib-' + contribKey + suffix).style.display = 'block';
    document.getElementById('tq-pkkh-contrib-' + contribKey + suffix).style.display = 'block';
  }}
}}
// NIM panel: lũy kế mode shows one combined 2026/2025 clustered chart; Trong ngày shows Spot
// Mua and Spot Bán side by side (two separate chart-cards, not a toggle between them).
function onMbntNimRender() {{
  const isDaily = mbntHtAgg === 'ngay';
  document.getElementById('mbnt-nim-luykke-wrap').style.display = isDaily ? 'none' : 'block';
  document.getElementById('mbnt-nim-daily-wrap').style.display = isDaily ? 'flex' : 'none';
}}
// Số dư HĐLS donut has two independent axes: bình quân/ngày (driven by hdlsHtAgg, same as the
// NIM panel) and Tất cả/CCS/IRS (its own Loại select) — six charts, one shown at a time.
let hdlsSoDuLoai = 'all';
function onHdlsSoDuRender() {{
  ['binhquan-all', 'binhquan-ccs', 'binhquan-irs', 'ngay-all', 'ngay-ccs', 'ngay-irs'].forEach(k => {{
    document.getElementById('hdls-sodu-chart-' + k).style.display = 'none';
  }});
  const agg = hdlsHtAgg === 'ngay' ? 'ngay' : 'binhquan';
  document.getElementById('hdls-sodu-chart-' + agg + '-' + hdlsSoDuLoai).style.display = 'block';
  document.getElementById('hdls-sodu-title-binhquan').style.display = agg === 'ngay' ? 'none' : 'block';
  document.getElementById('hdls-sodu-title-ngay').style.display = agg === 'ngay' ? 'block' : 'none';
}}
function onHdlsSoDuLoaiChange(value) {{ hdlsSoDuLoai = value; onHdlsSoDuRender(); }}
function onHdlsChartMetricChange(value) {{
  onChartMetricChange('hdls-diaban-chart', value);
  onChartMetricChange('hdls-pkkh-chart', value);
  onChartMetricChange('hdls-diaban-contrib-chart', value);
  onChartMetricChange('hdls-pkkh-contrib-chart', value);
}}
function onMbntDailyChartMetricChange(value) {{
  onChartMetricChange('mbnt-diaban-chart-daily', value);
  onChartMetricChange('mbnt-pkkh-chart-daily', value);
}}
function onHdlsDailyChartMetricChange(value) {{
  onChartMetricChange('hdls-diaban-chart-daily', value);
  onChartMetricChange('hdls-pkkh-chart-daily', value);
}}
function onTdpsChartMetricChange(value) {{
  onChartMetricChange('tdps-diaban-chart', value);
  onChartMetricChange('tdps-pkkh-chart', value);
  onChartMetricChange('tdps-diaban-contrib-chart', value);
  onChartMetricChange('tdps-pkkh-contrib-chart', value);
}}
function onTdpsDailyChartMetricChange(value) {{
  onChartMetricChange('tdps-diaban-chart-daily', value);
  onChartMetricChange('tdps-pkkh-chart-daily', value);
}}
function onPshhChartMetricChange(value) {{
  onChartMetricChange('pshh-diaban-chart', value);
  onChartMetricChange('pshh-pkkh-chart', value);
}}
function onPshhDailyChartMetricChange(value) {{
  onChartMetricChange('pshh-diaban-chart-daily', value);
  onChartMetricChange('pshh-pkkh-chart-daily', value);
}}

applyStoredTheme();
document.addEventListener('DOMContentLoaded', () => {{
  updateThemeIcon();
  showTab(currentTab);
  restoreFilters();
  updateMbntRankingView();
  updateHdlsRankingView();
}});
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
    # rank_col may already be display-formatted (e.g. "1,234.56" strings, comma thousands
    # separators) by the calculations layer — coerce back to numeric so the gradient still
    # scales on the actual values instead of erroring on string arithmetic. Always run the
    # string coercion (not just when dtype == object) — pandas' nullable "string" dtype and
    # other non-plain-object text dtypes fail that check and slip raw strings through.
    numeric_col = pd.to_numeric(df[rank_col].astype(str).str.replace(",", "", regex=False), errors="coerce")
    values = numeric_col.dropna()
    if values.empty:
        return {}
    vmin, vmax = values.min(), values.max()
    colors = {}
    for idx, val in numeric_col.items():
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


def _table_header_html(col: str) -> str:
    text = col.replace(" (tr đồng)", "<br>(tr đồng)")
    if col == "STT":
        return f'<th style="text-align:center; width:50px;">{text}</th>'
    if col == "Thay đổi (m/m)":
        return f'<th style="width:80px;">{text}</th>'
    return f"<th>{text}</th>"


def render_table(df, rank_col=None, gradient=None, stt_colors=None, right_align_cols=None):
    headers = "".join(_table_header_html(col) for col in df.columns)

    row_colors = {}
    if rank_col and gradient:
        row_colors = compute_row_colors(df, rank_col, gradient)

    right_align_cols = right_align_cols or set()

    rows_html = []
    for idx, row in df.iterrows():
        color_pair = row_colors.get(idx)
        stt_pair = stt_colors.get(idx) if stt_colors else None
        cells = []
        for col in df.columns:
            value = row[col]
            if col == "STT":
                align_style = "text-align:center;"
            elif col in right_align_cols:
                align_style = "text-align:right;"
            else:
                align_style = ""

            if col == "Tên khách hàng" and color_pair:
                light_color, dark_color = color_pair
                cell_style = f' style="{align_style}--cell-bg-light: #{light_color.lstrip("#")}; --cell-bg-dark: #{dark_color.lstrip("#")};" class="gradient-cell"'
            elif col == "STT" and stt_pair:
                light_color, dark_color = stt_pair
                cell_style = f' style="{align_style}--cell-bg-light: #{light_color.lstrip("#")}; --cell-bg-dark: #{dark_color.lstrip("#")};" class="gradient-cell"'
            elif col in HIGHLIGHT_COLUMNS:
                cell_style = f' style="background-color:{HIGHLIGHT_COLUMNS[col]}; color:#1a1c18;"'
            elif align_style:
                cell_style = f' style="{align_style}"'
            else:
                cell_style = ""

            if col in GROWTH_COLUMNS_PCT or col in GROWTH_COLUMNS_ABS:
                try:
                    # value may already be a "1,234.56"-formatted string (Khách hàng tab's top/
                    # bottom tables), so strip thousands separators before parsing.
                    numeric_value = float(str(value).replace(",", ""))
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


# Khách hàng tab's top/bottom ranking tables: every column except these three identifying ones
# is a formatted numeric value and should be right-aligned.
KHACHHANG_TEXT_COLUMNS = {"Tên khách hàng", "Chi nhánh", "Cán bộ phụ trách"}


def build_sections(by_group, rank_col, title_top, title_bottom=None, include_bottom=True):
    sections = []
    for group, (top5, bottom5) in by_group.items():
        right_align_cols = set(top5.columns) - KHACHHANG_TEXT_COLUMNS
        html = (
            f'<div class="table-card" data-group="{group}">'
            f'<h2>{title_top}</h2>'
            f'{render_table(top5, rank_col=rank_col, gradient="top", right_align_cols=right_align_cols)}'
        )
        if include_bottom:
            html += (
                f'<h2>{title_bottom}</h2>'
                f'{render_table(bottom5, rank_col=rank_col, gradient="bottom", right_align_cols=right_align_cols)}'
            )
        html += '</div>'
        sections.append(html)
    return sections


def _pct_html(pct: float) -> str:
    """"so với cùng kỳ" indicator under a Lũy kế metric."""
    pct = pct or 0.0
    arrow, css = ("▲" if pct >= 0 else "▼"), ("pos" if pct >= 0 else "neg")
    return (
        f'<div class="kpi-big {css}" style="font-size:18px;margin-top:8px;">{arrow} {abs(pct):.1f}%</div>'
        f'<div class="kpi-sub">so với cùng kỳ</div>'
    )


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


def _time_elapsed_pct(selected_date: str) -> tuple[float, float]:
    """% of the selected date's month elapsed, % of its year elapsed — the pace-bar tick
    markers used by both Tổng quan's scorecards and Nhóm phụ trách's HT panels."""
    ref_date = pd.to_datetime(selected_date)
    days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
    days_in_year = 366 if calendar.isleap(ref_date.year) else 365
    month_elapsed_pct = ref_date.day / days_in_month * 100
    year_elapsed_pct = ref_date.dayofyear / days_in_year * 100
    return month_elapsed_pct, year_elapsed_pct


def _pace_row(label: str, value: float, elapsed_pct: float | None, gap: str | None = None) -> str:
    """One completion bar — value vs a 100% cap, colored by a flat 3-tier scheme against the
    value itself (not a pace-vs-elapsed-time comparison): <50% red, 50-<100% gold, >=100% green.
    elapsed_pct is accepted for call-site compatibility with the pace-vs-time convention this
    replaced, but is no longer used for coloring. No tick mark is drawn — just the fill and its
    color.

    gap is the Trong ngày cards' absolute so-với-KH/ngày number (e.g. "▲ 46.3M", from
    hoanthanh_kh_ds_mbnt and its siblings) — shown next to the label in the head row when
    given, with the % value dropped to its own line underneath (not enough room for label +
    gap + % all on one line); the lũy kế HT tháng/HT năm rows have no equivalent absolute
    figure, so they keep label + % together on one line as before."""
    fill_pct = max(0.0, min(value, 100.0))
    if value >= 100.0:
        css = ""
    elif value >= 50.0:
        css = "behind"
    else:
        css = "low"
    gap_css = "pos" if (gap and gap.startswith("▲")) else "neg"
    if gap:
        head_html = f'''
        <div class="pace-head pace-head-inline">
            <span class="pace-label">{label}</span>
            <span class="pace-gap {gap_css}">{gap}</span>
        </div>
        <div class="pace-value-row"><span class="pace-value">{value:.1f}%</span></div>
        '''
    else:
        head_html = f'''
        <div class="pace-head">
            <span class="pace-label">{label}</span>
            <span class="pace-value">{value:.1f}%</span>
        </div>
        '''
    return f'''
    <div class="pace-row">
        {head_html}
        <span class="pace-track">
            <span class="pace-fill {css}" style="width:{fill_pct:.1f}%"></span>
        </span>
    </div>
    '''


def _paces_block(ht_thang: float | None, ht_nam: float | None, month_elapsed_pct: float, year_elapsed_pct: float) -> str:
    """HT tháng + HT năm pace rows for one metric (Doanh số or Lợi nhuận). No plan data at all
    (e.g. TDPS's Doanh số) — omit the block rather than showing empty "-" bars."""
    if ht_thang is None and ht_nam is None:
        return ""
    return f'''
    <div class="kpi-paces">
        {_pace_row("HT tháng", ht_thang, month_elapsed_pct)}
        {_pace_row("HT năm", ht_nam, year_elapsed_pct)}
    </div>
    '''


def _value_block(*rows: tuple[str, str]) -> str:
    """One or more labeled figures with no completion bar (no plan/target to compare against)
    — the same .kpi-paces spacing/typography as the pace blocks, minus the track. Used to fill
    the blank space under a metric that has no HT tháng/HT năm of its own, e.g. TDPS's Số dư
    IRS/CCS under Doanh số."""
    rows_html = "".join(
        f'<div class="pace-row"><div class="pace-head">'
        f'<span class="pace-label">{label}</span><span class="pace-value">{value_str}</span>'
        f'</div></div>'
        for label, value_str in rows
    )
    return f'<div class="kpi-paces value-block">{rows_html}</div>'


def _daily_paces_block(pct: float | None, gap: str | None = None) -> str:
    """Single "HT so với KH/ngày" pace row for Trong ngày scorecards — same bar component as
    the lũy kế cards' HT tháng/HT năm, but comparing today's actual to today's daily-pace
    target instead. gap is the absolute so-với-KH/ngày figure, shown next to the % in the
    row's head."""
    if pct is None:
        return ""
    return f'''
    <div class="kpi-paces">
        {_pace_row("HT so với KH/ngày", pct, None, gap)}
    </div>
    '''


def build_kpi_row_by_sanpham(selected_date: str):
    """Same "Kết quả mua bán ngoại tệ và phái sinh" scorecards as build_kpi_row, but grouped by
    sản phẩm (MBNT/HĐLS/TDPS/PSHH) instead of nhóm phụ trách. HT tháng/HT năm are tracked
    separately for Doanh số and Lợi nhuận — except TDPS, which has no Doanh số plan in the KHKD
    sheet at all (its Doanh số HT cells render "-"), and PSHH, whose Doanh số plan exists in the
    sheet but isn't wired here — only Lợi nhuận's completion is tracked, per explicit scope."""
    month_value = str(pd.to_datetime(selected_date).month)
    date_2025 = same_day_last_year(selected_date)

    ds_mbnt = tong_ds_mbnt_ytd_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_mbnt = tong_ln_mbnt_ytd_by_nhom(selected_date).get("TOTAL", 0.0)
    ds_mbnt_kh_thang = ke_hoach_ds_mbnt_thang(month_value).get("TOTAL", 0.0)
    ds_mbnt_kh_nam = ke_hoach_ds_mbnt_nam().get("TOTAL", 0.0)
    ln_mbnt_kh_thang = ke_hoach_ln_mbnt_thang(month_value).get("TOTAL", 0.0)
    ln_mbnt_kh_nam = ke_hoach_ln_mbnt_nam().get("TOTAL", 0.0)
    ds_mbnt_base = compute_y1_tong_ds_mbnt_nhom(date_2025).get("TOTAL", 0.0)
    ln_mbnt_base = compute_y1_tong_ln_mbnt_nhom(date_2025).get("TOTAL", 0.0)

    ds_hdls = tong_ds_hdls_ytd_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_hdls = tong_ln_hdls_ytd_by_nhom(selected_date).get("TOTAL", 0.0)
    ds_hdls_kh_thang = ke_hoach_ds_hdls_thang(month_value).get("TOTAL", 0.0)
    ds_hdls_ht_nam_frac = ds_hdls_hoan_thanh(selected_date).get("TOTAL")
    ln_hdls_kh_thang = ke_hoach_ln_hdls_thang(month_value).get("TOTAL", 0.0)
    ln_hdls_ht_nam_frac = ln_hdls_hoan_thanh(selected_date).get("TOTAL")
    ds_hdls_pct = ds_hdls_pct_change_by_nhom(selected_date).get("TOTAL", 0.0) or 0.0
    ln_hdls_pct = ln_hdls_pct_change_by_nhom(selected_date).get("TOTAL", 0.0) or 0.0

    ds_tdps = ds_tdps_luy_ke_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_tdps = ln_tdps_luy_ke_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_tdps_kh_thang = ke_hoach_ln_tdps_thang(month_value).get("TOTAL", 0.0)
    ln_tdps_kh_nam = ke_hoach_ln_tdps_nam().get("TOTAL", 0.0)
    ds_tdps_pct = ds_tdps_pct_change_by_nhom(selected_date).get("TOTAL", 0.0) or 0.0
    ln_tdps_pct = ln_tdps_pct_change_by_nhom(selected_date).get("TOTAL", 0.0) or 0.0

    # NIM (and, for HĐLS/TDPS, Số dư bình quân) embedded back into each scorecard — TOTAL only,
    # no nhóm phụ trách breakdown, matching the rest of the scorecard's single-figure style
    # instead of the per-nhóm bar/donut charts shown in the panels below.
    nim_mbnt_2026 = y_nim_mbnt_nhom_diaban_pkkh(selected_date).get("TOTAL", 0.0)
    nim_mbnt_2025 = y1_nim_mbnt_nhom_diaban_pkkh(date_2025).get("TOTAL", 0.0)
    ds_mbnt_ex_kbnn = y_doanhso_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_mbnt_khong_gom_chiase = y_loinhuan_by_nhom(selected_date).get("TOTAL", 0.0)
    nim_hdls = nim_hdls_binh_quan_by_nhom(selected_date).get("TOTAL", 0.0)
    so_du_ccs = so_du_ccs_binh_quan_by_nhom(selected_date).get("TOTAL", 0.0)
    so_du_irs = so_du_irs_binh_quan_by_nhom(selected_date).get("TOTAL", 0.0)
    nim_tdps = nim_tdps_binh_quan_by_nhom(selected_date).get("TOTAL", 0.0)
    so_du_tdps = so_du_tdps_binh_quan_by_nhom(selected_date).get("TOTAL", 0.0)

    # Split across the card's existing Doanh số | Lợi nhuận halves (not nested together in one
    # half) — NIM 2026 / NIM ties to the Doanh số side, NIM 2025 / Số dư ties to the Lợi nhuận
    # side, matching the card's own left/right divider.
    mbnt_ds_extra = _value_block(
        ("DS không gồm KBNN", _fmt_bn_m(ds_mbnt_ex_kbnn)), ("NIM KH 2025", f"{nim_mbnt_2025:,.2f}")
    )
    mbnt_ln_extra = _value_block(
        ("LN không gồm chia sẻ", _fmt_bn_m(ln_mbnt_khong_gom_chiase)), ("NIM KH 2026", f"{nim_mbnt_2026:,.2f}")
    )
    hdls_ds_extra = _value_block(
        ("Số dư B/Q CCS", _fmt_bn_m(so_du_ccs)), ("Số dư B/Q IRS", _fmt_bn_m(so_du_irs))
    )
    hdls_ln_extra = _value_block(("NIM 2026", f"{nim_hdls:,.2f}"))
    # Số dư TDPS moved under NIM (both in the Doanh số column) instead of the Lợi nhuận side.
    tdps_ds_extra = _value_block(("NIM 2026", f"{nim_tdps:,.2f}"), ("Số dư B/Q TDPS", _fmt_bn_m(so_du_tdps)))
    tdps_ln_extra = ""

    # TLHH (lots) and OTC (USD) are different units, so PSHH gets its own dedicated card below
    # instead of going through the generic products loop — both get the full metric treatment
    # (value + so với cùng kỳ), not one headline figure plus a secondary line.
    ds_pshh_otc = ds_pshh_otc_luy_ke(selected_date)
    ds_pshh_tlhh = ds_pshh_tlhh_luy_ke(selected_date)
    ln_pshh = ln_pshh_luy_ke(selected_date)
    ln_pshh_kh_thang = ke_hoach_ln_pshh_thang(month_value).get("TOTAL", 0.0)
    ln_pshh_kh_nam = ke_hoach_ln_pshh_nam().get("TOTAL", 0.0)
    ds_pshh_otc_base = y1_ds_pshh_otc(date_2025)
    ds_pshh_tlhh_base = y1_ds_pshh_tlhh(date_2025)
    ln_pshh_base = y1_ln_pshh(date_2025)
    ds_pshh_otc_pct = (ds_pshh_otc - ds_pshh_otc_base) / ds_pshh_otc_base * 100 if ds_pshh_otc_base else 0.0
    ds_pshh_tlhh_pct = (ds_pshh_tlhh - ds_pshh_tlhh_base) / ds_pshh_tlhh_base * 100 if ds_pshh_tlhh_base else 0.0
    ln_pshh_pct = (ln_pshh - ln_pshh_base) / ln_pshh_base * 100 if ln_pshh_base else 0.0
    ln_pshh_ht_thang = ln_pshh / ln_pshh_kh_thang * 100 if ln_pshh_kh_thang else 0.0
    ln_pshh_ht_nam = ln_pshh / ln_pshh_kh_nam * 100 if ln_pshh_kh_nam else 0.0

    products = [
        ("Mua bán ngoại tệ", "mbnt", ds_mbnt, ln_mbnt,
         (ds_mbnt - ds_mbnt_base) / ds_mbnt_base * 100 if ds_mbnt_base else 0.0,
         (ln_mbnt - ln_mbnt_base) / ln_mbnt_base * 100 if ln_mbnt_base else 0.0,
         ds_mbnt / ds_mbnt_kh_thang * 100 if ds_mbnt_kh_thang else 0.0,
         ds_mbnt / ds_mbnt_kh_nam * 100 if ds_mbnt_kh_nam else 0.0,
         ln_mbnt / ln_mbnt_kh_thang * 100 if ln_mbnt_kh_thang else 0.0,
         ln_mbnt / ln_mbnt_kh_nam * 100 if ln_mbnt_kh_nam else 0.0, mbnt_ds_extra, mbnt_ln_extra),
        ("Hoán đổi lãi suất", "hdls", ds_hdls, ln_hdls, ds_hdls_pct, ln_hdls_pct,
         ds_hdls / ds_hdls_kh_thang * 100 if ds_hdls_kh_thang else 0.0,
         ds_hdls_ht_nam_frac * 100 if pd.notna(ds_hdls_ht_nam_frac) else 0.0,
         ln_hdls / ln_hdls_kh_thang * 100 if ln_hdls_kh_thang else 0.0,
         ln_hdls_ht_nam_frac * 100 if pd.notna(ln_hdls_ht_nam_frac) else 0.0, hdls_ds_extra, hdls_ln_extra),
        ("Tín dụng phái sinh", "tdps", ds_tdps, ln_tdps, ds_tdps_pct, ln_tdps_pct, None, None,
         ln_tdps / ln_tdps_kh_thang * 100 if ln_tdps_kh_thang else 0.0,
         ln_tdps / ln_tdps_kh_nam * 100 if ln_tdps_kh_nam else 0.0, tdps_ds_extra, tdps_ln_extra),
    ]

    month_elapsed_pct, year_elapsed_pct = _time_elapsed_pct(selected_date)

    cards = []
    for (label, tone, ds_val, ln_val, ds_pct, ln_pct,
         ds_ht_thang, ds_ht_nam, ln_ht_thang, ln_ht_nam, ds_extra, ln_extra) in products:
        cards.append(f'''
        <div class="kpi-card" data-tone="{tone}">
            <h3 class="kpi-title">{label}</h3>
            <div class="kpi-row-inner" style="align-items:flex-start;">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {_paces_block(ds_ht_thang, ds_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                    {_pct_html(ds_pct)}
                    {ds_extra}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_paces_block(ln_ht_thang, ln_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                    {_pct_html(ln_pct)}
                    {ln_extra}
                </div>
            </div>
            {'<div style="font-style:italic; font-size:11px; color:var(--muted-foreground); margin-top:6px;">*NIM KH không gồm KBNN</div>' if tone == 'mbnt' else ''}
        </div>
        ''')

    # PSHH gets its own card — TLHH (lots) and OTC (USD) each get the full metric treatment
    # (value + so với cùng kỳ), not a headline figure plus a secondary line, since they're
    # different units and neither one alone is "Doanh số PSHH". Stacked in the left half so the
    # card keeps the same two-column width as every other product's, instead of squeezing a
    # third column in.
    cards.append(f'''
    <div class="kpi-card" data-tone="pshh">
        <h3 class="kpi-title">Phái sinh hàng hóa</h3>
        <div class="kpi-row-inner" style="align-items:flex-start;">
            <div class="kpi-metric" style="display:flex; flex-direction:column; gap:14px;">
                <div>
                    <div class="kpi-big">{ds_pshh_tlhh:,.0f} lots</div>
                    <div class="kpi-sub">Doanh số TLHH</div>
                    {_pct_html(ds_pshh_tlhh_pct)}
                </div>
                <div>
                    <div class="kpi-big">{_fmt_bn_m(ds_pshh_otc)}</div>
                    <div class="kpi-sub">Doanh số OTC</div>
                    {_pct_html(ds_pshh_otc_pct)}
                </div>
            </div>
            <div class="kpi-divider"></div>
            <div class="kpi-metric">
                <div class="kpi-big">{_fmt_bn_m(ln_pshh)}</div>
                <div class="kpi-sub">Lợi nhuận</div>
                {_pct_html(ln_pshh_pct)}
                {_paces_block(ln_pshh_ht_thang, ln_pshh_ht_nam, month_elapsed_pct, year_elapsed_pct)}
            </div>
        </div>
    </div>
    ''')
    return cards


def build_kpi_row_by_sanpham_daily(selected_date: str):
    """Trong ngày counterpart to build_kpi_row_by_sanpham — single-day figures only. No HT
    tháng/HT năm/so với cùng kỳ anywhere (a day's own movement has no meaningful completion-%
    or year-over-year comparison the way a YTD figure does), per explicit user request — the
    cards show just the raw Doanh số/Lợi nhuận numbers, no plan-comparison metric in their
    place. MBNT's NIM KH 2025/2026 pair (which needs a YTD baseline) is replaced by NIM
    Mua/NIM Bán (today's own buy/sell spot NIM — the same figures behind Nhóm phụ trách's "NIM
    Spot Mua/Bán" panel). HĐLS/TDPS's Số dư bình quân/NIM 2026 become Số dư ngày/NIM ngày."""
    ds_mbnt = ds_mbnt_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_mbnt = ln_mbnt_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    nim_mbnt_mua = nim_mbnt_buy_spot_by_nhom(selected_date).get("TOTAL", 0.0)
    nim_mbnt_ban = nim_mbnt_sell_spot_by_nhom(selected_date).get("TOTAL", 0.0)

    ds_hdls = ds_hdls_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_hdls = ln_hdls_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    nim_hdls_ngay = nim_hdls_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    so_du_ccs_ngay = so_du_ccs_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    so_du_irs_ngay = so_du_irs_ngay_by_nhom(selected_date).get("TOTAL", 0.0)

    ds_tdps = ds_tdps_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_tdps = ln_tdps_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    nim_tdps_ngay = nim_tdps_ngay_by_nhom(selected_date).get("TOTAL", 0.0)
    so_du_tdps_ngay = so_du_tdps_ngay_by_nhom(selected_date).get("TOTAL", 0.0)

    mbnt_ds_extra = _value_block(("NIM Mua", f"{nim_mbnt_mua:,.2f}"))
    mbnt_ln_extra = _value_block(("NIM Bán", f"{nim_mbnt_ban:,.2f}"))
    hdls_ds_extra = _value_block(
        ("Số dư ngày CCS", _fmt_bn_m(so_du_ccs_ngay)), ("Số dư ngày IRS", _fmt_bn_m(so_du_irs_ngay))
    )
    hdls_ln_extra = _value_block(("NIM ngày", f"{nim_hdls_ngay:,.2f}"))
    tdps_ds_extra = _value_block(
        ("NIM ngày", f"{nim_tdps_ngay:,.2f}"), ("Số dư ngày TDPS", _fmt_bn_m(so_du_tdps_ngay))
    )
    tdps_ln_extra = ""

    ds_pshh_tlhh = daily_ds_pshh_tlhh_by_nhom(selected_date).get("TOTAL", 0.0)
    ds_pshh_otc = daily_ds_pshh_otc_by_nhom(selected_date).get("TOTAL", 0.0)
    ln_pshh = daily_ln_pshh_by_nhom(selected_date).get("TOTAL", 0.0)

    products = [
        ("Mua bán ngoại tệ", "mbnt", ds_mbnt, ln_mbnt, mbnt_ds_extra, mbnt_ln_extra),
        ("Hoán đổi lãi suất", "hdls", ds_hdls, ln_hdls, hdls_ds_extra, hdls_ln_extra),
        ("Tín dụng phái sinh", "tdps", ds_tdps, ln_tdps, tdps_ds_extra, tdps_ln_extra),
    ]

    cards = []
    for (label, tone, ds_val, ln_val, ds_extra, ln_extra) in products:
        cards.append(f'''
        <div class="kpi-card" data-tone="{tone}">
            <h3 class="kpi-title">{label}</h3>
            <div class="kpi-row-inner" style="align-items:flex-start;">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {ds_extra}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {ln_extra}
                </div>
            </div>
        </div>
        ''')

    cards.append(f'''
    <div class="kpi-card" data-tone="pshh">
        <h3 class="kpi-title">Phái sinh hàng hóa</h3>
        <div class="kpi-row-inner" style="align-items:flex-start;">
            <div class="kpi-metric" style="display:flex; flex-direction:column; gap:14px;">
                <div>
                    <div class="kpi-big">{ds_pshh_tlhh:,.0f} lots</div>
                    <div class="kpi-sub">Doanh số TLHH</div>
                </div>
                <div>
                    <div class="kpi-big">{_fmt_bn_m(ds_pshh_otc)}</div>
                    <div class="kpi-sub">Doanh số OTC</div>
                </div>
            </div>
            <div class="kpi-divider"></div>
            <div class="kpi-metric">
                <div class="kpi-big">{_fmt_bn_m(ln_pshh)}</div>
                <div class="kpi-sub">Lợi nhuận</div>
            </div>
        </div>
    </div>
    ''')
    return cards


def _forecast_badge_row(ds_forecast: float | None, ln_forecast: float | None,
                         ds_gap: str | None, ln_gap: str | None) -> str:
    """"So với KH LK tháng" — forecasted cuối-tháng lũy kế (DS_MBNT_du_kien_cuoi_thang /
    LN_MBNT_du_kien_cuoi_thang) plus its gap vs. KH tháng (see mbnt_forecast_end_of_month.py)
    — its own value+badge section under the DS/LN block, separate from the HT tháng/HT năm
    pace bars above it rather than folded into them.

    When a metric has no KH to compare against (TDPS's Doanh số — see
    tdps_forecast_end_of_month.py's module docstring), gap is None but forecast still is not:
    that cell shows just the forecasted figure, rather than being dropped entirely.

    Styled to match "so với cùng kỳ" (_pct_html) exactly — same .kpi-big/.kpi-sub classes and
    18px inline size — instead of the earlier pill badge, per user request."""
    if ds_forecast is None and ln_forecast is None:
        return ""

    def _cell(label: str, forecast: float | None, gap: str | None) -> str:
        if forecast is None:
            return ""
        gap_html = ""
        if gap:
            css = "pos" if gap.startswith("▲") else "neg"
            gap_html = f'<div class="kpi-big {css}" style="font-size:18px;margin-top:8px;">{gap}</div>'
        return f'''
        <div class="kpi-big" style="font-size:18px;">{_fmt_bn_m(forecast)}</div>
        <div class="kpi-sub">{label}</div>
        {gap_html}
        '''

    return f'''
    <div class="kpi-forecast-title">Ước LK cuối tháng</div>
    <div class="kpi-row-inner" style="margin-top:6px;">
        <div class="kpi-metric" style="text-align:center;">{_cell("Doanh số", ds_forecast, ds_gap)}</div>
        <div class="kpi-metric" style="text-align:center;">{_cell("Lợi nhuận", ln_forecast, ln_gap)}</div>
    </div>
    <div class="kpi-forecast-label">So với KH LK tháng</div>
    '''


def build_ds_mbnt_row(selected_date: str, date_2025: str):
    ds = tong_ds_mbnt_ytd_by_nhom(selected_date)
    ln = tong_ln_mbnt_ytd_by_nhom(selected_date)
    ds_baseline = compute_y1_tong_ds_mbnt_nhom(date_2025)
    ln_baseline = compute_y1_tong_ln_mbnt_nhom(date_2025)
    ds_kh_nam = ke_hoach_ds_mbnt_nam()
    ln_kh_nam = ke_hoach_ln_mbnt_nam()
    month_value = str(pd.to_datetime(selected_date).month)
    ds_kh_thang = ke_hoach_ds_mbnt_thang(month_value)
    ln_kh_thang = ke_hoach_ln_mbnt_thang(month_value)
    month_elapsed_pct, year_elapsed_pct = _time_elapsed_pct(selected_date)
    ds_forecast = ds_mbnt_forecast_end_of_month_by_nhom(selected_date)
    ln_forecast = ln_mbnt_forecast_end_of_month_by_nhom(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_val, ln_val = ds.get(key, 0.0), ln.get(key, 0.0)
        ds_base, ln_base = ds_baseline.get(key, 0.0), ln_baseline.get(key, 0.0)
        ds_pct = (ds_val - ds_base) / ds_base * 100 if ds_base else 0.0
        ln_pct = (ln_val - ln_base) / ln_base * 100 if ln_base else 0.0
        ds_ht_thang = ds_val / ds_kh_thang.get(key, 0.0) * 100 if ds_kh_thang.get(key, 0.0) else 0.0
        ds_ht_nam = ds_val / ds_kh_nam.get(key, 0.0) * 100 if ds_kh_nam.get(key, 0.0) else 0.0
        ln_ht_thang = ln_val / ln_kh_thang.get(key, 0.0) * 100 if ln_kh_thang.get(key, 0.0) else 0.0
        ln_ht_nam = ln_val / ln_kh_nam.get(key, 0.0) * 100 if ln_kh_nam.get(key, 0.0) else 0.0
        ds_forecast_gap = hoanthanh_kh_ds_mbnt_forecast_gap(selected_date, key)
        ln_forecast_gap = hoanthanh_kh_ln_mbnt_forecast_gap(selected_date, key)
        ds_forecast_val = ds_forecast.get(key)
        ln_forecast_val = ln_forecast.get(key)

        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {_pct_html(ds_pct)}
                    {_paces_block(ds_ht_thang, ds_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_pct_html(ln_pct)}
                    {_paces_block(ln_ht_thang, ln_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                </div>
            </div>
            {_forecast_badge_row(ds_forecast_val, ln_forecast_val, ds_forecast_gap, ln_forecast_gap)}
        </div>
        ''')
    return cards


def build_ds_mbnt_row_daily(selected_date: str):
    """Same 4 groups as build_ds_mbnt_row, but the non-accumulative (single day, not YTD/lũy
    kế) DS_MBNT/LN_MBNT measures. NIM Spot Mua/Bán moved out to its own panel — see
    build_nim_mbnt_charts_daily."""
    ds = ds_mbnt_ngay_by_nhom(selected_date)
    ln = ln_mbnt_ngay_by_nhom(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_val, ln_val = ds.get(key, 0.0), ln.get(key, 0.0)
        ds_pct = ht_thang_ds_mbnt_pct(selected_date, key)
        ln_pct = ht_thang_ln_mbnt_pct(selected_date, key)
        ds_gap = hoanthanh_kh_ds_mbnt(selected_date, key)
        ln_gap = hoanthanh_kh_ln_mbnt(selected_date, key)
        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {_daily_paces_block(ds_pct, ds_gap)}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_daily_paces_block(ln_pct, ln_gap)}
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
    """NIM HĐLS bình quân moved out to its own panel — see build_nim_hdls_charts."""
    ds = tong_ds_hdls_ytd_by_nhom(selected_date)
    ln = tong_ln_hdls_ytd_by_nhom(selected_date)
    ds_pct_all = ds_hdls_pct_change_by_nhom(selected_date)
    ln_pct_all = ln_hdls_pct_change_by_nhom(selected_date)
    ds_kh_nam = _ke_hoach_ds_hdls_nam()
    ln_kh_nam = _ke_hoach_ln_hdls_nam()
    month_value = str(pd.to_datetime(selected_date).month)
    ds_kh_thang = ke_hoach_ds_hdls_thang(month_value)
    ln_kh_thang = ke_hoach_ln_hdls_thang(month_value)
    month_elapsed_pct, year_elapsed_pct = _time_elapsed_pct(selected_date)
    ds_forecast = ds_hdls_forecast_end_of_month_by_nhom(selected_date)
    ln_forecast = ln_hdls_forecast_end_of_month_by_nhom(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_val, ln_val = ds.get(key, 0.0), ln.get(key, 0.0)
        ds_pct = ds_pct_all.get(key, 0.0) or 0.0
        ln_pct = ln_pct_all.get(key, 0.0) or 0.0
        ds_ht_thang = ds_val / ds_kh_thang.get(key, 0.0) * 100 if ds_kh_thang.get(key, 0.0) else 0.0
        ds_ht_nam = ds_val / ds_kh_nam.get(key, 0.0) * 100 if ds_kh_nam.get(key, 0.0) else 0.0
        ln_ht_thang = ln_val / ln_kh_thang.get(key, 0.0) * 100 if ln_kh_thang.get(key, 0.0) else 0.0
        ln_ht_nam = ln_val / ln_kh_nam.get(key, 0.0) * 100 if ln_kh_nam.get(key, 0.0) else 0.0
        ds_forecast_gap = hoanthanh_kh_ds_hdls_forecast_gap(selected_date, key)
        ln_forecast_gap = hoanthanh_kh_ln_hdls_forecast_gap(selected_date, key)
        ds_forecast_val = ds_forecast.get(key)
        ln_forecast_val = ln_forecast.get(key)

        cards.append(f'''
        <div class="kpi-card" data-tone="hdls">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {_pct_html(ds_pct)}
                    {_paces_block(ds_ht_thang, ds_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_pct_html(ln_pct)}
                    {_paces_block(ln_ht_thang, ln_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                </div>
            </div>
            {_forecast_badge_row(ds_forecast_val, ln_forecast_val, ds_forecast_gap, ln_forecast_gap)}
        </div>
        ''')
    return cards


def build_ds_all_row(selected_date: str, date_2025: str):
    """Combined "Tất cả" lũy kế card — Lợi nhuận only (Doanh số removed per user request: MBNT's
    is USD-denominated, HĐLS's too, PSHH's DS splits into incompatible lots/USD units and has no
    combined figure at all — a single "Doanh số Tất cả" was never a coherent number to show).
    Lợi nhuận = MBNT + HĐLS + TDPS + PSHH. so với cùng kỳ is computed on the combined
    actual/baseline sums, not averaged from each product's own percentage, so a product with a
    small base doesn't get an outsized say in the combined ratio."""
    ln_val = (
        tong_ln_mbnt_ytd_by_nhom(selected_date)
        .add(tong_ln_hdls_ytd_by_nhom(selected_date), fill_value=0.0)
        .add(ln_tdps_luy_ke_by_nhom(selected_date), fill_value=0.0)
        .add(ln_pshh_by_nhom(selected_date), fill_value=0.0)
    )

    ln_baseline = (
        compute_y1_tong_ln_mbnt_nhom(date_2025)
        .add(y1_ln_hdls_by_nhom(date_2025), fill_value=0.0)
        .add(y1_ln_tdps_by_nhom(date_2025), fill_value=0.0)
        .add(y1_ln_pshh_by_nhom(date_2025), fill_value=0.0)
    )

    ln_kh_nam = (
        ke_hoach_ln_mbnt_nam()
        .add(_ke_hoach_ln_hdls_nam(), fill_value=0.0)
        .add(ke_hoach_ln_tdps_nam(), fill_value=0.0)
        .add(ke_hoach_ln_pshh_nam(), fill_value=0.0)
    )
    month_value = str(pd.to_datetime(selected_date).month)
    ln_kh_thang = (
        ke_hoach_ln_mbnt_thang(month_value)
        .add(ke_hoach_ln_hdls_thang(month_value), fill_value=0.0)
        .add(ke_hoach_ln_tdps_thang(month_value), fill_value=0.0)
        .add(ke_hoach_ln_pshh_thang(month_value), fill_value=0.0)
    )
    month_elapsed_pct, year_elapsed_pct = _time_elapsed_pct(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ln = ln_val.get(key, 0.0)
        ln_base = ln_baseline.get(key, 0.0)
        ln_pct = (ln - ln_base) / ln_base * 100 if ln_base else 0.0
        ln_ht_thang = ln / ln_kh_thang.get(key, 0.0) * 100 if ln_kh_thang.get(key, 0.0) else 0.0
        ln_ht_nam = ln / ln_kh_nam.get(key, 0.0) * 100 if ln_kh_nam.get(key, 0.0) else 0.0
        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_pct_html(ln_pct)}
                    {_paces_block(ln_ht_thang, ln_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                </div>
            </div>
        </div>
        ''')
    return cards


def _combine_dim_dfs(*dfs: pd.DataFrame, dim_col: str, value_col: str) -> pd.DataFrame:
    """Sums the given products' (nhóm, dim_col, value_col) frames onto a common (nhóm, dim_col)
    grid — e.g. MBNT's + HĐLS's own doanh số by địa bàn, so the combined "Tất cả" dim charts
    plot the same địa bàn/PKKH breakdown the individual product charts do, just pooled."""
    combined = pd.concat(dfs, ignore_index=True)
    return combined.groupby(["nhom_phu_trach", dim_col], as_index=False)[value_col].sum()


def build_ds_all_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    """"Tất cả" Doanh Số by địa bàn = MBNT + HĐLS only. PSHH is deliberately excluded (different
    units — TLHH is lots, OTC is USD — can't be summed into a single "doanh số" bn figure
    alongside the others), see its own chart under the PSHH product tab; footnoted on the page
    per user request. TDPS has no doanh số plan/measure to include either."""
    df_2025 = _combine_dim_dfs(
        y1_ds_mbnt_by_nhom_diaban(date_2025), y1_ds_hdls_by_nhom_diaban(date_2025),
        dim_col="dia_ban", value_col="doanh_so",
    )
    df_2026 = _combine_dim_dfs(
        y_ds_mbnt_by_nhom_diaban(selected_date), y_ds_hdls_by_nhom_diaban(selected_date),
        dim_col="dia_ban", value_col="doanh_so",
    )
    return _build_clustered_chart(
        df_2025, df_2026, "dia_ban", "doanh_so", 1_000_000_000, "bn", "Doanh Số", nhom_filter, pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_ds_all_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    df_2025 = _drop_excluded_pkkh(_combine_dim_dfs(
        y1_ds_mbnt_by_nhom_pkkh(date_2025), y1_ds_hdls_by_nhom_pkkh(date_2025),
        dim_col="pkkh", value_col="doanh_so",
    ))
    df_2026 = _drop_excluded_pkkh(_combine_dim_dfs(
        y_ds_mbnt_by_nhom_pkkh(selected_date), y_ds_hdls_by_nhom_pkkh(selected_date),
        dim_col="pkkh", value_col="doanh_so",
    ))
    return _build_clustered_chart(
        df_2025, df_2026, "pkkh", "doanh_so", 1_000_000_000, "bn", "Doanh Số", nhom_filter, pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_ln_all_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    df_2025 = _combine_dim_dfs(
        y1_ln_mbnt_by_nhom_diaban(date_2025), y1_ln_hdls_by_nhom_diaban(date_2025), y1_ln_tdps_by_nhom_diaban(date_2025),
        dim_col="dia_ban", value_col="loi_nhuan",
    )
    df_2026 = _combine_dim_dfs(
        y_ln_mbnt_by_nhom_diaban(selected_date), y_ln_hdls_by_nhom_diaban(selected_date), y_ln_tdps_by_nhom_diaban(selected_date),
        dim_col="dia_ban", value_col="loi_nhuan",
    )
    return _build_clustered_chart(
        df_2025, df_2026, "dia_ban", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_ln_all_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    df_2025 = _drop_excluded_pkkh(_combine_dim_dfs(
        y1_ln_mbnt_by_nhom_pkkh(date_2025), y1_ln_hdls_by_nhom_pkkh(date_2025), y1_ln_tdps_by_nhom_pkkh(date_2025),
        dim_col="pkkh", value_col="loi_nhuan",
    ))
    df_2026 = _drop_excluded_pkkh(_combine_dim_dfs(
        y_ln_mbnt_by_nhom_pkkh(selected_date), y_ln_hdls_by_nhom_pkkh(selected_date), y_ln_tdps_by_nhom_pkkh(selected_date),
        dim_col="pkkh", value_col="loi_nhuan",
    ))
    return _build_clustered_chart(
        df_2025, df_2026, "pkkh", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_ds_all_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    df = _combine_dim_dfs(
        daily_ds_mbnt_by_nhom_diaban(selected_date), daily_ds_hdls_by_nhom_diaban(selected_date),
        dim_col="dia_ban", value_col="doanh_so",
    )
    return _build_daily_dim_chart(df, "dia_ban", "doanh_so", "Doanh Số", nhom_filter, pool_nhom=pool_nhom)


def build_ds_all_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    df = _drop_excluded_pkkh(_combine_dim_dfs(
        daily_ds_mbnt_by_nhom_pkkh(selected_date), daily_ds_hdls_by_nhom_pkkh(selected_date),
        dim_col="pkkh", value_col="doanh_so",
    ))
    return _build_daily_dim_chart(df, "pkkh", "doanh_so", "Doanh Số", nhom_filter, pool_nhom=pool_nhom)


def build_ln_all_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    df = _combine_dim_dfs(
        daily_ln_mbnt_by_nhom_diaban(selected_date), daily_ln_hdls_by_nhom_diaban(selected_date),
        daily_ln_tdps_by_nhom_diaban(selected_date),
        dim_col="dia_ban", value_col="loi_nhuan",
    )
    return _build_daily_dim_chart(df, "dia_ban", "loi_nhuan", "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom)


def build_ln_all_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    df = _drop_excluded_pkkh(_combine_dim_dfs(
        daily_ln_mbnt_by_nhom_pkkh(selected_date), daily_ln_hdls_by_nhom_pkkh(selected_date),
        daily_ln_tdps_by_nhom_pkkh(selected_date),
        dim_col="pkkh", value_col="loi_nhuan",
    ))
    return _build_daily_dim_chart(df, "pkkh", "loi_nhuan", "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom)


def build_ds_all_row_daily(selected_date: str):
    """Trong ngày (non-cumulative) counterpart to build_ds_all_row, same DS/LN scope (DS =
    MBNT+HĐLS, LN = MBNT+HĐLS+TDPS). KH/ngày gaps are combined by summing each product's own
    (actual, kế hoạch tháng) pair before taking the difference — equal to summing the
    individual gaps since every product divides by the same WorkingDays_YTD for this date —
    rather than concatenating the already-formatted per-product gap strings."""
    ds = ds_mbnt_ngay_by_nhom(selected_date).add(ds_hdls_ngay_by_nhom(selected_date), fill_value=0.0)
    ln = (
        ln_mbnt_ngay_by_nhom(selected_date)
        .add(ln_hdls_ngay_by_nhom(selected_date), fill_value=0.0)
        .add(ln_tdps_ngay_by_nhom(selected_date), fill_value=0.0)
    )

    wd = working_days_ytd(selected_date)
    month_value = str(pd.to_datetime(selected_date).month)
    ds_kh_thang = ke_hoach_ds_mbnt_thang(month_value).add(ke_hoach_ds_hdls_thang(month_value), fill_value=0.0)
    ln_kh_thang = (
        ke_hoach_ln_mbnt_thang(month_value)
        .add(ke_hoach_ln_hdls_thang(month_value), fill_value=0.0)
        .add(ke_hoach_ln_tdps_thang(month_value), fill_value=0.0)
    )

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_val, ln_val = ds.get(key, 0.0), ln.get(key, 0.0)
        ds_kh_per_day = ds_kh_thang.get(key, 0.0) / wd
        ln_kh_per_day = ln_kh_thang.get(key, 0.0) / wd
        ds_gap_val = ds_val - ds_kh_per_day
        ln_gap_val = ln_val - ln_kh_per_day
        ds_gap = f"{'▲' if ds_gap_val >= 0 else '▼'} {_fmt_gap_value(abs(ds_gap_val))}"
        ln_gap = f"{'▲' if ln_gap_val >= 0 else '▼'} {_fmt_gap_value(abs(ln_gap_val))}"
        ds_pct = ds_val / ds_kh_per_day * 100 if ds_kh_per_day else None
        ln_pct = ln_val / ln_kh_per_day * 100 if ln_kh_per_day else None

        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {_daily_paces_block(ds_pct, ds_gap)}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_daily_paces_block(ln_pct, ln_gap)}
                </div>
            </div>
        </div>
        ''')
    return cards


def build_tdps_row_daily(selected_date: str):
    """Daily (non-accumulative) DS/LN TDPS cards, same shape as the MBNT/HĐLS daily rows.
    Doanh số comes from pvkh_dsdaily_temp (see ds_tdps.py) — the sum_ds_tdps_ngay_bc column
    this used to have no access to is empty in the source."""
    ds = ds_tdps_ngay_by_nhom(selected_date)
    ln = ln_tdps_ngay_by_nhom(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ln_pct = ht_thang_ln_tdps_pct(selected_date, key)
        ln_gap = hoanthanh_kh_ln_tdps(selected_date, key)
        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner" style="align-items:flex-start;">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds.get(key, 0.0))}</div>
                    <div class="kpi-sub">Doanh số</div>
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln.get(key, 0.0))}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_daily_paces_block(ln_pct, ln_gap)}
                </div>
            </div>
        </div>
        ''')
    return cards


def build_tdps_row_ytd(selected_date: str):
    """Lũy kế (cumulative-to-date) DS/LN TDPS cards, same 4 groups as the daily row, plus so
    với cùng kỳ (vs. Y-1) for each, matching HĐLS's card. Lợi nhuận also carries the HT tháng/
    HT năm pace bars plus the "dự kiến cuối tháng" forecast gap (see tdps_forecast_end_of_
    month.py), shown as its own badge row below the card — same treatment as MBNT/HĐLS's Lợi
    nhuận. No Doanh số pace bars: TDPS has no Doanh số kế hoạch in the KHKD sheet. NIM bình
    quân moved out to its own panel — see build_nim_tdps_charts."""
    ds = ds_tdps_luy_ke_by_nhom(selected_date)
    ln = ln_tdps_luy_ke_by_nhom(selected_date)
    ds_pct_all = ds_tdps_pct_change_by_nhom(selected_date)
    ln_pct_all = ln_tdps_pct_change_by_nhom(selected_date)
    ln_kh_nam = ke_hoach_ln_tdps_nam()
    month_value = str(pd.to_datetime(selected_date).month)
    ln_kh_thang = ke_hoach_ln_tdps_thang(month_value)
    month_elapsed_pct, year_elapsed_pct = _time_elapsed_pct(selected_date)
    ln_forecast = ln_tdps_forecast_end_of_month_by_nhom(selected_date)
    ds_forecast = ds_tdps_forecast_end_of_month_by_nhom(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ln_val = ln.get(key, 0.0)
        ln_ht_thang = ln_val / ln_kh_thang.get(key, 0.0) * 100 if ln_kh_thang.get(key, 0.0) else 0.0
        ln_ht_nam = ln_val / ln_kh_nam.get(key, 0.0) * 100 if ln_kh_nam.get(key, 0.0) else 0.0
        ln_forecast_gap = hoanthanh_kh_ln_tdps_forecast_gap(selected_date, key)
        ln_forecast_val = ln_forecast.get(key)
        ds_forecast_val = ds_forecast.get(key)
        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner" style="align-items:flex-start;">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds.get(key, 0.0))}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {_pct_html(ds_pct_all.get(key, 0.0))}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_pct_html(ln_pct_all.get(key, 0.0))}
                    {_paces_block(ln_ht_thang, ln_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                </div>
            </div>
            {_forecast_badge_row(ds_forecast_val, ln_forecast_val, None, ln_forecast_gap)}
        </div>
        ''')
    return cards


def build_ds_hdls_row_daily(selected_date: str):
    """Same 4 groups as build_ds_hdls_row, but the non-accumulative (single day, not YTD/lũy
    kế) DS_HDLS/LN_HDLS measures. NIM ngày moved out to its own panel — see
    build_nim_hdls_charts_daily."""
    ds = ds_hdls_ngay_by_nhom(selected_date)
    ln = ln_hdls_ngay_by_nhom(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_val, ln_val = ds.get(key, 0.0), ln.get(key, 0.0)
        ds_pct = ht_thang_ds_hdls_pct(selected_date, key)
        ln_pct = ht_thang_ln_hdls_pct(selected_date, key)
        ds_gap = hoanthanh_kh_ds_hdls(selected_date, key)
        ln_gap = hoanthanh_kh_ln_hdls(selected_date, key)
        cards.append(f'''
        <div class="kpi-card" data-tone="hdls">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner">
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ds_val)}</div>
                    <div class="kpi-sub">Doanh số</div>
                    {_daily_paces_block(ds_pct, ds_gap)}
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_daily_paces_block(ln_pct, ln_gap)}
                </div>
            </div>
        </div>
        ''')
    return cards


def build_pshh_row_daily(selected_date: str):
    """Trong ngày (non-cumulative) PSHH cards — Doanh số stays split TLHH (lots) / OTC (USD),
    same reasoning as the Tổng quan PSHH card (see build_kpi_row_by_sanpham). No so-với-cùng-kỳ
    or KH pace bars — Trong ngày mode doesn't carry either anywhere else in this tab."""
    ds_tlhh = daily_ds_pshh_tlhh_by_nhom(selected_date)
    ds_otc = daily_ds_pshh_otc_by_nhom(selected_date)
    ln = daily_ln_pshh_by_nhom(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner" style="align-items:flex-start;">
                <div class="kpi-metric" style="display:flex; flex-direction:column; gap:14px;">
                    <div>
                        <div class="kpi-big">{ds_tlhh.get(key, 0.0):,.0f} lots</div>
                        <div class="kpi-sub">Doanh số TLHH</div>
                    </div>
                    <div>
                        <div class="kpi-big">{_fmt_bn_m(ds_otc.get(key, 0.0))}</div>
                        <div class="kpi-sub">Doanh số OTC</div>
                    </div>
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln.get(key, 0.0))}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                </div>
            </div>
        </div>
        ''')
    return cards


def build_pshh_row_ytd(selected_date: str, date_2025: str):
    """Lũy kế PSHH cards — Doanh số split TLHH/OTC, each with so với cùng kỳ (vs. Y-1); Lợi
    nhuận with so với cùng kỳ plus HT tháng/HT năm pace bars (ke_hoach_ln_pshh_thang/nam already
    exist). No Doanh số KH/pace bars — no KH DS PSHH anywhere in the KHKD sheet, matching TDPS's
    own no-DS-KH shape."""
    ds_tlhh = ds_pshh_tlhh_by_nhom(selected_date)
    ds_otc = ds_pshh_otc_by_nhom(selected_date)
    ln = ln_pshh_by_nhom(selected_date)
    y1_ds_tlhh = y1_ds_pshh_tlhh_by_nhom(date_2025)
    y1_ds_otc = y1_ds_pshh_otc_by_nhom(date_2025)
    y1_ln = y1_ln_pshh_by_nhom(date_2025)
    ln_kh_nam = ke_hoach_ln_pshh_nam()
    month_value = str(pd.to_datetime(selected_date).month)
    ln_kh_thang = ke_hoach_ln_pshh_thang(month_value)
    month_elapsed_pct, year_elapsed_pct = _time_elapsed_pct(selected_date)

    cards = []
    for key in ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]:
        ds_tlhh_val = ds_tlhh.get(key, 0.0)
        ds_otc_val = ds_otc.get(key, 0.0)
        ln_val = ln.get(key, 0.0)
        ds_tlhh_base = y1_ds_tlhh.get(key, 0.0)
        ds_otc_base = y1_ds_otc.get(key, 0.0)
        ln_base = y1_ln.get(key, 0.0)
        ds_tlhh_pct = (ds_tlhh_val - ds_tlhh_base) / ds_tlhh_base * 100 if ds_tlhh_base else 0.0
        ds_otc_pct = (ds_otc_val - ds_otc_base) / ds_otc_base * 100 if ds_otc_base else 0.0
        ln_pct = (ln_val - ln_base) / ln_base * 100 if ln_base else 0.0
        ln_kh_thang_val = ln_kh_thang.get(key, 0.0)
        ln_kh_nam_val = ln_kh_nam.get(key, 0.0)
        ln_ht_thang = ln_val / ln_kh_thang_val * 100 if ln_kh_thang_val else 0.0
        ln_ht_nam = ln_val / ln_kh_nam_val * 100 if ln_kh_nam_val else 0.0

        cards.append(f'''
        <div class="kpi-card">
            <h3 class="kpi-title">{KPI_LABELS[key]}</h3>
            <div class="kpi-row-inner" style="align-items:flex-start;">
                <div class="kpi-metric" style="display:flex; flex-direction:column; gap:14px;">
                    <div>
                        <div class="kpi-big">{ds_tlhh_val:,.0f} lots</div>
                        <div class="kpi-sub">Doanh số TLHH</div>
                        {_pct_html(ds_tlhh_pct)}
                    </div>
                    <div>
                        <div class="kpi-big">{_fmt_bn_m(ds_otc_val)}</div>
                        <div class="kpi-sub">Doanh số OTC</div>
                        {_pct_html(ds_otc_pct)}
                    </div>
                </div>
                <div class="kpi-divider"></div>
                <div class="kpi-metric">
                    <div class="kpi-big">{_fmt_bn_m(ln_val)}</div>
                    <div class="kpi-sub">Lợi nhuận</div>
                    {_pct_html(ln_pct)}
                    {_paces_block(ln_ht_thang, ln_ht_nam, month_elapsed_pct, year_elapsed_pct)}
                </div>
            </div>
        </div>
        ''')
    return cards


def _nice_step(max_val: float) -> float:
    if max_val <= 0:
        return 1
    raw_step = max_val / 5
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = raw_step
    for m in (1, 2, 5, 10):
        step = m * magnitude
        if step >= raw_step:
            break
    # once the column itself is at least 1 (whole unit), never step by a fraction of it — a
    # max of 2.3 or 2.65 should both top out at a clean "3", not "2.5"/"2" grid lines
    if max_val >= 1:
        step = max(step, 1)
    return step


def _build_clustered_chart(df_2025: pd.DataFrame, df_2026: pd.DataFrame, dim_col: str, value_col: str,
                            scale: float, unit: str, legend_label: str, nhom_filter: str = None,
                            target_series: pd.Series = None, pool_nhom: bool = False,
                            only_2026: bool = False, label_decimals: int = None) -> str:
    merged = pd.merge(
        df_2025, df_2026, on=["nhom_phu_trach", dim_col], how="outer", suffixes=("_2025", "_2026")
    ).fillna(0)
    merged = merged[merged["nhom_phu_trach"] != "TSC"]
    # A column is plotted when either year has a figure — widened on request from the earlier
    # "2025 only" rule (which hid business that's new in 2026 and so has no prior-year row).
    # Drop only rows where both years are truly zero, i.e. nothing to plot at all.
    merged = merged[(merged[f"{value_col}_2025"] != 0) | (merged[f"{value_col}_2026"] != 0)]
    if pool_nhom:
        # Tổng quan has no nhóm phụ trách selector, so its charts sum every nhóm into one bar
        # per dim_col value instead of clustering bars by nhóm (which is what nhom_filter=None
        # does for the Nhóm phụ trách tab's "Tất cả" — a different, still-per-nhóm view).
        merged = merged.groupby(dim_col, as_index=False)[[f"{value_col}_2025", f"{value_col}_2026"]].sum()
        merged["nhom_phu_trach"] = ""
        if target_series is not None:
            # Some target sources (MBNT's PKKH-level PL02 KH) carry their own genuine "THT"
            # (Toàn hệ thống) row alongside PTKD 1/PTKD 2/VPV — that row is already the real
            # system total, not derived from the other three, so summing every nhóm level would
            # double-count it. Use THT directly when present; dia_ban-level KH sources have no
            # such row (only PTKD 1/2/VPV), so those still fall back to summing across nhóm.
            if "nhom_phu_trach" in target_series.index.names and \
                    "THT" in target_series.index.get_level_values("nhom_phu_trach"):
                target_series = target_series.xs("THT", level="nhom_phu_trach")
            else:
                target_series = target_series.groupby(level=dim_col).sum()
    elif nhom_filter:
        merged = merged[merged["nhom_phu_trach"] == nhom_filter]
        if target_series is not None:
            target_series = target_series[target_series.index.get_level_values("nhom_phu_trach") == nhom_filter]
    # scale to the (possibly nhom-filtered) data's own max, so the axis rescales to fit whichever
    # nhóm phụ trách is selected instead of staying fixed to the largest value across all groups
    # (also factors in target_series, or a target line taller than every bar would render off-screen)
    target_vals = (target_series.dropna() / scale).tolist() if target_series is not None else []
    max_val = max(
        (merged[f"{value_col}_2026"] / scale).tolist()
        + ([] if only_2026 else (merged[f"{value_col}_2025"] / scale).tolist())
        + target_vals
        + [1]
    )
    merged = merged.sort_values(["nhom_phu_trach", dim_col]).reset_index(drop=True)

    groups = merged["nhom_phu_trach"].tolist()
    dia_bans = merged[dim_col].tolist()
    vals_2026 = (merged[f"{value_col}_2026"] / scale).tolist()
    vals_2025 = (merged[f"{value_col}_2025"] / scale).tolist()
    step = _nice_step(max_val)
    # snap up to the next whole multiple of step, so the tallest bar's own value always lands
    # exactly on (or just under) the top labeled grid line, e.g. max 2.65 -> grid_max 3
    grid_max = step * math.ceil(max_val / step)

    chart_h, left_pad, top_pad, right_pad = 160, 45, 14, 10
    n = len(dia_bans)
    # bar width scales to fill CHART_TARGET_WIDTH regardless of column count, avoiding leftover blank space
    available = max(CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    if only_2026:
        # single bar per dim_col value (no 2025 bar), so each group is just one bar wide
        bar_w = round(max(8, available / (n * 1.67 - 0.67)) if n else 18, 1)
        bar_gap = 0
        group_gap = round(bar_w * 0.67, 1)
        group_w = bar_w
    else:
        bar_w = round(max(8, available / (n * 3.83 - 1.67)) if n else 18, 1)
        bar_gap, group_gap = round(bar_w * 0.17, 1), round(bar_w * 1.67, 1)
        group_w = bar_w * 2 + bar_gap
    width = round(left_pad + n * group_w + max(n - 1, 0) * group_gap + right_pad, 1)
    # Always angled, not conditional on whether this chart's own labels would fit horizontally —
    # dia_ban and PKKH charts are shown side by side and need to read as a consistent pair, not
    # one rotated and the other not depending on which category names happen to be longer.
    rotate_labels = True
    # Pooled charts have no nhóm label row underneath the dim_col labels, so they need less
    # bottom padding than the clustered (per-nhóm) charts do; rotated labels need more room
    # still, since they extend diagonally below the axis instead of sitting on one line.
    bottom_pad = (22 if pool_nhom else 40) + (44 if rotate_labels else 0)
    height = chart_h + top_pad + bottom_pad

    # enough decimals that consecutive grid labels (spaced `step` apart) never round to the same
    # text — unless the caller pins a fixed count instead (NIM and lợi nhuận-in-bn labels always
    # show 2 decimals regardless of step, per user request; this dynamic count stays the default
    # for every other chart).
    if label_decimals is None:
        label_decimals = max(0, -math.floor(math.log10(step)))

    grid_lines = []
    n_ticks = int(math.floor(grid_max / step))
    for i in range(n_ticks + 1):
        v = i * step
        y = top_pad + chart_h - (chart_h * v / grid_max if grid_max else 0)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - 10}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.{label_decimals}f}{unit}</text>')

    bars = []
    hover_rects = []

    group_ticks = []
    nhom_labels = []
    bar_ranges = []
    prev_group = None
    group_start_x = left_pad
    for i, (g, db, v26, v25) in enumerate(zip(groups, dia_bans, vals_2026, vals_2025)):
        # Color now encodes nhóm phụ trách (not year) — every bar for a given nhóm shares its
        # color; 2026 is full opacity, 2025 is faded, same "color=category, opacity=year"
        # convention _build_stacked_clustered_chart already uses for IRS/CCS.
        bar_color = NHOM_COLORS.get(g, NHOM_COLORS["TOTAL"])
        x = left_pad + i * (group_w + group_gap)
        h26 = chart_h * v26 / grid_max if grid_max else 0
        y26 = top_pad + chart_h - h26
        # 2025 on the left, 2026 on the right — position only; color/opacity still tracks year,
        # not slot (2026 always solid, 2025 always faded/override), per user request.
        if only_2026:
            bars.append(f'<rect x="{x}" y="{y26:.1f}" width="{bar_w}" height="{h26:.1f}" fill="{bar_color}" rx="2" />')
            x26_center = x + bar_w / 2
        else:
            h25 = chart_h * v25 / grid_max if grid_max else 0
            y25 = top_pad + chart_h - h25
            bars.append(f'<rect x="{x}" y="{y25:.1f}" width="{bar_w}" height="{h25:.1f}" {_y1_bar_fill_attrs(g, bar_color)} rx="2" />')
            bars.append(f'<rect x="{x + bar_w + bar_gap}" y="{y26:.1f}" width="{bar_w}" height="{h26:.1f}" fill="{bar_color}" rx="2" />')
            x26_center = x + bar_w + bar_gap + bar_w / 2
        # 2026 data label above its bar — per user request ("dia ban/pkkh charts in every tab
        # and every filter need a data label for 2026"). 2025 stays hover-only, unlabeled.
        bars.append(
            f'<text x="{x26_center:.1f}" y="{y26 - 5:.1f}" font-size="9" font-weight="700" '
            f'text-anchor="middle" fill="var(--foreground)">{v26:,.{label_decimals}f}</text>'
        )
        if rotate_labels:
            lx, ly = x + group_w / 2, top_pad + chart_h + 14
            bars.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" text-anchor="end" '
                f'fill="var(--foreground)" transform="rotate(-65 {lx:.1f} {ly:.1f})">{db}</text>'
            )
        else:
            bars.append(f'<text x="{x + group_w / 2}" y="{top_pad + chart_h + 14}" font-size="10" text-anchor="middle" fill="var(--foreground)">{db}</text>')
        bar_ranges.append((x, x + group_w, g, db))

        # summarized tooltip on a wide invisible overlay, so hovering anywhere near the group works
        tv = (target_series.get(db) if pool_nhom else target_series.get((g, db))) if target_series is not None else None
        target_line = f"\nKHKD 2026: {tv / scale:,.2f}{unit}" if tv is not None and not pd.isna(tv) else ""
        label = db if pool_nhom else f"{g} - {db}"
        value_2025_line = "" if only_2026 else f"\n{legend_label} 2025: {v25:,.2f}{unit}"
        summary = f"{label}\n{legend_label} 2026: {v26:,.2f}{unit}{value_2025_line}{target_line}"
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

    nhom_label_y = top_pad + chart_h + (74 if rotate_labels else 32)
    # Skipped for pool_nhom (Tổng quan, no nhóm identity to show) and for a single filtered
    # nhóm (the nhóm select + legend swatch already say which one — repeating it centered under
    # the bars was redundant, per user).
    nhom_html = "" if (pool_nhom or nhom_filter) else "".join(
        f'<text x="{mid}" y="{nhom_label_y}" font-size="11" font-weight="700" text-anchor="middle" fill="var(--foreground)">{name}</text>'
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
            tv = target_series.get(dname) if pool_nhom else target_series.get((gname, dname))
            if tv is None or pd.isna(tv):
                continue
            tv_scaled = tv / scale
            ty = top_pad + chart_h - (chart_h * tv_scaled / grid_max if grid_max else 0)
            segments.append(
                f'<line x1="{bx1:.1f}" y1="{ty:.1f}" x2="{bx2:.1f}" y2="{ty:.1f}" '
                f'stroke="#c0392b" stroke-width="2" stroke-dasharray="6,3" />'
            )
        target_html = "".join(segments)

    # Legend shows one solid swatch per nhóm actually present (color = nhóm identity), plus a
    # plain-text note for the opacity convention (2026 solid / 2025 faded) instead of repeating
    # every nhóm twice at two opacities. Skipped entirely for pool_nhom (no nhóm identity to
    # show) and for a single filtered nhóm (the nhóm select already names it — redundant here).
    seen_groups = list(dict.fromkeys(groups)) if not (pool_nhom or nhom_filter) else []
    nhom_legend = "".join(
        f'<span><span style="display:inline-block;width:10px;height:10px;background:{NHOM_COLORS.get(g, NHOM_COLORS["TOTAL"])};margin-right:6px;"></span>{KPI_LABELS.get(g, g)}</span>'
        for g in seen_groups
    )
    if pool_nhom:
        # Pooled charts have no per-nhóm swatches to hang the opacity convention off of (nhom_legend
        # is empty above), so show it as its own pair of swatches in the pooled bar's own color —
        # solid for 2026, faded to match the actual 2025 bar opacity — instead of a plain text note.
        pool_color = NHOM_COLORS["TOTAL"]
        year_note = ""
        if not only_2026:
            year_note += f'<span><span style="display:inline-block;width:10px;height:10px;background:{pool_color};opacity:0.55;margin-right:6px;"></span>{legend_label} 2025</span>'
        year_note += f'<span><span style="display:inline-block;width:10px;height:10px;background:{pool_color};margin-right:6px;"></span>{legend_label} 2026</span>'
    else:
        # Per-nhóm legend already uses color for nhóm identity, so there's no single swatch color
        # left for the opacity convention in the multi-nhóm case — falls back to neutral gray
        # there. But when one nhóm is filtered, every bar on screen is that nhóm's own color, so
        # the swatch should match it exactly instead of showing an unrelated gray dot.
        if only_2026:
            year_note = ""
        else:
            note_color = NHOM_COLORS.get(nhom_filter, NHOM_COLORS["TOTAL"]) if nhom_filter else "var(--muted-foreground)"
            note_color_2025 = NHOM_COLORS_Y1_OVERRIDE.get(nhom_filter, note_color) if nhom_filter else note_color
            note_2025_opacity = "" if nhom_filter in NHOM_COLORS_Y1_OVERRIDE else "opacity:0.55;"
            year_note = (
                f'<span><span style="display:inline-block;width:10px;height:10px;background:{note_color_2025};{note_2025_opacity}margin-right:6px;"></span>{legend_label} 2025</span>'
                f'<span><span style="display:inline-block;width:10px;height:10px;background:{note_color};margin-right:6px;"></span>{legend_label} 2026</span>'
            )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; max-width:{width}px; height:auto; margin:0 auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{top_pad + chart_h}" x2="{width - 10}" y2="{top_pad + chart_h}" stroke="var(--foreground)" />
        {''.join(bars)}
        {target_html}
        {tick_html}
        {nhom_html}
        {''.join(hover_rects)}
    </svg>
    <div style="display:flex; gap:14px; flex-wrap:wrap; justify-content:center; margin-top:8px; font-size:12px;">
        {nhom_legend}
        {year_note}
        {'<span><span style="display:inline-block;width:14px;height:0;border-top:2px dashed #c0392b;margin-right:6px;"></span>KHKD 2026</span>' if target_series is not None else ''}
    </div>
    {build_note_line("KH lũy kế của tháng gần nhất") if target_series is not None else ''}
    '''


def _build_stacked_clustered_chart(df_2025: pd.DataFrame, df_2026: pd.DataFrame, dim_col: str,
                                    seg_cols: list, seg_labels: list, seg_colors: list,
                                    scale: float, unit: str, legend_label: str,
                                    nhom_filter: str = None, pool_nhom: bool = False,
                                    seg_colors_2025: list = None) -> str:
    """Same 2025-vs-2026 clustered layout as _build_clustered_chart, but each year's bar is a
    stack of seg_cols (e.g. IRS + CCS) instead of one solid color. 2025 used to reuse the 2026
    colors at reduced opacity, which read as a washed-out near-duplicate rather than a clearly
    different series — seg_colors_2025 now gives each (segment, year) pair its own fully
    opaque, distinct color instead. Defaults to seg_colors unchanged (opaque) if not given, so
    existing callers that only pass seg_colors keep working, just without the old fade."""
    seg_colors_2025 = seg_colors_2025 or seg_colors
    merged = pd.merge(
        df_2025, df_2026, on=["nhom_phu_trach", dim_col], how="outer", suffixes=("_2025", "_2026")
    ).fillna(0)
    merged = merged[merged["nhom_phu_trach"] != "TSC"]
    # A column is plotted when either year has a figure — see _build_clustered_chart's version
    # of this rule.
    total_2025 = sum(merged[f"{c}_2025"] for c in seg_cols)
    total_2026 = sum(merged[f"{c}_2026"] for c in seg_cols)
    merged = merged[(total_2025 != 0) | (total_2026 != 0)]
    if pool_nhom:
        agg_cols = [f"{c}_2025" for c in seg_cols] + [f"{c}_2026" for c in seg_cols]
        merged = merged.groupby(dim_col, as_index=False)[agg_cols].sum()
        merged["nhom_phu_trach"] = ""
    elif nhom_filter:
        merged = merged[merged["nhom_phu_trach"] == nhom_filter]
    merged = merged.sort_values(["nhom_phu_trach", dim_col]).reset_index(drop=True)

    totals_2026 = [sum(row[f"{c}_2026"] for c in seg_cols) / scale for _, row in merged.iterrows()]
    totals_2025 = [sum(row[f"{c}_2025"] for c in seg_cols) / scale for _, row in merged.iterrows()]
    max_val = max(totals_2026 + totals_2025 + [1])
    step = _nice_step(max_val)
    grid_max = step * math.ceil(max_val / step)

    chart_h, left_pad, top_pad, right_pad = 160, 45, 14, 10
    n = len(merged)
    available = max(CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    bar_w = round(max(8, available / (n * 3.83 - 1.67)) if n else 18, 1)
    bar_gap, group_gap = round(bar_w * 0.17, 1), round(bar_w * 1.67, 1)
    group_w = bar_w * 2 + bar_gap
    width = round(left_pad + n * group_w + max(n - 1, 0) * group_gap + right_pad, 1)

    dims = merged[dim_col].tolist()
    rotate_labels = True
    bottom_pad = (22 if pool_nhom else 40) + (44 if rotate_labels else 0)
    height = chart_h + top_pad + bottom_pad

    label_decimals = max(0, -math.floor(math.log10(step)))
    grid_lines = []
    n_ticks = int(math.floor(grid_max / step))
    for i in range(n_ticks + 1):
        v = i * step
        y = top_pad + chart_h - (chart_h * v / grid_max if grid_max else 0)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - 10}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.{label_decimals}f}{unit}</text>')

    def _stack_rects(x: float, vals: list, colors: list) -> str:
        offset, parts = 0.0, []
        for val, color in zip(vals, colors):
            top = offset + val
            h = chart_h * val / grid_max if grid_max else 0
            y = top_pad + chart_h - chart_h * top / grid_max if grid_max else top_pad + chart_h
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}" rx="2" />')
            offset = top
        return "".join(parts)

    bars, hover_rects, group_ticks, nhom_labels = [], [], [], []
    prev_group, group_start_x = None, left_pad
    for i, row in merged.iterrows():
        g, d = row["nhom_phu_trach"], row[dim_col]
        x = left_pad + i * (group_w + group_gap)
        vals_2026 = [row[f"{c}_2026"] / scale for c in seg_cols]
        vals_2025 = [row[f"{c}_2025"] / scale for c in seg_cols]
        # 2025 on the left, 2026 on the right — same position swap as _build_clustered_chart.
        bars.append(_stack_rects(x, vals_2025, seg_colors_2025))
        bars.append(_stack_rects(x + bar_w + bar_gap, vals_2026, seg_colors))
        # 2026 total data label above the stack — the per-segment split is already on hover;
        # this is the total figure at a glance, per user request.
        total_2026 = sum(vals_2026)
        label_y = top_pad + chart_h - (chart_h * total_2026 / grid_max if grid_max else 0) - 5
        bars.append(
            f'<text x="{x + bar_w + bar_gap + bar_w / 2:.1f}" y="{label_y:.1f}" font-size="9" '
            f'font-weight="700" text-anchor="middle" fill="var(--foreground)">{total_2026:,.{label_decimals}f}</text>'
        )
        if rotate_labels:
            lx, ly = x + group_w / 2, top_pad + chart_h + 14
            bars.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" text-anchor="end" '
                f'fill="var(--foreground)" transform="rotate(-65 {lx:.1f} {ly:.1f})">{d}</text>'
            )
        else:
            bars.append(f'<text x="{x + group_w / 2}" y="{top_pad + chart_h + 14}" font-size="10" text-anchor="middle" fill="var(--foreground)">{d}</text>')

        label = d if pool_nhom else f"{g} - {d}"
        seg_lines_2026 = "".join(f"\n{sl} 2026: {v:,.2f}{unit}" for sl, v in zip(seg_labels, vals_2026))
        seg_lines_2025 = "".join(f"\n{sl} 2025: {v:,.2f}{unit}" for sl, v in zip(seg_labels, vals_2025))
        hover_rects.append(
            f'<rect x="{x - bar_gap / 2:.1f}" y="{top_pad}" width="{group_w + bar_gap:.1f}" height="{chart_h}" '
            f'fill="transparent"><title>{label}{seg_lines_2026}{seg_lines_2025}</title></rect>'
        )
        if g != prev_group:
            if prev_group is not None:
                mid = (group_start_x + x - group_gap) / 2
                nhom_labels.append((mid, prev_group))
                group_ticks.append(x - group_gap / 2)
            group_start_x = x
            prev_group = g
    last_x = left_pad + n * (group_w + group_gap)
    nhom_labels.append(((group_start_x + last_x - group_gap) / 2, prev_group))

    nhom_label_y = top_pad + chart_h + (74 if rotate_labels else 32)
    # Skipped for pool_nhom (Tổng quan, no nhóm identity to show) and for a single filtered
    # nhóm (the nhóm select + legend swatch already say which one — repeating it centered under
    # the bars was redundant, per user).
    nhom_html = "" if (pool_nhom or nhom_filter) else "".join(
        f'<text x="{mid}" y="{nhom_label_y}" font-size="11" font-weight="700" text-anchor="middle" fill="var(--foreground)">{name}</text>'
        for mid, name in nhom_labels
    )
    tick_html = "".join(
        f'<line x1="{tx}" y1="{top_pad + chart_h}" x2="{tx}" y2="{top_pad + chart_h + 6}" stroke="var(--border)" />'
        for tx in group_ticks
    )
    legend_html = "".join(
        f'<span><span style="display:inline-block;width:10px;height:10px;background:{c25};margin-right:6px;"></span>{sl} 2025</span>'
        f'<span><span style="display:inline-block;width:10px;height:10px;background:{c26};margin-right:6px;"></span>{sl} 2026</span>'
        for sl, c26, c25 in zip(seg_labels, seg_colors, seg_colors_2025)
    )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; max-width:{width}px; height:auto; margin:0 auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{top_pad + chart_h}" x2="{width - 10}" y2="{top_pad + chart_h}" stroke="var(--foreground)" />
        {''.join(bars)}
        {tick_html}
        {nhom_html}
        {''.join(hover_rects)}
    </svg>
    <div style="display:flex; gap:20px; justify-content:center; margin-top:8px; font-size:12px; flex-wrap:wrap;">
        {legend_html}
    </div>
    '''


def _build_stacked_daily_chart(df: pd.DataFrame, dim_col: str, seg_cols: list, seg_labels: list,
                                seg_colors: list, nhom_filter: str = None, pool_nhom: bool = False,
                                period_label: str = "trong ngày",
                                empty_message: str = "Không phát sinh giao dịch trong ngày") -> str:
    """Trong ngày counterpart to _build_stacked_clustered_chart — one stacked bar per (nhóm,
    dim) instead of a 2025/2026 pair. Segments can be negative (a day's IRS/CCS doanh số can
    net negative on unwinds/corrections), so each segment's rect is drawn from the running
    offset to offset+value, whatever the sign, instead of assuming everything stacks upward
    from zero. period_label/empty_message default to the "trong ngày" wording but are
    overridable — Tổng quan's Số dư HĐLS chart reuses this for a "bình quân năm" balance stack
    instead, which is not a day's movement."""
    df = df[df["nhom_phu_trach"] != "TSC"].copy()
    total = sum(df[c] for c in seg_cols)
    df = df[df[dim_col].notna() & (total != 0)]
    if pool_nhom:
        df = df.groupby(dim_col, as_index=False)[seg_cols].sum()
        df["nhom_phu_trach"] = ""
    elif nhom_filter:
        df = df[df["nhom_phu_trach"] == nhom_filter]
    df = df.sort_values(["nhom_phu_trach", dim_col]).reset_index(drop=True)
    if df.empty:
        return _daily_placeholder(empty_message)

    scale, unit = _auto_money_unit(pd.concat([df[c] for c in seg_cols]))

    running = [0.0] * len(df)
    lo = [0.0] * len(df)
    hi = [0.0] * len(df)
    for c in seg_cols:
        vals = (df[c] / scale).tolist()
        for i, v in enumerate(vals):
            new = running[i] + v
            lo[i], hi[i] = min(lo[i], new), max(hi[i], new)
            running[i] = new

    max_val, min_val = max(hi + [0.0]), min(lo + [0.0])
    step = _nice_step(max(max_val - min_val, abs(max_val), abs(min_val)))
    grid_max = step * math.ceil(max_val / step) if max_val > 0 else 0.0
    grid_min = step * math.floor(min_val / step) if min_val < 0 else 0.0
    if grid_max == grid_min:
        grid_max = step
    span = grid_max - grid_min

    groups = df["nhom_phu_trach"].tolist()
    dims = df[dim_col].tolist()

    chart_h, left_pad, top_pad, right_pad = 160, 45, 14, 10
    n = len(dims)
    available = max(CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    bar_w = round(max(8, available / (n * 1.9)) if n else 18, 1)
    group_gap = round(bar_w * 0.9, 1)
    width = round(left_pad + n * bar_w + max(n - 1, 0) * group_gap + right_pad, 1)
    # Always angled for consistency with the paired dia_ban/PKKH chart, not conditional on
    # whether this chart's own labels would fit horizontally.
    rotate_labels = True
    bottom_pad = (22 if pool_nhom else 40) + (44 if rotate_labels else 0)
    height = chart_h + top_pad + bottom_pad

    def y_of(v: float) -> float:
        return top_pad + chart_h * (grid_max - v) / span

    label_decimals = max(0, -math.floor(math.log10(step)))
    zero_y = y_of(0.0)

    grid_lines = []
    n_ticks = int(round(span / step))
    for i in range(n_ticks + 1):
        v = grid_min + i * step
        y = y_of(v)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - 10}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.{label_decimals}f}{unit}</text>')

    bars, hover_rects, group_ticks, nhom_labels = [], [], [], []
    prev_group, group_start_x = None, left_pad
    for i, (g, dim) in enumerate(zip(groups, dims)):
        x = left_pad + i * (bar_w + group_gap)
        offset = 0.0
        tooltip_lines = [dim if pool_nhom else f"{g} - {dim}"]
        for c, sl, color in zip(seg_cols, seg_labels, seg_colors):
            v = df.iloc[i][c] / scale
            top = offset + v
            y1, y2 = y_of(offset), y_of(top)
            y_top, h = min(y1, y2), abs(y2 - y1)
            bars.append(f'<rect x="{x}" y="{y_top:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}" rx="2" />')
            tooltip_lines.append(f"{sl}: {v:,.2f}{unit}")
            offset = top
        # 2026 total data label above (or below, for a net-negative stack) the bar — the
        # per-segment split is already on hover; this is the total figure at a glance.
        label_y = y_of(offset) - 5 if offset >= 0 else y_of(offset) + 12
        bars.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{label_y:.1f}" font-size="9" font-weight="700" '
            f'text-anchor="middle" fill="var(--foreground)">{offset:,.{label_decimals}f}</text>'
        )
        if rotate_labels:
            lx, ly = x + bar_w / 2, top_pad + chart_h + 14
            bars.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" text-anchor="end" '
                f'fill="var(--foreground)" transform="rotate(-65 {lx:.1f} {ly:.1f})">{dim}</text>'
            )
        else:
            bars.append(f'<text x="{x + bar_w / 2}" y="{top_pad + chart_h + 14}" font-size="10" text-anchor="middle" fill="var(--foreground)">{dim}</text>')
        hover_rects.append(
            f'<rect x="{x - group_gap / 2:.1f}" y="{top_pad}" width="{bar_w + group_gap:.1f}" height="{chart_h}" '
            f'fill="transparent"><title>{chr(10).join(tooltip_lines)}</title></rect>'
        )
        if g != prev_group:
            if prev_group is not None:
                nhom_labels.append(((group_start_x + x - group_gap) / 2, prev_group))
                group_ticks.append(x - group_gap / 2)
            group_start_x = x
            prev_group = g
    last_x = left_pad + n * (bar_w + group_gap)
    nhom_labels.append(((group_start_x + last_x - group_gap) / 2, prev_group))

    nhom_label_y = top_pad + chart_h + (74 if rotate_labels else 32)
    # Skipped for pool_nhom (Tổng quan, no nhóm identity to show) and for a single filtered
    # nhóm (the nhóm select + legend swatch already say which one — repeating it centered under
    # the bars was redundant, per user).
    nhom_html = "" if (pool_nhom or nhom_filter) else "".join(
        f'<text x="{mid}" y="{nhom_label_y}" font-size="11" font-weight="700" text-anchor="middle" fill="var(--foreground)">{name}</text>'
        for mid, name in nhom_labels
    )
    tick_html = "".join(
        f'<line x1="{tx}" y1="{top_pad + chart_h}" x2="{tx}" y2="{top_pad + chart_h + 6}" stroke="var(--border)" />'
        for tx in group_ticks
    )
    legend_html = "".join(
        f'<span><span style="display:inline-block;width:10px;height:10px;background:{color};margin-right:6px;"></span>{sl} {period_label}</span>'
        for sl, color in zip(seg_labels, seg_colors)
    )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; max-width:{width}px; height:auto; margin:0 auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{zero_y:.1f}" x2="{width - 10}" y2="{zero_y:.1f}" stroke="var(--foreground)" />
        {''.join(bars)}
        <line x1="{left_pad}" y1="{top_pad + chart_h}" x2="{width - 10}" y2="{top_pad + chart_h}" stroke="var(--border)" />
        {tick_html}
        {nhom_html}
        {''.join(hover_rects)}
    </svg>
    <div style="display:flex; gap:20px; justify-content:center; margin-top:8px; font-size:12px;">
        {legend_html}
    </div>
    '''


def _nim_to_dict(series: pd.Series) -> dict:
    """NIM lookups can return pd.NA (rate lookup failed) — fillna before handing to
    _build_nim_bar_chart, whose `values.get(key, 0.0) or 0.0` would raise on a bare NA."""
    return series.fillna(0.0).to_dict()


def _build_nim_bar_chart(values: dict, tooltip_label: str) -> str:
    """Single-series column chart of a value by nhóm phụ trách (PTKD1/PTKD2/VPV/TOTAL) — used
    for the NIM panels. Like HT, NIM has no địa bàn/pkkh breakdown of its own at this level and
    no 2025-vs-2026 clustering (a single point-in-time ratio, not a year-over-year comparison),
    so this is a plain one-bar-per-nhóm chart — but unlike HT's gauge (which only ever shows a
    0-100+ % completion), NIM can go negative, so this one draws bars from a zero baseline in
    either direction instead of always growing up from the bottom."""
    keys = ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]
    vals = [values.get(k, 0.0) or 0.0 for k in keys]
    max_val = max(vals + [0.0])
    min_val = min(vals + [0.0])
    step = _nice_step(max(max_val, abs(min_val), 1))
    grid_max = step * math.ceil(max_val / step) if max_val > 0 else 0.0
    grid_min = -step * math.ceil(abs(min_val) / step) if min_val < 0 else 0.0
    span = (grid_max - grid_min) or 1

    # taller than a plain HT/bar gauge (chart_h 120 -> 200): this chart usually sits beside the
    # số dư donut (height 260) in a flex row and used to leave a lot of blank space under itself
    chart_h, left_pad, top_pad, bottom_pad, right_pad = 200, 50, 22, 30, 10
    n = len(keys)
    available = max(CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    bar_w = round(max(20, available / (n * 1.67 - 0.67)), 1)
    bar_gap = round(bar_w * 0.67, 1)
    width = round(left_pad + n * bar_w + (n - 1) * bar_gap + right_pad, 1)
    height = chart_h + top_pad + bottom_pad

    def y_of(v: float) -> float:
        return top_pad + chart_h - chart_h * (v - grid_min) / span

    label_decimals = max(0, -math.floor(math.log10(step))) if step else 0
    n_ticks = int(round(span / step)) if step else 0
    grid_lines = []
    for i in range(n_ticks + 1):
        v = grid_min + i * step
        y = y_of(v)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - 10}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.{label_decimals}f}</text>')

    zero_y = y_of(0)
    bars = []
    hover_rects = []
    for i, (key, v) in enumerate(zip(keys, vals)):
        x = left_pad + i * (bar_w + bar_gap)
        y_top = min(y_of(v), zero_y)
        h = abs(y_of(v) - zero_y)
        bars.append(f'<rect x="{x}" y="{y_top:.1f}" width="{bar_w}" height="{h:.1f}" fill="{HT_RING_COLORS[i % len(HT_RING_COLORS)]}" rx="2" />')
        # data label sits above the bar for a positive value, below for a negative one — NIM can
        # go negative, so the label can't just always be pinned above the bar's top edge
        label_y = y_top - 7 if v >= 0 else y_top + h + 15
        bars.append(f'<text x="{x + bar_w / 2:.1f}" y="{label_y:.1f}" font-size="14" font-weight="700" text-anchor="middle" fill="var(--foreground)">{v:,.2f}</text>')
        bars.append(f'<text x="{x + bar_w / 2}" y="{top_pad + chart_h + 16}" font-size="11" font-weight="700" text-anchor="middle" fill="var(--foreground)">{KPI_LABELS[key]}</text>')
        hover_rects.append(
            f'<rect x="{x - bar_gap / 2:.1f}" y="{top_pad}" width="{bar_w + bar_gap:.1f}" height="{chart_h}" '
            f'fill="transparent"><title>{KPI_LABELS[key]}\n{tooltip_label}: {v:,.2f}</title></rect>'
        )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; height:auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{zero_y:.1f}" x2="{width - 10}" y2="{zero_y:.1f}" stroke="var(--foreground)" />
        {''.join(bars)}
        {''.join(hover_rects)}
    </svg>
    '''


def _build_nim_clustered_bar_chart(values_a: dict, values_b: dict, label_a: str = "2026",
                                    label_b: str = "2025", swap_position: bool = False) -> str:
    """Two-series column chart of NIM by nhóm phụ trách — series A (solid) and series B (faded)
    bars side by side per nhóm, same color convention as _build_clustered_chart's DS/LN
    dia_ban/pkkh charts. swap_position puts B on the left / A on the right (used for the
    2025-left/2026-right lũy kế convention) without changing which series is solid vs faded —
    that still tracks A/B identity, not left/right slot. Left False for Spot Mua/Bán, which
    isn't a year comparison and keeps Mua on the left. Originally built for 2026-vs-2025 lũy kế
    (default labels), reused as-is
    for Trong ngày's Spot Mua-vs-Bán clustering — NIM has no dia_ban/pkkh breakdown to cluster
    against here, so nhóm is the only axis, but two series still read better side by side than
    switched between behind a filter."""
    keys = ["PTKD 1", "PTKD 2", "VPV", "TOTAL"]
    vals_2026 = [values_a.get(k, 0.0) or 0.0 for k in keys]
    vals_2025 = [values_b.get(k, 0.0) or 0.0 for k in keys]
    all_vals = vals_2026 + vals_2025
    max_val = max(all_vals + [0.0])
    min_val = min(all_vals + [0.0])
    step = _nice_step(max(max_val, abs(min_val), 1))
    grid_max = step * math.ceil(max_val / step) if max_val > 0 else 0.0
    grid_min = -step * math.ceil(abs(min_val) / step) if min_val < 0 else 0.0
    span = (grid_max - grid_min) or 1

    chart_h, left_pad, top_pad, bottom_pad, right_pad = 200, 50, 22, 46, 10
    n = len(keys)
    available = max(CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    # two bars per nhóm instead of one — same total slot count logic as _build_clustered_chart
    bar_w = round(max(10, available / (n * 2 * 1.4 - 0.4)), 1)
    bar_gap = round(bar_w * 0.2, 1)
    group_gap = round(bar_w * 1.0, 1)
    group_w = 2 * bar_w + bar_gap
    width = round(left_pad + n * group_w + (n - 1) * group_gap + right_pad, 1)
    height = chart_h + top_pad + bottom_pad

    def y_of(v: float) -> float:
        return top_pad + chart_h - chart_h * (v - grid_min) / span

    label_decimals = max(0, -math.floor(math.log10(step))) if step else 0
    n_ticks = int(round(span / step)) if step else 0
    grid_lines = []
    for i in range(n_ticks + 1):
        v = grid_min + i * step
        y = y_of(v)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - 10}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.{label_decimals}f}</text>')

    zero_y = y_of(0)
    bars = []
    hover_rects = []
    for i, key in enumerate(keys):
        # Color = nhóm identity (not year) here too — A full opacity, B faded, matching
        # _build_clustered_chart's convention. swap_position only moves which x-slot each
        # occupies; the solid/faded styling stays tied to A/B, not to left/right.
        bar_color = NHOM_COLORS[key]
        group_x = left_pad + i * (group_w + group_gap)
        v26, v25 = vals_2026[i], vals_2025[i]
        x_a = group_x + bar_w + bar_gap if swap_position else group_x
        x_b = group_x if swap_position else group_x + bar_w + bar_gap

        y26_top = min(y_of(v26), zero_y)
        h26 = abs(y_of(v26) - zero_y)
        bars.append(f'<rect x="{x_a}" y="{y26_top:.1f}" width="{bar_w}" height="{h26:.1f}" fill="{bar_color}" rx="2" />')
        label_y26 = y26_top - 7 if v26 >= 0 else y26_top + h26 + 14
        bars.append(f'<text x="{x_a + bar_w / 2:.1f}" y="{label_y26:.1f}" font-size="12" font-weight="700" text-anchor="middle" fill="var(--foreground)">{v26:,.2f}</text>')
        # per-bar series label ("2026"/"Mua" etc.) directly under its own bar, instead of a
        # single "Đậm: X · Nhạt: Y" note off in the legend — nhóm name still sits below this,
        # in its own row, since it applies to the whole group, not just one bar.
        bars.append(f'<text x="{x_a + bar_w / 2:.1f}" y="{top_pad + chart_h + 15}" font-size="11" text-anchor="middle" fill="var(--muted-foreground)">{label_a}</text>')

        x25 = x_b
        y25_top = min(y_of(v25), zero_y)
        h25 = abs(y_of(v25) - zero_y)
        bars.append(f'<rect x="{x25}" y="{y25_top:.1f}" width="{bar_w}" height="{h25:.1f}" {_y1_bar_fill_attrs(key, bar_color)} rx="2" />')
        label_y25 = y25_top - 7 if v25 >= 0 else y25_top + h25 + 14
        bars.append(f'<text x="{x25 + bar_w / 2:.1f}" y="{label_y25:.1f}" font-size="12" font-weight="700" text-anchor="middle" fill="var(--foreground)">{v25:,.2f}</text>')
        bars.append(f'<text x="{x25 + bar_w / 2:.1f}" y="{top_pad + chart_h + 15}" font-size="11" text-anchor="middle" fill="var(--muted-foreground)">{label_b}</text>')

        bars.append(f'<text x="{group_x + group_w / 2}" y="{top_pad + chart_h + 30}" font-size="11" font-weight="700" text-anchor="middle" fill="var(--foreground)">{KPI_LABELS[key]}</text>')
        hover_rects.append(
            f'<rect x="{group_x - group_gap / 2:.1f}" y="{top_pad}" width="{group_w + group_gap:.1f}" height="{chart_h}" '
            f'fill="transparent"><title>{KPI_LABELS[key]}\nNIM {label_a}: {v26:,.2f}\nNIM {label_b}: {v25:,.2f}</title></rect>'
        )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; height:auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{zero_y:.1f}" x2="{width - 10}" y2="{zero_y:.1f}" stroke="var(--foreground)" />
        {''.join(bars)}
        {''.join(hover_rects)}
    </svg>
    <div style="display:flex; gap:14px; flex-wrap:wrap; justify-content:center; margin-top:8px; font-size:12px;">
        {"".join(f'<span><span style="display:inline-block;width:10px;height:10px;background:{NHOM_COLORS[k]};margin-right:6px;"></span>{KPI_LABELS[k]}</span>' for k in keys)}
    </div>
    '''


def build_nim_mbnt_charts(selected_date: str, date_2025: str) -> str:
    """NIM MBNT lũy kế column chart, pulled out of the DS/LN scorecard — 2026 and 2025 shown
    side by side per nhóm in one clustered chart, same as the dia_ban/pkkh charts' own
    year-over-year style, instead of a Năm-toggle between two separate single-year charts."""
    return _build_nim_clustered_bar_chart(
        _nim_to_dict(y_nim_mbnt_nhom_diaban_pkkh(selected_date)),
        _nim_to_dict(y1_nim_mbnt_nhom_diaban_pkkh(date_2025)),
        swap_position=True,
    )


def build_nim_mbnt_charts_daily(selected_date: str) -> dict:
    """Trong ngày counterpart to build_nim_mbnt_charts — NIM Spot Mua/Bán shown as one clustered
    chart (Mua solid, Bán faded, per nhóm) instead of behind a Loại filter, plus NIM ngày (the
    day's combined/blended NIM, same concept as HĐLS/TDPS's own "NIM ngày") as its own separate
    chart-card next to it."""
    return {
        "spot": _build_nim_clustered_bar_chart(
            _nim_to_dict(nim_mbnt_buy_spot_by_nhom(selected_date)),
            _nim_to_dict(nim_mbnt_sell_spot_by_nhom(selected_date)),
            label_a="Mua", label_b="Bán",
        ),
        "ngay": _build_nim_bar_chart(_nim_to_dict(nim_mbnt_ngay_by_nhom(selected_date)), "NIM trong ngày"),
    }


def build_nim_hdls_charts(selected_date: str) -> str:
    """NIM HĐLS bình quân column chart, pulled out of the lũy kế scorecard. Single figure, no
    filter needed — unlike MBNT there's no 2025 counterpart to toggle between."""
    return _build_nim_bar_chart(_nim_to_dict(nim_hdls_binh_quan_by_nhom(selected_date)), "NIM bình quân")


def build_nim_hdls_charts_daily(selected_date: str) -> str:
    """Trong ngày counterpart to build_nim_hdls_charts — NIM ngày, pulled out of the daily
    scorecard."""
    return _build_nim_bar_chart(_nim_to_dict(nim_hdls_ngay_by_nhom(selected_date)), "NIM ngày")


def build_nim_tdps_charts(selected_date: str) -> str:
    """NIM TDPS bình quân column chart, pulled out of the lũy kế scorecard."""
    return _build_nim_bar_chart(_nim_to_dict(nim_tdps_binh_quan_by_nhom(selected_date)), "NIM bình quân")


def build_nim_tdps_charts_daily(selected_date: str) -> str:
    """Trong ngày counterpart to build_nim_tdps_charts — NIM ngày, pulled out of the daily
    scorecard."""
    return _build_nim_bar_chart(_nim_to_dict(nim_tdps_ngay_by_nhom(selected_date)), "NIM ngày")


def _auto_money_unit(values: pd.Series) -> tuple[float, str]:
    """Pick the display unit from the plotted data's own peak, so a day whose whole movement is
    a few hundred thousand đồng reads "300K" instead of "0.30M".

    A day's figure spans several orders of magnitude depending on product, nhóm and how busy the
    day was — the same fixed unit that suits MBNT lợi nhuận (billions) renders every HĐLS doanh
    số bar as 0.00. Falls back to M when everything is zero, so an all-quiet day still shows a
    conventional axis instead of a bare count."""
    peak = values.abs().max()
    if pd.isna(peak) or peak == 0:
        return 1_000_000, "M"
    if peak >= 1_000_000_000:
        return 1_000_000_000, "bn"
    if peak >= 1_000_000:
        return 1_000_000, "M"
    if peak >= 1_000:
        return 1_000, "K"
    return 1, ""


def _daily_placeholder(message: str) -> str:
    """Stands in for a Trong ngày chart that has nothing to plot, sized to roughly match the
    chart it replaces so the two-column layout doesn't collapse."""
    return ('<div style="text-align:center; color:var(--muted-foreground); font-size:20px; '
            f'font-weight:700; padding:80px 0;">{message}</div>')


def _build_daily_dim_chart(df: pd.DataFrame, dim_col: str, value_col: str, legend_label: str,
                            nhom_filter: str = None, scale: float = None, unit: str = "",
                            period_label: str = "trong ngày",
                            empty_message: str = "Không phát sinh giao dịch trong ngày",
                            pool_nhom: bool = False, label_decimals: int = None) -> str:
    """Single-series sibling of _build_clustered_chart for the "Trong ngày" view. One bar per
    (nhóm, dim) instead of a 2026/2025 pair — see daily_diaban_pkkh.py for why there is no 2025
    counterpart to cluster against.

    Only dims that actually moved are plotted; a zero column is dropped rather than drawn as an
    empty slot. The axis therefore changes shape from day to day and does not track the lũy kế
    chart's columns — that is the requested behaviour. (An earlier version pinned the columns to
    the lũy kế set and zero-padded the quiet ones; if that is ever wanted back, it needs the
    2025 frame passed in again to derive the column list.)

    scale/unit default to None = pick from the data via _auto_money_unit. Only NIM overrides
    them, being a ratio with no monetary unit to scale.

    Also unlike the clustered chart, the axis can run below zero: a day's own DS/LN really can
    be negative (unwinds, corrections), where a YTD cumulative in practice never is."""
    df = df[df["nhom_phu_trach"] != "TSC"].copy()
    # NaN arises for NIM, whose ratio is undefined when the day's DS is 0 — that is a
    # no-movement column too, so it drops out with the zeros.
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0.0)
    df = df[df[dim_col].notna() & (df[value_col] != 0)]
    if pool_nhom:
        # Tổng quan has no nhóm selector, so it sums every nhóm into one bar per dim_col value
        # instead of clustering bars by nhóm. Only meaningful for additive measures (Số dư) —
        # never called for NIM, whose ratio can't be summed across nhóm.
        df = df.groupby(dim_col, as_index=False)[value_col].sum()
        df["nhom_phu_trach"] = ""
    elif nhom_filter:
        df = df[df["nhom_phu_trach"] == nhom_filter]
    df = df.sort_values(["nhom_phu_trach", dim_col]).reset_index(drop=True)
    if df.empty:
        return _daily_placeholder(empty_message)

    if scale is None:
        # after nhom_filter, so the unit tracks what is actually on screen for this nhóm
        scale, unit = _auto_money_unit(df[value_col])
        # "Trong ngày" lợi nhuận can land in bn same as any lũy kế chart on a big-movement day —
        # give it the same fixed 2 decimals those get, without forcing it on K/M days too.
        if unit == "bn" and label_decimals is None:
            label_decimals = 2

    groups = df["nhom_phu_trach"].tolist()
    dims = df[dim_col].tolist()
    vals = (df[value_col] / scale).tolist()

    max_val, min_val = max(vals + [0.0]), min(vals + [0.0])
    step = _nice_step(max(max_val - min_val, abs(max_val), abs(min_val)))
    grid_max = step * math.ceil(max_val / step) if max_val > 0 else 0.0
    grid_min = step * math.floor(min_val / step) if min_val < 0 else 0.0
    if grid_max == grid_min:
        grid_max = step
    span = grid_max - grid_min

    chart_h, left_pad, top_pad, right_pad = 160, 45, 14, 10
    n = len(dims)
    available = max(CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    # one bar per column rather than two, so the same available width spreads over n slots
    bar_w = round(max(8, available / (n * 1.9)) if n else 18, 1)
    group_gap = round(bar_w * 0.9, 1)
    width = round(left_pad + n * bar_w + max(n - 1, 0) * group_gap + right_pad, 1)
    # Always angled for consistency with the paired dia_ban/PKKH chart, not conditional on
    # whether this chart's own labels would fit horizontally.
    rotate_labels = True
    bottom_pad = (22 if pool_nhom else 40) + (44 if rotate_labels else 0)
    height = chart_h + top_pad + bottom_pad

    def y_of(v: float) -> float:
        return top_pad + chart_h * (grid_max - v) / span

    if label_decimals is None:
        label_decimals = max(0, -math.floor(math.log10(step)))
    zero_y = y_of(0.0)

    grid_lines = []
    n_ticks = int(round(span / step))
    for i in range(n_ticks + 1):
        v = grid_min + i * step
        y = y_of(v)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - 10}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.{label_decimals}f}{unit}</text>')

    bars, hover_rects, group_ticks, nhom_labels = [], [], [], []
    prev_group, group_start_x = None, left_pad
    for i, (g, dim, v) in enumerate(zip(groups, dims, vals)):
        x = left_pad + i * (bar_w + group_gap)
        y = y_of(v) if v >= 0 else zero_y
        h = abs(y_of(v) - zero_y)
        bar_color = NHOM_COLORS.get(g, NHOM_COLORS["TOTAL"])
        bars.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{bar_color}" rx="2" />')
        # 2026 data label — above the bar for a positive value, below for a negative one, same
        # up/down convention _build_nim_bar_chart already uses for its own signed bars.
        label_y = y - 5 if v >= 0 else y + h + 12
        bars.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{label_y:.1f}" font-size="9" font-weight="700" '
            f'text-anchor="middle" fill="var(--foreground)">{v:,.{label_decimals}f}</text>'
        )
        # dim labels sit under the axis floor, not under the bar, so negative bars don't collide
        if rotate_labels:
            lx, ly = x + bar_w / 2, top_pad + chart_h + 14
            bars.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" text-anchor="end" '
                f'fill="var(--foreground)" transform="rotate(-65 {lx:.1f} {ly:.1f})">{dim}</text>'
            )
        else:
            bars.append(f'<text x="{x + bar_w / 2}" y="{top_pad + chart_h + 14}" font-size="10" text-anchor="middle" fill="var(--foreground)">{dim}</text>')
        label = dim if pool_nhom else f"{g} - {dim}"
        hover_rects.append(
            f'<rect x="{x - group_gap / 2:.1f}" y="{top_pad}" width="{bar_w + group_gap:.1f}" height="{chart_h}" '
            f'fill="transparent"><title>{label}\n{legend_label} {period_label}: {v:,.2f}{unit}</title></rect>'
        )
        if g != prev_group:
            if prev_group is not None:
                nhom_labels.append(((group_start_x + x - group_gap) / 2, prev_group))
                group_ticks.append(x - group_gap / 2)
            group_start_x = x
            prev_group = g
    last_x = left_pad + n * (bar_w + group_gap)
    nhom_labels.append(((group_start_x + last_x - group_gap) / 2, prev_group))

    nhom_label_y = top_pad + chart_h + (74 if rotate_labels else 32)
    # Skipped for pool_nhom (Tổng quan, no nhóm identity to show) and for a single filtered
    # nhóm (the nhóm select + legend swatch already say which one — repeating it centered under
    # the bars was redundant, per user).
    nhom_html = "" if (pool_nhom or nhom_filter) else "".join(
        f'<text x="{mid}" y="{nhom_label_y}" font-size="11" font-weight="700" text-anchor="middle" fill="var(--foreground)">{name}</text>'
        for mid, name in nhom_labels
    )
    tick_html = "".join(
        f'<line x1="{tx}" y1="{top_pad + chart_h}" x2="{tx}" y2="{top_pad + chart_h + 6}" stroke="var(--border)" />'
        for tx in group_ticks
    )

    # legend swatches follow whichever nhóm actually appear in this chart, in their original
    # order, each colored to match its bars — a single generic swatch would be misleading now
    # that bars are colored per nhóm instead of one flat color for the whole series. Skipped for
    # a single filtered nhóm (the nhóm select already names it); pool_nhom's group="" case still
    # needs its fallback "{legend_label} 2026" text, so that one isn't filtered out here.
    seen_groups = [] if nhom_filter else list(dict.fromkeys(groups))
    legend_items = "".join(
        f'<span><span style="display:inline-block;width:10px;height:10px;background:{NHOM_COLORS.get(g, NHOM_COLORS["TOTAL"])};margin-right:6px;"></span>{KPI_LABELS.get(g, g) if g else f"{legend_label} 2026"}</span>'
        for g in seen_groups
    )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; max-width:{width}px; height:auto; margin:0 auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{zero_y:.1f}" x2="{width - 10}" y2="{zero_y:.1f}" stroke="var(--foreground)" />
        {''.join(bars)}
        <line x1="{left_pad}" y1="{top_pad + chart_h}" x2="{width - 10}" y2="{top_pad + chart_h}" stroke="var(--border)" />
        {tick_html}
        {nhom_html}
        {''.join(hover_rects)}
    </svg>
    <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center; margin-top:8px; font-size:12px;">
        {legend_items}
    </div>
    '''


CONTRIB_PALETTE = [
    "#0F766E", "#F59E0B", "#6366F1", "#EC4899", "#10B981", "#F97316",
    "#3B82F6", "#A855F7", "#EF4444", "#14B8A6", "#84CC16", "#8B5CF6",
]


def _build_contribution_chart(df: pd.DataFrame, dim_col: str, value_col: str) -> str:
    """Doanh số tỷ trọng đóng góp (%) of each dia_ban/PKKH, expressed as a share of whatever's in
    `df` — the caller decides scope: pass the whole (unfiltered) frame for "pooled across every
    nhóm", or pre-filter to one nhóm phụ trách so each dia_ban/PKKH's % is relative to that
    nhóm's own total instead. Expressed as this sản phẩm's own doanh số total, not compared
    against the other products (different units/scale, so a single combined 100% would not mean
    anything). 2026 only — a contribution share has no year-over-year pair to cluster against.

    Rendered as a donut (one ring, no leader-line labels — dia_ban/PKKH can run to a dozen-plus
    slices, too many for labels on the ring itself without overlapping) with a legend below
    carrying each slice's name and %, sorted biggest-first so the legend reads in the same order
    as the ring starting at 12 o'clock. No center label — also used as-is by
    _build_sanpham_contribution_chart, where the slices are different products that may use
    different underlying units, so a "100%" claim in the middle would be misleading."""
    grouped = df.groupby(dim_col, as_index=False)[value_col].sum()
    grouped = grouped[grouped[dim_col].notna() & (grouped[value_col] > 0)]
    total = grouped[value_col].sum()
    if total <= 0 or grouped.empty:
        return _daily_placeholder("Không có dữ liệu")
    grouped = grouped.sort_values(value_col, ascending=False).reset_index(drop=True)
    grouped["pct"] = grouped[value_col] / total * 100.0

    dims = grouped[dim_col].tolist()
    pcts = grouped["pct"].tolist()
    colors = [CONTRIB_PALETTE[i % len(CONTRIB_PALETTE)] for i in range(len(dims))]

    width, height, cx, cy, r_outer, r_inner = 320, 260, 160, 130, 95, 55

    def point(radius: float, fraction: float):
        angle = 2 * math.pi * fraction - math.pi / 2  # start at 12 o'clock
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    arcs = []
    cursor = 0.0
    for dim, pct, color in zip(dims, pcts, colors):
        share = pct / 100.0
        start, end = cursor, cursor + share
        cursor = end
        # a full-circle single slice can't be drawn as one arc (start == end), so nudge it
        if share >= 0.999:
            arcs.append(
                f'<circle cx="{cx}" cy="{cy}" r="{(r_outer + r_inner) / 2}" fill="none" '
                f'stroke="{color}" stroke-width="{r_outer - r_inner}">'
                f'<title>{dim}: {pct:.1f}%</title></circle>'
            )
            continue
        x1, y1 = point(r_outer, start)
        x2, y2 = point(r_outer, end)
        x3, y3 = point(r_inner, end)
        x4, y4 = point(r_inner, start)
        large = 1 if share > 0.5 else 0
        arcs.append(
            f'<path d="M {x1:.1f} {y1:.1f} A {r_outer} {r_outer} 0 {large} 1 {x2:.1f} {y2:.1f} '
            f'L {x3:.1f} {y3:.1f} A {r_inner} {r_inner} 0 {large} 0 {x4:.1f} {y4:.1f} Z" '
            f'fill="{color}"><title>{dim}: {pct:.1f}%</title></path>'
        )

    legend = "".join(
        f'<span><span style="display:inline-block;width:10px;height:10px;background:{color};'
        f'margin-right:6px;border-radius:2px;"></span>{dim} ({pct:.1f}%)</span>'
        for dim, pct, color in zip(dims, pcts, colors)
    )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; margin:0 auto; max-width:100%; height:auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(arcs)}
    </svg>
    <div style="display:flex; gap:10px 16px; justify-content:center; flex-wrap:wrap; margin-top:8px; font-size:12px;">
        {legend}
    </div>
    '''


def _build_sanpham_contribution_chart(pairs: list) -> str:
    """Tỷ trọng đóng góp (%) across sản phẩm (MBNT/HĐLS/TDPS) instead of dia_ban/PKKH — each
    product's lũy kế TOTAL as a share of the sum of the products passed in. `pairs` is a list of
    (label, value) tuples; zero/negative values are dropped before the ring is built (mirrors
    _build_contribution_chart's own filter)."""
    df = pd.DataFrame(pairs, columns=["san_pham", "value"])
    return _build_contribution_chart(df, "san_pham", "value")


def build_ds_sanpham_contrib_chart(selected_date: str) -> str:
    """Doanh số tỷ trọng by sản phẩm, lũy kế TOTAL across nhóm — same TOTAL figures as the
    Tổng quan scorecards (build_kpi_row_by_sanpham)."""
    pairs = [
        ("MBNT", tong_ds_mbnt_ytd_by_nhom(selected_date).get("TOTAL", 0.0)),
        ("HĐLS", tong_ds_hdls_ytd_by_nhom(selected_date).get("TOTAL", 0.0)),
        ("TDPS", ds_tdps_luy_ke_by_nhom(selected_date).get("TOTAL", 0.0)),
    ]
    return _build_sanpham_contribution_chart(pairs)


def build_ln_sanpham_contrib_chart(selected_date: str) -> str:
    """Lợi nhuận tỷ trọng by sản phẩm — same TOTAL figures as the Tổng quan scorecards."""
    pairs = [
        ("MBNT", tong_ln_mbnt_ytd_by_nhom(selected_date).get("TOTAL", 0.0)),
        ("HĐLS", tong_ln_hdls_ytd_by_nhom(selected_date).get("TOTAL", 0.0)),
        ("TDPS", ln_tdps_luy_ke_by_nhom(selected_date).get("TOTAL", 0.0)),
    ]
    return _build_sanpham_contribution_chart(pairs)


def build_sodu_sanpham_contrib_chart(selected_date: str) -> str:
    """Số dư tỷ trọng by sản phẩm — MBNT has no số dư measure (§1.1), so only HĐLS/TDPS appear,
    same bình quân năm TOTAL figures used by their own scorecards."""
    pairs = [
        ("HĐLS", so_du_hdls_binh_quan_by_nhom(selected_date).get("TOTAL", 0.0)),
        ("TDPS", so_du_tdps_binh_quan_by_nhom(selected_date).get("TOTAL", 0.0)),
    ]
    return _build_sanpham_contribution_chart(pairs)


def build_ds_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    """Doanh số contribution % by địa bàn — MBNT + HĐLS only (TDPS has no doanh số), same
    product scope as build_ds_all_diaban_chart. nhom_filter=None (the "Tất cả" nhóm_variants
    case) pools every nhóm's doanh số together, matching _build_contribution_chart's default."""
    df = _combine_dim_dfs(
        y_ds_mbnt_by_nhom_diaban(selected_date), y_ds_hdls_by_nhom_diaban(selected_date),
        dim_col="dia_ban", value_col="doanh_so",
    )
    if nhom_filter:
        df = df[df["nhom_phu_trach"] == nhom_filter]
    return _build_contribution_chart(df, "dia_ban", "doanh_so")


def build_ds_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(_combine_dim_dfs(
        y_ds_mbnt_by_nhom_pkkh(selected_date), y_ds_hdls_by_nhom_pkkh(selected_date),
        dim_col="pkkh", value_col="doanh_so",
    ))
    if nhom_filter:
        df = df[df["nhom_phu_trach"] == nhom_filter]
    return _build_contribution_chart(df, "pkkh", "doanh_so")


def build_ds_contribution_diaban_chart_daily(selected_date: str, nhom_filter: str = None) -> str:
    """Trong ngày counterpart to build_ds_contribution_diaban_chart."""
    df = _combine_dim_dfs(
        daily_ds_mbnt_by_nhom_diaban(selected_date), daily_ds_hdls_by_nhom_diaban(selected_date),
        dim_col="dia_ban", value_col="doanh_so",
    )
    if nhom_filter:
        df = df[df["nhom_phu_trach"] == nhom_filter]
    return _build_contribution_chart(df, "dia_ban", "doanh_so")


def build_ds_contribution_pkkh_chart_daily(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(_combine_dim_dfs(
        daily_ds_mbnt_by_nhom_pkkh(selected_date), daily_ds_hdls_by_nhom_pkkh(selected_date),
        dim_col="pkkh", value_col="doanh_so",
    ))
    if nhom_filter:
        df = df[df["nhom_phu_trach"] == nhom_filter]
    return _build_contribution_chart(df, "pkkh", "doanh_so")


def _product_contribution_chart(df: pd.DataFrame, dim_col: str, value_col: str, nhom_filter: str = None) -> str:
    """Shared step for each individual sản phẩm's own (not pooled/"Tất cả") lũy kế tỷ trọng
    đóng góp charts below — nhom_filter=None means every nhóm pooled together (the "Tất cả"
    nhóm_variants case), matching _build_contribution_chart's own default scope."""
    if nhom_filter:
        df = df[df["nhom_phu_trach"] == nhom_filter]
    return _build_contribution_chart(df, dim_col, value_col)


def build_ds_mbnt_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(y_ds_mbnt_by_nhom_diaban(selected_date), "dia_ban", "doanh_so", nhom_filter)


def build_ds_mbnt_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(y_ds_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT)
    return _product_contribution_chart(df, "pkkh", "doanh_so", nhom_filter)


def build_ln_mbnt_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(y_ln_mbnt_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan", nhom_filter)


def build_ln_mbnt_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(y_ln_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT)
    return _product_contribution_chart(df, "pkkh", "loi_nhuan", nhom_filter)


def build_ds_hdls_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(y_ds_hdls_by_nhom_diaban(selected_date), "dia_ban", "doanh_so", nhom_filter)


def build_ds_hdls_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(y_ds_hdls_by_nhom_pkkh(selected_date))
    return _product_contribution_chart(df, "pkkh", "doanh_so", nhom_filter)


def build_ln_hdls_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(y_ln_hdls_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan", nhom_filter)


def build_ln_hdls_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(y_ln_hdls_by_nhom_pkkh(selected_date))
    return _product_contribution_chart(df, "pkkh", "loi_nhuan", nhom_filter)


def build_sodu_hdls_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(so_du_hdls_luy_ke_by_nhom_diaban(selected_date), "dia_ban", "so_du", nhom_filter)


def build_sodu_hdls_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(so_du_hdls_luy_ke_by_nhom_pkkh(selected_date))
    return _product_contribution_chart(df, "pkkh", "so_du", nhom_filter)


def build_ds_tdps_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(y_ds_tdps_by_nhom_diaban(selected_date), "dia_ban", "doanh_so", nhom_filter)


def build_ds_tdps_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(y_ds_tdps_by_nhom_pkkh(selected_date))
    return _product_contribution_chart(df, "pkkh", "doanh_so", nhom_filter)


def build_ln_tdps_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(y_ln_tdps_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan", nhom_filter)


def build_ln_tdps_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(y_ln_tdps_by_nhom_pkkh(selected_date))
    return _product_contribution_chart(df, "pkkh", "loi_nhuan", nhom_filter)


def build_sodu_tdps_contribution_diaban_chart(selected_date: str, nhom_filter: str = None) -> str:
    return _product_contribution_chart(so_du_tdps_luy_ke_by_nhom_diaban(selected_date), "dia_ban", "so_du", nhom_filter)


def build_sodu_tdps_contribution_pkkh_chart(selected_date: str, nhom_filter: str = None) -> str:
    df = _drop_excluded_pkkh(so_du_tdps_luy_ke_by_nhom_pkkh(selected_date))
    return _product_contribution_chart(df, "pkkh", "so_du", nhom_filter)


STACK_COLORS = NHOM_COLORS
STACK_ORDER = ["PTKD 1", "PTKD 2", "VPV"]
STACKED_CHART_TARGET_WIDTH = 620  # two line charts side by side, matching CHART_TARGET_WIDTH


def _build_donut_chart(values: pd.Series) -> str:
    """Donut split by nhóm phụ trách for a single day's figures. Only the three real nhóm are
    plotted — the source's own TOTAL row is the sum of them, so including it would double the
    circle. Negative or zero slices are skipped since they can't be drawn as an arc.

    Labels sit outside the ring on a leader line (value only, no %), matching the reference
    screenshot's style — extra canvas width on both sides makes room for them."""
    scale, unit = 1_000_000, "M"
    slices = [(g, float(values.get(g, 0.0)) / scale) for g in STACK_ORDER]
    slices = [(g, v) for g, v in slices if v > 0]
    total = sum(v for _, v in slices)

    width, height, cx, cy, r_outer, r_inner = 420, 260, 210, 130, 95, 55
    if total <= 0:
        return '<div style="text-align:center; color:var(--muted-foreground); font-size:13px;">Không có số dư</div>'

    def point(radius: float, fraction: float):
        angle = 2 * math.pi * fraction - math.pi / 2  # start at 12 o'clock
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    arcs = []
    labels = []
    cursor = 0.0
    for grp, value in slices:
        share = value / total
        start, end = cursor, cursor + share
        cursor = end
        x1, y1 = point(r_outer, start)
        x2, y2 = point(r_outer, end)
        x3, y3 = point(r_inner, end)
        x4, y4 = point(r_inner, start)
        large = 1 if share > 0.5 else 0

        mid = (start + end) / 2
        angle = 2 * math.pi * mid - math.pi / 2
        ux, uy = math.cos(angle), math.sin(angle)
        ex, ey = point(r_outer, mid)  # leader start, right at the ring's outer edge
        bx, by = cx + (r_outer + 14) * ux, cy + (r_outer + 14) * uy  # bend point
        lx = bx + (26 if ux >= 0 else -26)  # short horizontal dogleg out to the label
        anchor = "start" if ux >= 0 else "end"
        text_x = lx + (4 if ux >= 0 else -4)
        label = (
            f'<polyline points="{ex:.1f},{ey:.1f} {bx:.1f},{by:.1f} {lx:.1f},{by:.1f}" '
            f'fill="none" stroke="var(--muted-foreground)" stroke-width="1" />'
            f'<text x="{text_x:.1f}" y="{by + 4:.1f}" font-size="12" font-weight="700" '
            f'text-anchor="{anchor}" fill="var(--foreground)">{value:,.1f}{unit}</text>'
        )

        # a full-circle single slice can't be drawn as one arc (start == end), so nudge it
        if share >= 0.999:
            arcs.append(
                f'<circle cx="{cx}" cy="{cy}" r="{(r_outer + r_inner) / 2}" fill="none" '
                f'stroke="{STACK_COLORS[grp]}" stroke-width="{r_outer - r_inner}">'
                f'<title>{grp}: {value:,.1f}{unit} (100.0%)</title></circle>'
            )
            labels.append(label)
            continue

        arcs.append(
            f'<path d="M {x1:.1f} {y1:.1f} A {r_outer} {r_outer} 0 {large} 1 {x2:.1f} {y2:.1f} '
            f'L {x3:.1f} {y3:.1f} A {r_inner} {r_inner} 0 {large} 0 {x4:.1f} {y4:.1f} Z" '
            f'fill="{STACK_COLORS[grp]}">'
            f'<title>{grp}: {value:,.1f}{unit} ({share * 100:.1f}%)</title></path>'
        )
        labels.append(label)

    legend = "".join(
        f'<span><span style="display:inline-block;width:10px;height:10px;background:{STACK_COLORS[g]};'
        f'margin-right:6px;border-radius:2px;"></span>{g}</span>'
        for g, v in slices
    )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; margin:0 auto; max-width:100%; height:auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(arcs)}
        {''.join(labels)}
        <text x="{cx}" y="{cy - 4}" font-size="12" text-anchor="middle" fill="var(--muted-foreground)">Tổng</text>
        <text x="{cx}" y="{cy + 16}" font-size="16" font-weight="700" text-anchor="middle" fill="var(--foreground)">{total:,.1f}{unit}</text>
    </svg>
    <div style="display:flex; gap:16px; justify-content:center; flex-wrap:wrap; margin-top:8px; font-size:12px;">
        {legend}
    </div>
    '''


def build_so_du_tdps_donut_charts(selected_date: str) -> dict:
    """Số dư TDPS donuts — bình quân (YTD average) for Lũy kế mode, ngày (daily snapshot) for
    Trong ngày mode, matching the NIM panel's same bình quân/ngày split."""
    return {
        "binhquan": _build_donut_chart(so_du_tdps_binh_quan_by_nhom(selected_date)),
        "ngay": _build_donut_chart(so_du_tdps_ngay_by_nhom(selected_date)),
    }


def build_so_du_hdls_donut_charts(selected_date: str) -> dict:
    """Số dư HĐLS donuts, one per (Loại số liệu, Loại) combination — bình quân/ngày × Tất
    cả/CCS/IRS, same _build_donut_chart as TDPS's, just six series to pick from instead of two."""
    return {
        "binhquan-all": _build_donut_chart(so_du_hdls_binh_quan_by_nhom(selected_date)),
        "binhquan-ccs": _build_donut_chart(so_du_ccs_binh_quan_by_nhom(selected_date)),
        "binhquan-irs": _build_donut_chart(so_du_irs_binh_quan_by_nhom(selected_date)),
        "ngay-all": _build_donut_chart(so_du_hdls_ngay_by_nhom(selected_date)),
        "ngay-ccs": _build_donut_chart(so_du_ccs_ngay_by_nhom(selected_date)),
        "ngay-irs": _build_donut_chart(so_du_irs_ngay_by_nhom(selected_date)),
    }


def _build_line_chart(df: pd.DataFrame, value_col: str) -> str:
    """One line per nhóm phụ trách over the date window. Unlike the stacked version the series
    are drawn independently, so the y range comes from individual values rather than daily
    totals — and a nhóm posting a loss pulls the axis below zero."""
    scale, unit = 1_000_000, "M"
    dates = sorted(d for d in df["ngay"].unique() if pd.Timestamp(d).dayofweek < 5)
    pivot = (
        df.pivot_table(index="ngay", columns="nhom_phu_trach", values=value_col, fill_value=0.0)
        .reindex(columns=STACK_ORDER, fill_value=0.0)
        .reindex(dates, fill_value=0.0)
    )

    chart_h, left_pad, top_pad, bottom_pad, right_pad = 180, 55, 20, 55, 10
    scaled = pivot / scale
    max_val = max(scaled.max().max() if len(scaled) else 0, 1)
    min_val = min(scaled.min().min() if len(scaled) else 0, 0)
    step = _nice_step(max(max_val, abs(min_val)))
    grid_max = step * math.ceil(max_val / step)
    grid_min = -step * math.ceil(abs(min_val) / step)
    span = grid_max - grid_min

    def y_of(value: float) -> float:
        if not span:
            return top_pad + chart_h
        return top_pad + chart_h - chart_h * (value - grid_min) / span

    n = len(dates)
    plot_w = max(STACKED_CHART_TARGET_WIDTH - left_pad - right_pad, 100)
    x_step = plot_w / (n - 1) if n > 1 else 0
    width = round(left_pad + plot_w + right_pad, 1)
    height = chart_h + top_pad + bottom_pad

    def x_of(i: int) -> float:
        return left_pad + i * x_step if n > 1 else left_pad + plot_w / 2

    label_decimals = max(0, -math.floor(math.log10(step))) if step else 0
    n_ticks = int(round(span / step)) if step else 0
    grid_lines = []
    for i in range(n_ticks + 1):
        v = grid_min + i * step
        y = y_of(v)
        grid_lines.append(f'<line x1="{left_pad}" y1="{y:.1f}" x2="{width - right_pad}" y2="{y:.1f}" stroke="var(--border)" stroke-dasharray="2,2" />')
        grid_lines.append(f'<text x="{left_pad - 8}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="var(--muted-foreground)">{v:,.{label_decimals}f}{unit}</text>')

    series = []
    for grp in STACK_ORDER:
        points = " ".join(f"{x_of(i):.1f},{y_of(scaled.loc[d, grp]):.1f}" for i, d in enumerate(dates))
        series.append(
            f'<polyline points="{points}" fill="none" stroke="{STACK_COLORS[grp]}" '
            f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />'
        )
        for i, d in enumerate(dates):
            series.append(
                f'<circle cx="{x_of(i):.1f}" cy="{y_of(scaled.loc[d, grp]):.1f}" r="2.5" fill="{STACK_COLORS[grp]}" />'
            )

    hover_rects = []
    x_labels = []
    label_every = max(1, n // 10)
    band = x_step if x_step else plot_w
    for i, d in enumerate(dates):
        d_label = pd.to_datetime(d).strftime("%d/%m")
        lines = "\n".join(f"{g}: {scaled.loc[d, g]:,.1f}{unit}" for g in STACK_ORDER)
        summary = f"{d_label}\n{lines}\nTổng: {scaled.loc[d].sum():,.1f}{unit}"
        hover_rects.append(
            f'<rect x="{x_of(i) - band / 2:.1f}" y="{top_pad}" width="{band:.1f}" height="{chart_h}" '
            f'fill="transparent"><title>{summary}</title></rect>'
        )
        if i % label_every == 0:
            lx, ly = x_of(i), top_pad + chart_h + 14
            x_labels.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" text-anchor="end" '
                f'fill="var(--foreground)" transform="rotate(-45 {lx:.1f} {ly:.1f})">{d_label}</text>'
            )

    legend = "".join(
        f'<span><span style="display:inline-block;width:14px;height:3px;background:{STACK_COLORS[g]};margin-right:6px;border-radius:2px;vertical-align:middle;"></span>{g}</span>'
        for g in STACK_ORDER
    )

    return f'''
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block; width:100%; height:auto;" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        <line x1="{left_pad}" y1="{y_of(0):.1f}" x2="{width - right_pad}" y2="{y_of(0):.1f}" stroke="var(--foreground)" />
        {''.join(series)}
        {''.join(x_labels)}
        {''.join(hover_rects)}
    </svg>
    <div style="display:flex; gap:20px; justify-content:center; margin-top:8px; font-size:12px;">
        {legend}
    </div>
    '''


def build_ds_mbnt_line_chart(selected_date: str, days: int = 30) -> str:
    return _build_line_chart(ds_mbnt_stacked(selected_date, days), "sum_ds_mbnt_ngay_bc")


def build_ln_mbnt_line_chart(selected_date: str, days: int = 30) -> str:
    return _build_line_chart(ln_mbnt_stacked(selected_date, days), "sum_ln_mbnt_ngay_bao_cao")


def build_ds_hdls_line_chart(selected_date: str, days: int = 30) -> str:
    return _build_line_chart(ds_hdls_stacked(selected_date, days), "sum_ds_hdls_ngay_bc")


def build_ln_hdls_line_chart(selected_date: str, days: int = 30) -> str:
    return _build_line_chart(ln_hdls_stacked(selected_date, days), "sum_ln_hdls_ngay_bc")


def build_ln_tdps_line_chart(selected_date: str, days: int = 30) -> str:
    return _build_line_chart(ln_tdps_stacked(selected_date, days), "sum_ln_tdps_ngay_bc")


def build_ds_tdps_line_chart(selected_date: str, days: int = 30) -> str:
    return _build_line_chart(ds_tdps_stacked(selected_date, days), "sum_ds_tdps_ngay_bc")


def build_ds_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                           pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        y1_ds_mbnt_by_nhom_diaban(date_2025), y_ds_mbnt_by_nhom_diaban(selected_date), "dia_ban",
        "doanh_so", 1_000_000_000, "bn", "Doanh Số", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026,
        label_decimals=2
    )


def build_ds_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                         pool_nhom: bool = False, only_2026: bool = False) -> str:
    df_2025 = y1_ds_mbnt_by_nhom_pkkh(date_2025)
    df_2026 = y_ds_mbnt_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED_MBNT)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED_MBNT)]
    target = kh_ds_mbnt_by_nhom_pkkh(selected_date)
    return _build_clustered_chart(
        df_2025, df_2026, "pkkh", "doanh_so", 1_000_000_000, "bn", "Doanh Số", nhom_filter,
        target_series=target, pool_nhom=pool_nhom, only_2026=only_2026, label_decimals=2
    )


def build_nim_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                            pool_nhom: bool = False, only_2026: bool = False) -> str:
    # NIM is a ratio (LN/DS) — it can't be summed across nhóm like the other measures, so
    # pool_nhom here means "recompute a genuine combined NIM" (aggregate LN ÷ aggregate DS per
    # dia_ban), not the usual sum-then-groupby _build_clustered_chart does for everything else.
    if pool_nhom:
        df_2025, df_2026 = y1_nim_diaban_pooled(date_2025), y_nim_diaban_pooled(selected_date)
    else:
        df_2025, df_2026 = y1_nim_by_nhom_diaban(date_2025), y_nim_by_nhom_diaban(selected_date)
    return _build_clustered_chart(
        df_2025, df_2026, "dia_ban", "nim", 1, "", "NIM", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026,
        label_decimals=2
    )


def build_nim_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                          pool_nhom: bool = False, only_2026: bool = False) -> str:
    if pool_nhom:
        df_2025, df_2026 = y1_nim_pkkh_pooled(date_2025), y_nim_pkkh_pooled(selected_date)
    else:
        df_2025, df_2026 = y1_nim_by_nhom_pkkh(date_2025), y_nim_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED_MBNT)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED_MBNT)]
    return _build_clustered_chart(
        df_2025, df_2026, "pkkh", "nim", 1, "", "NIM", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026,
        label_decimals=2
    )


def build_ln_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                           pool_nhom: bool = False, only_2026: bool = False) -> str:
    target = kh_mbnt_by_nhom_diaban(selected_date)
    return _build_clustered_chart(
        y1_ln_mbnt_by_nhom_diaban(date_2025), y_ln_mbnt_by_nhom_diaban(selected_date), "dia_ban",
        "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, target_series=target,
        pool_nhom=pool_nhom, only_2026=only_2026, label_decimals=2
    )


def build_ln_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                         pool_nhom: bool = False, only_2026: bool = False) -> str:
    df_2025 = y1_ln_mbnt_by_nhom_pkkh(date_2025)
    df_2026 = y_ln_mbnt_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED_MBNT)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED_MBNT)]
    target = kh_mbnt_by_nhom_pkkh(selected_date)
    return _build_clustered_chart(
        df_2025, df_2026, "pkkh", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter,
        target_series=target, pool_nhom=pool_nhom, only_2026=only_2026, label_decimals=2
    )


def build_ln_hdls_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                pool_nhom: bool = False, only_2026: bool = False) -> str:
    target = kh_hdls_by_nhom_diaban(selected_date)
    return _build_clustered_chart(
        y1_ln_hdls_by_nhom_diaban(date_2025), y_ln_hdls_by_nhom_diaban(selected_date), "dia_ban",
        "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, target_series=target,
        pool_nhom=pool_nhom, only_2026=only_2026, label_decimals=2
    )


def build_ln_hdls_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                              pool_nhom: bool = False, only_2026: bool = False) -> str:
    df_2025 = y1_ln_hdls_by_nhom_pkkh(date_2025)
    df_2026 = y_ln_hdls_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED)]
    return _build_clustered_chart(
        df_2025, df_2026, "pkkh", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter,
        pool_nhom=pool_nhom, only_2026=only_2026, label_decimals=2
    )


def build_nim_hdls_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                 pool_nhom: bool = False) -> str:
    """NIM HĐLS by dia_ban — single-series, not clustered: nim_hdls_diaban_pkkh.py's source
    table has no 2025 rows to compare against, unlike DS/LN's own dedicated Y1 sources."""
    df = nim_hdls_diaban_pooled(selected_date) if pool_nhom else nim_hdls_by_nhom_diaban(selected_date)
    return _build_daily_dim_chart(
        df, "dia_ban", "nim", "NIM", nhom_filter, scale=1, unit="", period_label="2026", pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_nim_hdls_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                               pool_nhom: bool = False) -> str:
    df = (
        nim_hdls_pkkh_pooled(selected_date) if pool_nhom
        else _drop_excluded_pkkh(nim_hdls_by_nhom_pkkh(selected_date))
    )
    return _build_daily_dim_chart(
        df, "pkkh", "nim", "NIM", nhom_filter, scale=1, unit="", period_label="2026", pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_nim_hdls_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None,
                                       pool_nhom: bool = False) -> str:
    df = nim_hdls_ngay_diaban_pooled(selected_date) if pool_nhom else nim_hdls_ngay_by_nhom_diaban(selected_date)
    return _build_daily_dim_chart(df, "dia_ban", "nim", "NIM", nhom_filter, scale=1, unit="", pool_nhom=pool_nhom, label_decimals=2)


def build_nim_hdls_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None,
                                     pool_nhom: bool = False) -> str:
    df = (
        nim_hdls_ngay_pkkh_pooled(selected_date) if pool_nhom
        else _drop_excluded_pkkh(nim_hdls_ngay_by_nhom_pkkh(selected_date))
    )
    return _build_daily_dim_chart(df, "pkkh", "nim", "NIM", nhom_filter, scale=1, unit="", pool_nhom=pool_nhom, label_decimals=2)


def build_ds_hdls_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                pool_nhom: bool = False, only_2026: bool = False) -> str:
    """Stacked IRS+CCS — see y_ds_hdls_irs_ccs_by_nhom_diaban for why LN has no equivalent
    stacked chart (no per-sub-product LN column exists at customer level)."""
    return _build_stacked_clustered_chart(
        y1_ds_hdls_irs_ccs_by_nhom_diaban(date_2025), y_ds_hdls_irs_ccs_by_nhom_diaban(selected_date),
        "dia_ban", ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"],
        1_000_000, "M", "Doanh Số", nhom_filter, pool_nhom=pool_nhom,
        seg_colors_2025=["#99F6E4", "#FDE68A"],
    )


def build_ds_hdls_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                              pool_nhom: bool = False, only_2026: bool = False) -> str:
    df_2025 = y1_ds_hdls_irs_ccs_by_nhom_pkkh(date_2025)
    df_2026 = y_ds_hdls_irs_ccs_by_nhom_pkkh(selected_date)
    df_2025 = df_2025[~df_2025["pkkh"].isin(PKKH_EXCLUDED)]
    df_2026 = df_2026[~df_2026["pkkh"].isin(PKKH_EXCLUDED)]
    return _build_stacked_clustered_chart(
        df_2025, df_2026, "pkkh", ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"],
        1_000_000, "M", "Doanh Số", nhom_filter, pool_nhom=pool_nhom,
        seg_colors_2025=["#99F6E4", "#FDE68A"],
    )


# --- "Trong ngày" counterparts of the six charts above. Same dimensions and same Chỉ tiêu /
# Nhóm filters, but the value is that day's own movement (cumulative today - cumulative
# previous report day) instead of the YTD cumulative, and single-series instead of 2026-vs-2025.

def _drop_excluded_pkkh(df: pd.DataFrame, excluded: set = PKKH_EXCLUDED) -> pd.DataFrame:
    return df[~df["pkkh"].isin(excluded)]


# These pass no scale/unit: a day's movement swings between a few hundred thousand đồng and
# several billion depending on product, nhóm and how busy the day was, so the unit is chosen
# per chart from the data itself (see _auto_money_unit). NIM alone fixes scale=1, being a ratio.
# date_2025 is currently unused — kept so these keep the same signature as their lũy kế twins
# and the route can call both uniformly. It was previously used to pin the columns to the lũy
# kế chart's set; that was dropped when Trong ngày moved to showing only non-zero columns.
def build_ds_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ds_mbnt_by_nhom_diaban(selected_date), "dia_ban", "doanh_so", "Doanh Số", nhom_filter,
        pool_nhom=pool_nhom
    )


def build_ds_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ds_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT), "pkkh", "doanh_so",
        "Doanh Số", nhom_filter, pool_nhom=pool_nhom
    )


def build_nim_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None,
                                  pool_nhom: bool = False) -> str:
    df = daily_nim_diaban_pooled(selected_date) if pool_nhom else daily_nim_by_nhom_diaban(selected_date)
    return _build_daily_dim_chart(
        df, "dia_ban", "nim", "NIM", nhom_filter, scale=1, unit="", pool_nhom=pool_nhom, label_decimals=2
    )


def build_nim_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None,
                                pool_nhom: bool = False) -> str:
    df = (
        daily_nim_pkkh_pooled(selected_date) if pool_nhom
        else _drop_excluded_pkkh(daily_nim_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT)
    )
    return _build_daily_dim_chart(df, "pkkh", "nim", "NIM", nhom_filter, scale=1, unit="", pool_nhom=pool_nhom, label_decimals=2)


def build_ln_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ln_mbnt_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan", "Lợi Nhuận", nhom_filter,
        pool_nhom=pool_nhom
    )


def build_ln_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ln_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT), "pkkh", "loi_nhuan",
        "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom
    )


def build_ds_hdls_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_stacked_daily_chart(
        daily_ds_hdls_irs_ccs_by_nhom_diaban(selected_date), "dia_ban",
        ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"], nhom_filter, pool_nhom=pool_nhom
    )


def build_ds_hdls_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_stacked_daily_chart(
        _drop_excluded_pkkh(daily_ds_hdls_irs_ccs_by_nhom_pkkh(selected_date)), "pkkh",
        ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"], nhom_filter, pool_nhom=pool_nhom
    )


def build_ln_hdls_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ln_hdls_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan", "Lợi Nhuận", nhom_filter,
        pool_nhom=pool_nhom
    )


def build_ln_hdls_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ln_hdls_by_nhom_pkkh(selected_date)), "pkkh", "loi_nhuan",
        "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom
    )


# --- TDPS: the same four lũy kế charts as HĐLS (DS/LN x địa bàn/PKKH) plus their Trong ngày
# counterparts. Scales mirror HĐLS's — TDPS doanh số runs in the hundreds of millions and its
# lợi nhuận in the tens of billions.

def build_ds_tdps_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        y1_ds_tdps_by_nhom_diaban(date_2025), y_ds_tdps_by_nhom_diaban(selected_date), "dia_ban",
        "doanh_so", 1_000_000, "M", "Doanh Số", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026
    )


def build_ds_tdps_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                              pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        _drop_excluded_pkkh(y1_ds_tdps_by_nhom_pkkh(date_2025)),
        _drop_excluded_pkkh(y_ds_tdps_by_nhom_pkkh(selected_date)),
        "pkkh", "doanh_so", 1_000_000, "M", "Doanh Số", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026
    )


def build_ln_tdps_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                pool_nhom: bool = False, only_2026: bool = False) -> str:
    target = kh_tdps_by_nhom_diaban(selected_date)
    return _build_clustered_chart(
        y1_ln_tdps_by_nhom_diaban(date_2025), y_ln_tdps_by_nhom_diaban(selected_date), "dia_ban",
        "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, target_series=target,
        pool_nhom=pool_nhom, only_2026=only_2026, label_decimals=2
    )


def build_ln_tdps_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                              pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        _drop_excluded_pkkh(y1_ln_tdps_by_nhom_pkkh(date_2025)),
        _drop_excluded_pkkh(y_ln_tdps_by_nhom_pkkh(selected_date)),
        "pkkh", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom,
        only_2026=only_2026, label_decimals=2
    )


def build_nim_tdps_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                 pool_nhom: bool = False) -> str:
    """NIM TDPS by dia_ban — single-series, not clustered: nim_tdps_diaban_pkkh.py's source
    table has no 2025 rows to compare against."""
    df = nim_tdps_diaban_pooled(selected_date) if pool_nhom else nim_tdps_by_nhom_diaban(selected_date)
    return _build_daily_dim_chart(
        df, "dia_ban", "nim", "NIM", nhom_filter, scale=1, unit="", period_label="2026", pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_nim_tdps_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                               pool_nhom: bool = False) -> str:
    df = (
        nim_tdps_pkkh_pooled(selected_date) if pool_nhom
        else _drop_excluded_pkkh(nim_tdps_by_nhom_pkkh(selected_date))
    )
    return _build_daily_dim_chart(
        df, "pkkh", "nim", "NIM", nhom_filter, scale=1, unit="", period_label="2026", pool_nhom=pool_nhom,
        label_decimals=2
    )


def build_nim_tdps_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None,
                                       pool_nhom: bool = False) -> str:
    df = nim_tdps_ngay_diaban_pooled(selected_date) if pool_nhom else nim_tdps_ngay_by_nhom_diaban(selected_date)
    return _build_daily_dim_chart(df, "dia_ban", "nim", "NIM", nhom_filter, scale=1, unit="", pool_nhom=pool_nhom, label_decimals=2)


def build_nim_tdps_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None,
                                     pool_nhom: bool = False) -> str:
    df = (
        nim_tdps_ngay_pkkh_pooled(selected_date) if pool_nhom
        else _drop_excluded_pkkh(nim_tdps_ngay_by_nhom_pkkh(selected_date))
    )
    return _build_daily_dim_chart(df, "pkkh", "nim", "NIM", nhom_filter, scale=1, unit="", pool_nhom=pool_nhom, label_decimals=2)


def build_ds_tdps_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ds_tdps_by_nhom_diaban(selected_date), "dia_ban", "doanh_so", "Doanh Số", nhom_filter,
        pool_nhom=pool_nhom
    )


def build_ds_tdps_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ds_tdps_by_nhom_pkkh(selected_date)), "pkkh", "doanh_so",
        "Doanh Số", nhom_filter, pool_nhom=pool_nhom
    )


def build_ln_tdps_diaban_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ln_tdps_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan", "Lợi Nhuận", nhom_filter,
        pool_nhom=pool_nhom
    )


def build_ln_tdps_pkkh_chart_daily(selected_date: str, date_2025: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ln_tdps_by_nhom_pkkh(selected_date)), "pkkh", "loi_nhuan",
        "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom
    )


# PSHH's Doanh số stays split TLHH (lots)/OTC (USD) here too — same reasoning as the scorecard
# cards. TLHH gets its own "lots" unit (scale=1); OTC uses the same 1_000_000_000/"bn" USD
# convention as every other product's Doanh số (see ds_ln_pshh.py's module docstring).
def build_ds_tlhh_pshh_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                     pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        y1_ds_pshh_tlhh_by_nhom_diaban(date_2025), ds_pshh_tlhh_by_nhom_diaban(selected_date), "dia_ban",
        "doanh_so", 1, " lots", "Doanh Số TLHH", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026
    )


def build_ds_tlhh_pshh_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                   pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        _drop_excluded_pkkh(y1_ds_pshh_tlhh_by_nhom_pkkh(date_2025)),
        _drop_excluded_pkkh(ds_pshh_tlhh_by_nhom_pkkh(selected_date)),
        "pkkh", "doanh_so", 1, " lots", "Doanh Số TLHH", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026
    )


def build_ds_otc_pshh_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                    pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        y1_ds_pshh_otc_by_nhom_diaban(date_2025), ds_pshh_otc_by_nhom_diaban(selected_date), "dia_ban",
        "doanh_so", 1_000_000_000, "bn", "Doanh Số OTC", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026,
        label_decimals=2
    )


def build_ds_otc_pshh_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                  pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        _drop_excluded_pkkh(y1_ds_pshh_otc_by_nhom_pkkh(date_2025)),
        _drop_excluded_pkkh(ds_pshh_otc_by_nhom_pkkh(selected_date)),
        "pkkh", "doanh_so", 1_000_000_000, "bn", "Doanh Số OTC", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026,
        label_decimals=2
    )


def build_ln_pshh_diaban_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                                pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        y1_ln_pshh_by_nhom_diaban(date_2025), ln_pshh_by_nhom_diaban(selected_date), "dia_ban",
        "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom, only_2026=only_2026,
        label_decimals=2
    )


def build_ln_pshh_pkkh_chart(selected_date: str, date_2025: str, nhom_filter: str = None,
                              pool_nhom: bool = False, only_2026: bool = False) -> str:
    return _build_clustered_chart(
        _drop_excluded_pkkh(y1_ln_pshh_by_nhom_pkkh(date_2025)),
        _drop_excluded_pkkh(ln_pshh_by_nhom_pkkh(selected_date)),
        "pkkh", "loi_nhuan", 1_000_000_000, "bn", "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom,
        only_2026=only_2026, label_decimals=2
    )


def build_ds_tlhh_pshh_diaban_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ds_pshh_tlhh_by_nhom_diaban(selected_date), "dia_ban", "doanh_so", "Doanh Số TLHH",
        nhom_filter, scale=1, unit=" lots", pool_nhom=pool_nhom
    )


def build_ds_tlhh_pshh_pkkh_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ds_pshh_tlhh_by_nhom_pkkh(selected_date)), "pkkh", "doanh_so",
        "Doanh Số TLHH", nhom_filter, scale=1, unit=" lots", pool_nhom=pool_nhom
    )


def build_ds_otc_pshh_diaban_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ds_pshh_otc_by_nhom_diaban(selected_date), "dia_ban", "doanh_so", "Doanh Số OTC",
        nhom_filter, pool_nhom=pool_nhom
    )


def build_ds_otc_pshh_pkkh_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ds_pshh_otc_by_nhom_pkkh(selected_date)), "pkkh", "doanh_so",
        "Doanh Số OTC", nhom_filter, pool_nhom=pool_nhom
    )


def build_ln_pshh_diaban_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        daily_ln_pshh_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan", "Lợi Nhuận",
        nhom_filter, pool_nhom=pool_nhom
    )


def build_ln_pshh_pkkh_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(daily_ln_pshh_by_nhom_pkkh(selected_date)), "pkkh", "loi_nhuan",
        "Lợi Nhuận", nhom_filter, pool_nhom=pool_nhom
    )


# Số dư is a point-in-time balance, not a flow, so it is always single-series — pvkh_dailyreport
# starts at 2026-01-01, so there is no Y-1 balance to cluster against even if one were wanted.
# "Ngày" is that day's own snapshot; "lũy kế" is the year-to-date average balance (bq_nam), the
# only sense in which balance "accumulates" — see so_du_hdls_diaban_pkkh.py / tdps_diaban_pkkh.py.
def build_so_du_tdps_diaban_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        so_du_tdps_by_nhom_diaban(selected_date), "dia_ban", "so_du", "Số Dư", nhom_filter, pool_nhom=pool_nhom
    )


def build_so_du_tdps_pkkh_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(so_du_tdps_by_nhom_pkkh(selected_date)), "pkkh", "so_du",
        "Số Dư", nhom_filter, pool_nhom=pool_nhom
    )


def build_so_du_tdps_diaban_chart_luy_ke(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        so_du_tdps_luy_ke_by_nhom_diaban(selected_date), "dia_ban", "so_du", "Số Dư", nhom_filter,
        period_label="bình quân năm", empty_message="Không có số dư", pool_nhom=pool_nhom
    )


def build_so_du_tdps_pkkh_chart_luy_ke(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(so_du_tdps_luy_ke_by_nhom_pkkh(selected_date)), "pkkh", "so_du",
        "Số Dư", nhom_filter, period_label="bình quân năm", empty_message="Không có số dư", pool_nhom=pool_nhom
    )


def build_so_du_hdls_diaban_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_stacked_daily_chart(
        so_du_hdls_irs_ccs_ngay_by_nhom_diaban(selected_date), "dia_ban",
        ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"], nhom_filter, pool_nhom=pool_nhom
    )


def build_so_du_hdls_pkkh_chart_daily(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_stacked_daily_chart(
        _drop_excluded_pkkh(so_du_hdls_irs_ccs_ngay_by_nhom_pkkh(selected_date)), "pkkh",
        ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"], nhom_filter, pool_nhom=pool_nhom
    )


def build_so_du_hdls_diaban_chart_luy_ke(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_stacked_daily_chart(
        so_du_hdls_irs_ccs_luy_ke_by_nhom_diaban(selected_date), "dia_ban",
        ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"], nhom_filter,
        period_label="bình quân năm", empty_message="Không có số dư", pool_nhom=pool_nhom
    )


def build_so_du_hdls_pkkh_chart_luy_ke(selected_date: str, nhom_filter: str = None, pool_nhom: bool = False) -> str:
    return _build_stacked_daily_chart(
        _drop_excluded_pkkh(so_du_hdls_irs_ccs_luy_ke_by_nhom_pkkh(selected_date)), "pkkh",
        ["irs", "ccs"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"], nhom_filter,
        period_label="bình quân năm", empty_message="Không có số dư", pool_nhom=pool_nhom
    )


# Tổng quan's Số dư TDPS/CCS/IRS theo địa bàn/PKKH — pvkh_pstc_dia_ban/pkkh instead of exploding
# pvkh_dailyreport, since Tổng quan pools every nhóm together anyway and these pre-aggregated
# tables have no nhóm dimension to lose (see calculations/so_du_pstc_diaban_pkkh.py). Nhóm phụ
# trách's own Số dư charts keep using so_du_tdps/hdls_luy_ke_by_nhom_diaban/pkkh above, which
# still need the customer-level pvkh_dailyreport path to break out by nhóm.
def build_tq_so_du_tdps_diaban_chart(selected_date: str) -> str:
    return _build_daily_dim_chart(
        so_du_tdps_pstc_by_diaban(selected_date), "dia_ban", "so_du", "Số Dư", pool_nhom=True,
        period_label="bình quân năm", empty_message="Không có số dư"
    )


def build_tq_so_du_tdps_pkkh_chart(selected_date: str) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(so_du_tdps_pstc_by_pkkh(selected_date)), "pkkh", "so_du", "Số Dư",
        pool_nhom=True, period_label="bình quân năm", empty_message="Không có số dư"
    )


# Trong ngày counterparts — same pvkh_pstc_dia_ban/pkkh source, the sum_so_du_*_ngay_bc columns
# instead of the *_binh_quan ones (see calculations/so_du_pstc_diaban_pkkh.py's "ngày" section).
def build_tq_so_du_tdps_diaban_chart_daily(selected_date: str) -> str:
    return _build_daily_dim_chart(
        so_du_tdps_pstc_ngay_by_diaban(selected_date), "dia_ban", "so_du", "Số Dư", pool_nhom=True,
        empty_message="Không có số dư"
    )


def build_tq_so_du_tdps_pkkh_chart_daily(selected_date: str) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(so_du_tdps_pstc_ngay_by_pkkh(selected_date)), "pkkh", "so_du", "Số Dư",
        pool_nhom=True, empty_message="Không có số dư"
    )


def build_tq_so_du_hdls_diaban_chart_daily(selected_date: str) -> str:
    return _build_daily_dim_chart(
        so_du_hdls_pstc_ngay_by_diaban(selected_date), "dia_ban", "so_du", "Số Dư", pool_nhom=True,
        empty_message="Không có số dư"
    )


def build_tq_so_du_hdls_pkkh_chart_daily(selected_date: str) -> str:
    return _build_daily_dim_chart(
        _drop_excluded_pkkh(so_du_hdls_pstc_ngay_by_pkkh(selected_date)), "pkkh", "so_du", "Số Dư",
        pool_nhom=True, empty_message="Không có số dư"
    )


def build_tq_so_du_hdls_diaban_chart(selected_date: str) -> str:
    # Split into IRS/CCS segments (so_du_hdls_stack_pstc_by_diaban) instead of one flat total —
    # matches Doanh Số HĐLS's own IRS+CCS stacked chart just above it.
    return _build_stacked_daily_chart(
        so_du_hdls_stack_pstc_by_diaban(selected_date), "dia_ban",
        ["so_du_irs_binh_quan", "so_du_ccs_binh_quan"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"],
        pool_nhom=True, period_label="bình quân năm", empty_message="Không có số dư"
    )


def build_tq_so_du_hdls_pkkh_chart(selected_date: str) -> str:
    return _build_stacked_daily_chart(
        _drop_excluded_pkkh(so_du_hdls_stack_pstc_by_pkkh(selected_date)), "pkkh",
        ["so_du_irs_binh_quan", "so_du_ccs_binh_quan"], ["IRS", "CCS"], ["#14B8A6", "#FFD700"],
        pool_nhom=True, period_label="bình quân năm", empty_message="Không có số dư"
    )


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
    if nhom != "Tất cả":
        df = df[df["Nhóm phụ trách"] == nhom]
    sub = df.sort_values("% năm", ascending=False)[CN_TRONG_DIEM_COLUMNS].copy()
    sub = sub[sub["KQ KDNT&PS (tr đồng)"].fillna(0) != 0]
    if nhom == "Tất cả":
        # STT from branch_table() is RANKX(...) within each Nhóm phụ trách (matching Power BI's
        # ALLSELECTED context when one nhóm is selected), so it repeats 1..N per nhóm. With no
        # nhóm filter, ALLSELECTED spans every branch, so STT here must be one global rank
        # instead of those per-nhóm duplicates.
        sub["STT"] = sub["% năm"].rank(method="dense", ascending=False)
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
    if nhom != "Tất cả":
        df = df[df["Nhóm phụ trách"] == nhom]
    sub = df.sort_values("% năm", ascending=False)[CN_CANBO_COLUMNS].copy()
    sub = sub[sub["KQ KDNT&PS (tr đồng)"].fillna(0) != 0]
    if nhom == "Tất cả":
        # Same fix as build_cn_trong_diem_table — see that comment for why.
        sub["STT"] = sub["% năm"].rank(method="dense", ascending=False)
    stt_colors = compute_stt_gradient_colors(sub)
    sub["STT"] = sub["STT"].map(lambda v: f"{v:.0f}" if pd.notna(v) else "")
    sub["Thay đổi (m/m)"] = sub["Thay đổi (m/m)"].fillna("")
    for col in CN_CANBO_VALUE_COLUMNS:
        sub[col] = sub[col].map(lambda v: f"{v:,.2f}" if pd.notna(v) else "")
    for col in CN_CANBO_PCT_COLUMNS:
        sub[col] = sub[col].map(lambda v: f"{v * 100:,.2f}%" if pd.notna(v) else "")
    return render_table(sub, stt_colors=stt_colors)


def build_note_line(text: str) -> str:
    """Italic asterisked footnote placed *outside* and below a charts panel, flush to the left
    edge — the same treatment as Tổng quan's "*Số liệu được lấy từ 30 ngày gần nhất"."""
    return (f'<div style="font-style:italic; font-size:12px; color:var(--primary); '
            f'margin-top:8px;">*{text}</div>')


def build_section_label(text: str) -> str:
    """Tổng quan's section divider — the same coloured ribbon pill removed earlier this
    session ("remove all ribbons"), reinstated here specifically per a later request."""
    return f'<div class="ribbon ribbon-1">{text}</div>'


def build_nav_html(active_tab: str) -> str:
    items = []
    for tab_id, icon, label in NAV_TABS:
        active_class = " active" if tab_id == active_tab else ""
        items.append(
            f'<button class="nav-item{active_class}" data-tab="{tab_id}" onclick="showTab(\'{tab_id}\')">'
            f'<span class="nav-item-icon">{icon}</span><span>{label}</span></button>'
        )
    return "".join(items)


NHOM_VALUES = ["Tất cả", "PTKD 1", "PTKD 2", "VPV"]


def nhom_variants(build_fn, active_nhom: str) -> str:
    """Render `build_fn` once per nhóm phụ trách and stack the results, showing only the active
    one. onHeaderNhomChange then swaps them client-side instead of navigating.

    The filter used to reload the page with ?nhom=..., which cannot work in an exported HTML
    file: there is no server to re-render, so the static file reloaded itself and the figures
    never changed. Baking all four costs ~250KB on a ~720KB export (the nhóm-dependent blocks
    are only ~11% of the page) and makes the filter instant on the live dashboard too.

    build_fn takes the nhom_filter value the builders expect — None for "Tất cả"."""
    return "".join(
        f'<div class="nhom-variant" data-nhom="{n}"'
        f'{"" if n == active_nhom else " style=&quot;display:none&quot;"}>'
        f'{build_fn(None if n == "Tất cả" else n)}</div>'
        for n in NHOM_VALUES
    ).replace("&quot;", '"')


def build_nhom_select_html(select_id: str, nhom: str) -> str:
    """Inline Nhóm phụ trách select (same options/behavior as the topbar one) for placing
    next to a Chỉ tiêu control — needs its own unique id since the topbar's #header-nhom-select
    already exists in the same page."""
    options = "".join(
        f'<option value="{value}"{" selected" if nhom == value else ""}>{value}</option>'
        for value in ["Tất cả", "PTKD 1", "PTKD 2", "VPV"]
    )
    return f'''
        <div class="filter-group-compact">
            <label class="filter-label">Nhóm phụ trách</label>
            <select class="filter-select" id="{select_id}" onchange="onHeaderNhomChange(this.value)">
                {options}
            </select>
        </div>
    '''


@app.route("/")
def show_table():
    selected_date = request.args.get("date") or latest_date()
    date_2025 = same_day_last_year(selected_date)
    nhom = request.args.get("nhom", "PTKD 1")
    nhom_filter = None if nhom == "Tất cả" else nhom
    valid_tab_ids = {tab_id for tab_id, _, _ in NAV_TABS}
    active_tab = request.args.get("tab", "sanpham")
    if active_tab not in valid_tab_ids:
        active_tab = "sanpham"
    export_mode = request.args.get("export_img") == "1"

    mbnt_df = bao_cao_ket_qua_mbnt_2025_2026(selected_date)
    hdls_df = bao_cao_ket_qua_hdls_2025_2026(selected_date)

    # Khách hàng tab's "Top 10 KH" (raw-value) tables, Trong ngày variant: per-customer
    # cumulative(selected_date) - cumulative(previous trading date), so ranking reflects that
    # single day's own DS/LN instead of the YTD lũy kế total.
    _prev_date = previous_date(selected_date)
    mbnt_df_prev = bao_cao_ket_qua_mbnt_2025_2026(_prev_date) if _prev_date else None
    hdls_df_prev = bao_cao_ket_qua_hdls_2025_2026(_prev_date) if _prev_date else None
    mbnt_daily_df = mbnt_daily_customer_df(mbnt_df, mbnt_df_prev)
    hdls_daily_df = hdls_daily_customer_df(hdls_df, hdls_df_prev)

    kpi_cards = build_kpi_row_by_sanpham(selected_date)
    kpi_cards_daily = build_kpi_row_by_sanpham_daily(selected_date)
    ds_mbnt_cards = build_ds_mbnt_row(selected_date, date_2025)
    ds_mbnt_cards_daily = build_ds_mbnt_row_daily(selected_date)
    mbnt_nim_charts = build_nim_mbnt_charts(selected_date, date_2025)
    mbnt_nim_charts_daily = build_nim_mbnt_charts_daily(selected_date)
    hdls_nim_chart = build_nim_hdls_charts(selected_date)
    hdls_nim_chart_daily = build_nim_hdls_charts_daily(selected_date)
    tdps_nim_chart = build_nim_tdps_charts(selected_date)
    tdps_nim_chart_daily = build_nim_tdps_charts_daily(selected_date)
    tdps_sodu_charts = build_so_du_tdps_donut_charts(selected_date)
    hdls_sodu_charts = build_so_du_hdls_donut_charts(selected_date)
    ds_hdls_cards = build_ds_hdls_row(selected_date)
    ds_hdls_cards_daily = build_ds_hdls_row_daily(selected_date)
    tdps_cards_daily = build_tdps_row_daily(selected_date)
    tdps_cards_ytd = build_tdps_row_ytd(selected_date)
    ds_all_cards = build_ds_all_row(selected_date, date_2025)
    ds_all_cards_daily = build_ds_all_row_daily(selected_date)

    # nhom_filter=None means "Tất cả" was selected — pool_nhom=(nf is None) switches those charts
    # from clustering every nhóm side by side to a genuine pooled/combined figure per dim_col.
    ds_diaban_chart = nhom_variants(lambda nf: build_ds_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_pkkh_chart = nhom_variants(lambda nf: build_ds_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_diaban_chart = nhom_variants(lambda nf: build_nim_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_pkkh_chart = nhom_variants(lambda nf: build_nim_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_diaban_chart = nhom_variants(lambda nf: build_ln_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_pkkh_chart = nhom_variants(lambda nf: build_ln_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    ln_hdls_diaban_chart = nhom_variants(lambda nf: build_ln_hdls_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_hdls_pkkh_chart = nhom_variants(lambda nf: build_ln_hdls_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_hdls_diaban_chart = nhom_variants(lambda nf: build_ds_hdls_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_hdls_pkkh_chart = nhom_variants(lambda nf: build_ds_hdls_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_hdls_diaban_chart = nhom_variants(lambda nf: build_nim_hdls_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_hdls_pkkh_chart = nhom_variants(lambda nf: build_nim_hdls_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    ds_diaban_chart_daily = nhom_variants(lambda nf: build_ds_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_pkkh_chart_daily = nhom_variants(lambda nf: build_ds_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_diaban_chart_daily = nhom_variants(lambda nf: build_nim_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_pkkh_chart_daily = nhom_variants(lambda nf: build_nim_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_diaban_chart_daily = nhom_variants(lambda nf: build_ln_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_pkkh_chart_daily = nhom_variants(lambda nf: build_ln_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    ds_hdls_diaban_chart_daily = nhom_variants(lambda nf: build_ds_hdls_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_hdls_pkkh_chart_daily = nhom_variants(lambda nf: build_ds_hdls_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_hdls_diaban_chart_daily = nhom_variants(lambda nf: build_ln_hdls_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_hdls_pkkh_chart_daily = nhom_variants(lambda nf: build_ln_hdls_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_hdls_diaban_chart_daily = nhom_variants(lambda nf: build_nim_hdls_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_hdls_pkkh_chart_daily = nhom_variants(lambda nf: build_nim_hdls_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    ds_all_diaban_chart = nhom_variants(lambda nf: build_ds_all_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_all_pkkh_chart = nhom_variants(lambda nf: build_ds_all_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_all_diaban_chart = nhom_variants(lambda nf: build_ln_all_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_all_pkkh_chart = nhom_variants(lambda nf: build_ln_all_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_all_diaban_chart_daily = nhom_variants(lambda nf: build_ds_all_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_all_pkkh_chart_daily = nhom_variants(lambda nf: build_ds_all_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_all_diaban_chart_daily = nhom_variants(lambda nf: build_ln_all_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_all_pkkh_chart_daily = nhom_variants(lambda nf: build_ln_all_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    # Doanh số tỷ trọng đóng góp (%) by dia_ban/PKKH — nhom_filter here just scopes which
    # nhóm's own total the % is taken against; unlike the amount charts above there's no
    # pool_nhom toggle, since a % share is always "pooled" relative to whatever scope is active.
    ds_contribution_diaban_chart = nhom_variants(lambda nf: build_ds_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    ds_contribution_pkkh_chart = nhom_variants(lambda nf: build_ds_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)
    ds_contribution_diaban_chart_daily = nhom_variants(lambda nf: build_ds_contribution_diaban_chart_daily(selected_date, nhom_filter=nf), nhom)
    ds_contribution_pkkh_chart_daily = nhom_variants(lambda nf: build_ds_contribution_pkkh_chart_daily(selected_date, nhom_filter=nf), nhom)

    # Each sản phẩm's own (not pooled) lũy kế tỷ trọng đóng góp — MBNT/HĐLS get DS+LN, TDPS/HĐLS
    # also get Số Dư (MBNT has no Số Dư measure at all).
    ds_mbnt_contrib_diaban_chart = nhom_variants(lambda nf: build_ds_mbnt_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    ds_mbnt_contrib_pkkh_chart = nhom_variants(lambda nf: build_ds_mbnt_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)
    ln_mbnt_contrib_diaban_chart = nhom_variants(lambda nf: build_ln_mbnt_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    ln_mbnt_contrib_pkkh_chart = nhom_variants(lambda nf: build_ln_mbnt_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)

    ds_hdls_contrib_diaban_chart = nhom_variants(lambda nf: build_ds_hdls_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    ds_hdls_contrib_pkkh_chart = nhom_variants(lambda nf: build_ds_hdls_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)
    ln_hdls_contrib_diaban_chart = nhom_variants(lambda nf: build_ln_hdls_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    ln_hdls_contrib_pkkh_chart = nhom_variants(lambda nf: build_ln_hdls_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)
    sodu_hdls_contrib_diaban_chart = nhom_variants(lambda nf: build_sodu_hdls_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    sodu_hdls_contrib_pkkh_chart = nhom_variants(lambda nf: build_sodu_hdls_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)

    ds_tdps_diaban_chart = nhom_variants(lambda nf: build_ds_tdps_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_tdps_pkkh_chart = nhom_variants(lambda nf: build_ds_tdps_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_tdps_diaban_chart = nhom_variants(lambda nf: build_ln_tdps_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_tdps_pkkh_chart = nhom_variants(lambda nf: build_ln_tdps_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_tdps_diaban_chart = nhom_variants(lambda nf: build_nim_tdps_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_tdps_pkkh_chart = nhom_variants(lambda nf: build_nim_tdps_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_tdps_diaban_chart_daily = nhom_variants(lambda nf: build_ds_tdps_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_tdps_pkkh_chart_daily = nhom_variants(lambda nf: build_ds_tdps_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_tdps_diaban_chart_daily = nhom_variants(lambda nf: build_ln_tdps_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_tdps_pkkh_chart_daily = nhom_variants(lambda nf: build_ln_tdps_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_tdps_diaban_chart_daily = nhom_variants(lambda nf: build_nim_tdps_diaban_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    nim_tdps_pkkh_chart_daily = nhom_variants(lambda nf: build_nim_tdps_pkkh_chart_daily(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    ds_tdps_contrib_diaban_chart = nhom_variants(lambda nf: build_ds_tdps_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    ds_tdps_contrib_pkkh_chart = nhom_variants(lambda nf: build_ds_tdps_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)
    ln_tdps_contrib_diaban_chart = nhom_variants(lambda nf: build_ln_tdps_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    ln_tdps_contrib_pkkh_chart = nhom_variants(lambda nf: build_ln_tdps_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)
    sodu_tdps_contrib_diaban_chart = nhom_variants(lambda nf: build_sodu_tdps_contribution_diaban_chart(selected_date, nhom_filter=nf), nhom)
    sodu_tdps_contrib_pkkh_chart = nhom_variants(lambda nf: build_sodu_tdps_contribution_pkkh_chart(selected_date, nhom_filter=nf), nhom)
    so_du_tdps_diaban_chart_daily = nhom_variants(lambda nf: build_so_du_tdps_diaban_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    so_du_tdps_pkkh_chart_daily = nhom_variants(lambda nf: build_so_du_tdps_pkkh_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    so_du_tdps_diaban_chart_luy_ke = nhom_variants(lambda nf: build_so_du_tdps_diaban_chart_luy_ke(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    so_du_tdps_pkkh_chart_luy_ke = nhom_variants(lambda nf: build_so_du_tdps_pkkh_chart_luy_ke(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    so_du_hdls_diaban_chart_daily = nhom_variants(lambda nf: build_so_du_hdls_diaban_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    so_du_hdls_pkkh_chart_daily = nhom_variants(lambda nf: build_so_du_hdls_pkkh_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    so_du_hdls_diaban_chart_luy_ke = nhom_variants(lambda nf: build_so_du_hdls_diaban_chart_luy_ke(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    so_du_hdls_pkkh_chart_luy_ke = nhom_variants(lambda nf: build_so_du_hdls_pkkh_chart_luy_ke(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    pshh_cards_ytd = build_pshh_row_ytd(selected_date, date_2025)
    pshh_cards_daily = build_pshh_row_daily(selected_date)
    ds_tlhh_pshh_diaban_chart = nhom_variants(lambda nf: build_ds_tlhh_pshh_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_tlhh_pshh_pkkh_chart = nhom_variants(lambda nf: build_ds_tlhh_pshh_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_otc_pshh_diaban_chart = nhom_variants(lambda nf: build_ds_otc_pshh_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_otc_pshh_pkkh_chart = nhom_variants(lambda nf: build_ds_otc_pshh_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_pshh_diaban_chart = nhom_variants(lambda nf: build_ln_pshh_diaban_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_pshh_pkkh_chart = nhom_variants(lambda nf: build_ln_pshh_pkkh_chart(selected_date, date_2025, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_tlhh_pshh_diaban_chart_daily = nhom_variants(lambda nf: build_ds_tlhh_pshh_diaban_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_tlhh_pshh_pkkh_chart_daily = nhom_variants(lambda nf: build_ds_tlhh_pshh_pkkh_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_otc_pshh_diaban_chart_daily = nhom_variants(lambda nf: build_ds_otc_pshh_diaban_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ds_otc_pshh_pkkh_chart_daily = nhom_variants(lambda nf: build_ds_otc_pshh_pkkh_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_pshh_diaban_chart_daily = nhom_variants(lambda nf: build_ln_pshh_diaban_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)
    ln_pshh_pkkh_chart_daily = nhom_variants(lambda nf: build_ln_pshh_pkkh_chart_daily(selected_date, nhom_filter=nf, pool_nhom=(nf is None)), nhom)

    mbnt_pct_sections = build_sections(
        get_top_bottom_by_group_mbnt(mbnt_df, n=10), "▲LN%",
        "Top KH tăng trưởng LN cao nhất", "Top KH tăng trưởng LN thấp nhất"
    )
    mbnt_abs_sections = build_sections(
        get_top_bottom_by_group_abs_mbnt(mbnt_df, n=10), "▲LN",
        "Top KH tăng trưởng LN tuyệt đối cao nhất", "Top KH tăng trưởng LN tuyệt đối thấp nhất"
    )
    hdls_pct_sections = build_sections(
        get_top_bottom_by_group_hdls(hdls_df, n=10), "▲LN%",
        "Top KH tăng trưởng LN cao nhất", "Top KH tăng trưởng LN thấp nhất"
    )
    hdls_abs_sections = build_sections(
        get_top_bottom_by_group_abs_hdls(hdls_df, n=10), "▲LN",
        "Top KH tăng trưởng LN tuyệt đối cao nhất", "Top KH tăng trưởng LN tuyệt đối thấp nhất"
    )

    mbnt_ds_sections = build_sections(
        get_top_bottom_by_value_ds_mbnt(mbnt_df, n=10), "DS (tr USD)",
        "Top KH doanh số cao nhất", include_bottom=False
    )
    mbnt_ln_sections = build_sections(
        get_top_bottom_by_value_ln_mbnt(mbnt_df, n=10), "LN (tr VND)",
        "Top KH lợi nhuận cao nhất", include_bottom=False
    )
    hdls_ds_sections = build_sections(
        get_top_bottom_by_value_ds_hdls(hdls_df, n=10), "DS (tr USD)",
        "Top KH doanh số cao nhất", include_bottom=False
    )
    hdls_ln_sections = build_sections(
        get_top_bottom_by_value_ln_hdls(hdls_df, n=10), "LN (tr VND)",
        "Top KH lợi nhuận cao nhất", include_bottom=False
    )

    mbnt_ds_sections_daily = build_sections(
        get_top_bottom_by_value_ds_mbnt_daily(mbnt_daily_df, n=10), "DS (tr USD)",
        "Top KH doanh số cao nhất (trong ngày)", include_bottom=False
    )
    mbnt_ln_sections_daily = build_sections(
        get_top_bottom_by_value_ln_mbnt_daily(mbnt_daily_df, n=10), "LN (tr VND)",
        "Top KH lợi nhuận cao nhất (trong ngày)", include_bottom=False
    )
    hdls_ds_sections_daily = build_sections(
        get_top_bottom_by_value_ds_hdls_daily(hdls_daily_df, n=10), "DS (tr USD)",
        "Top KH doanh số cao nhất (trong ngày)", include_bottom=False
    )
    hdls_ln_sections_daily = build_sections(
        get_top_bottom_by_value_ln_hdls_daily(hdls_daily_df, n=10), "LN (tr VND)",
        "Top KH lợi nhuận cao nhất (trong ngày)", include_bottom=False
    )

    cn_trong_diem_table = nhom_variants(lambda nf: build_cn_trong_diem_table(selected_date, nf or "Tất cả"), nhom)
    cn_canbo_table = nhom_variants(lambda nf: build_cn_canbo_table(selected_date, nf or "Tất cả"), nhom)

    date_table_df = get_date_table()  # already sorted newest first
    # Last 2 working weeks only. Weekend rows exist in the source but aren't trading days,
    # so they're dropped before taking the window — otherwise 10 rows would only reach back
    # about a week and a half of actual business days. Exports get one working week instead.
    n_dates = DATE_OPTIONS_EXPORT_WORKING_DAYS if export_mode else DATE_OPTIONS_WORKING_DAYS
    option_dates = date_table_df[date_table_df["date"].dt.dayofweek < 5].head(n_dates)
    # A date passed in the URL (bookmark, shared link, older date) must stay selectable —
    # otherwise the dropdown would show a different date than the page actually rendered.
    if selected_date not in set(option_dates["date"].dt.strftime("%Y-%m-%d")):
        viewed = date_table_df[date_table_df["date"].dt.strftime("%Y-%m-%d") == selected_date]
        option_dates = pd.concat([option_dates, viewed]).sort_values("date", ascending=False)

    if not export_mode:
        missing_pinned = DATE_OPTIONS_PINNED - set(option_dates["date"].dt.strftime("%Y-%m-%d"))
        if missing_pinned:
            pinned = date_table_df[date_table_df["date"].dt.strftime("%Y-%m-%d").isin(missing_pinned)]
            option_dates = pd.concat([option_dates, pinned]).sort_values("date", ascending=False)

    date_table_df = option_dates
    date_options = "".join(
        f'<option value="{iso}"{" selected" if iso == selected_date else ""}>{weekday} - {display}</option>'
        for iso, display, weekday in zip(
            date_table_df["date"].dt.strftime("%Y-%m-%d"),
            date_table_df["date"].dt.strftime("%d/%m/%Y"),
            date_table_df["date"].dt.dayofweek.map(WEEKDAY_LABELS),
        )
    )

    # Pooled (pool_nhom=True) dia_ban/PKKH breakdowns, one bar-pair (2026 vs 2025) per
    # dia_ban/PKKH value summed across every nhóm — Tổng quan has no nhóm selector. All 12
    # (3 sản phẩm x 2 chỉ tiêu x 2 dimensions) are baked into the page and toggled client-side
    # by the Sản phẩm/Chỉ tiêu selects below, instead of being shown all at once.
    tq_ds_diaban_chart = build_ds_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_ds_pkkh_chart = build_ds_pkkh_chart(selected_date, date_2025, pool_nhom=True)
    tq_ln_diaban_chart = build_ln_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_ln_pkkh_chart = build_ln_pkkh_chart(selected_date, date_2025, pool_nhom=True)

    tq_ds_hdls_diaban_chart = build_ds_hdls_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_ds_hdls_pkkh_chart = build_ds_hdls_pkkh_chart(selected_date, date_2025, pool_nhom=True)
    tq_ln_hdls_diaban_chart = build_ln_hdls_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_ln_hdls_pkkh_chart = build_ln_hdls_pkkh_chart(selected_date, date_2025, pool_nhom=True)

    tq_ds_tdps_diaban_chart = build_ds_tdps_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_ds_tdps_pkkh_chart = build_ds_tdps_pkkh_chart(selected_date, date_2025, pool_nhom=True)
    tq_ln_tdps_diaban_chart = build_ln_tdps_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_ln_tdps_pkkh_chart = build_ln_tdps_pkkh_chart(selected_date, date_2025, pool_nhom=True)

    # NIM is a ratio, not an additive amount — pool_nhom=True here doesn't sum it across nhóm
    # like DS/LN, it recomputes a genuine combined NIM (aggregate LN ÷ aggregate DS per dia_ban/
    # pkkh), so Tổng quan can show one bar per dia_ban/PKKH value like every other chart on the
    # tab instead of clustering by nhóm phụ trách. only_2026=True to match NIM HĐLS/TDPS below,
    # which have no Y1 baseline to compare against at all — legend reads "NIM 2026" everywhere.
    tq_nim_diaban_chart = build_nim_diaban_chart(selected_date, date_2025, pool_nhom=True, only_2026=True)
    tq_nim_pkkh_chart = build_nim_pkkh_chart(selected_date, date_2025, pool_nhom=True, only_2026=True)
    tq_nim_hdls_diaban_chart = build_nim_hdls_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_nim_hdls_pkkh_chart = build_nim_hdls_pkkh_chart(selected_date, date_2025, pool_nhom=True)
    tq_nim_tdps_diaban_chart = build_nim_tdps_diaban_chart(selected_date, date_2025, pool_nhom=True)
    tq_nim_tdps_pkkh_chart = build_nim_tdps_pkkh_chart(selected_date, date_2025, pool_nhom=True)

    # Số dư (balance) is additive, so these pool like DS/LN. Bình quân năm (YTD average), the
    # closest thing Số dư has to a "lũy kế" figure, matching the other Tổng quan cards' scope —
    # no Doanh số/Lợi nhuận-style Trong ngày toggle exists on this tab. MBNT has no Số dư measure
    # at all (see so_du_hdls_diaban_pkkh.py / tdps_diaban_pkkh.py).
    tq_sodu_hdls_diaban_chart = build_tq_so_du_hdls_diaban_chart(selected_date)
    tq_sodu_hdls_pkkh_chart = build_tq_so_du_hdls_pkkh_chart(selected_date)
    tq_sodu_tdps_diaban_chart = build_tq_so_du_tdps_diaban_chart(selected_date)
    tq_sodu_tdps_pkkh_chart = build_tq_so_du_tdps_pkkh_chart(selected_date)

    # Doanh số tỷ trọng đóng góp (%): each dia_ban/PKKH's share of that sản phẩm's own doanh số
    # total, 2026 only. Same PKKH exclusion sets as each product's amount chart above, so the
    # slice list here matches what's actually plotted there.
    tq_ds_diaban_contrib_chart = _build_contribution_chart(
        y_ds_mbnt_by_nhom_diaban(selected_date), "dia_ban", "doanh_so"
    )
    tq_ds_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(y_ds_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT), "pkkh", "doanh_so"
    )
    tq_ds_hdls_diaban_contrib_chart = _build_contribution_chart(
        y_ds_hdls_by_nhom_diaban(selected_date), "dia_ban", "doanh_so"
    )
    tq_ds_hdls_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(y_ds_hdls_by_nhom_pkkh(selected_date)), "pkkh", "doanh_so"
    )
    tq_ds_tdps_diaban_contrib_chart = _build_contribution_chart(
        y_ds_tdps_by_nhom_diaban(selected_date), "dia_ban", "doanh_so"
    )
    tq_ds_tdps_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(y_ds_tdps_by_nhom_pkkh(selected_date)), "pkkh", "doanh_so"
    )

    # Lợi nhuận tỷ trọng đóng góp (%) — same shape/scope as doanh số's, just the LN source per
    # sản phẩm. No KBNN/PKKH-exclusion inconsistency vs the amount charts above: each pulls from
    # the exact same y_ln_*_by_nhom_diaban/pkkh functions those charts already use.
    tq_ln_mbnt_diaban_contrib_chart = _build_contribution_chart(
        y_ln_mbnt_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan"
    )
    tq_ln_mbnt_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(y_ln_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT), "pkkh", "loi_nhuan"
    )
    tq_ln_hdls_diaban_contrib_chart = _build_contribution_chart(
        y_ln_hdls_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan"
    )
    tq_ln_hdls_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(y_ln_hdls_by_nhom_pkkh(selected_date)), "pkkh", "loi_nhuan"
    )
    tq_ln_tdps_diaban_contrib_chart = _build_contribution_chart(
        y_ln_tdps_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan"
    )
    tq_ln_tdps_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(y_ln_tdps_by_nhom_pkkh(selected_date)), "pkkh", "loi_nhuan"
    )

    # Số dư tỷ trọng đóng góp (%) — MBNT has no Số dư measure at all, so no mbnt variant here
    # (matches the "Số Dư" chỉ tiêu option being hidden for MBNT in the toolbar). HĐLS shows two
    # separate donuts (CCS, IRS) side by side rather than one combined figure — per user request.
    tq_sodu_ccs_hdls_diaban_contrib_chart = _build_contribution_chart(
        so_du_ccs_pstc_by_diaban(selected_date), "dia_ban", "so_du"
    )
    tq_sodu_irs_hdls_diaban_contrib_chart = _build_contribution_chart(
        so_du_irs_pstc_by_diaban(selected_date), "dia_ban", "so_du"
    )
    tq_sodu_ccs_hdls_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(so_du_ccs_pstc_by_pkkh(selected_date)), "pkkh", "so_du"
    )
    tq_sodu_irs_hdls_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(so_du_irs_pstc_by_pkkh(selected_date)), "pkkh", "so_du"
    )
    tq_sodu_tdps_diaban_contrib_chart = _build_contribution_chart(
        so_du_tdps_pstc_by_diaban(selected_date), "dia_ban", "so_du"
    )
    tq_sodu_tdps_pkkh_contrib_chart = _build_contribution_chart(
        _drop_excluded_pkkh(so_du_tdps_pstc_by_pkkh(selected_date)), "pkkh", "so_du"
    )

    # ============================== Trong ngày counterparts ==============================
    # Same 12 (amount) + 6 (NIM) + 4 (Số dư) chart slots as the lũy kế block above, single-day
    # figures instead of YTD-cumulative, all already-existing "_daily" builders (built for Nhóm
    # phụ trách's own Trong ngày toggle) called with pool_nhom=True — no target_series support
    # on this code path at all, so no KHKD dashed line can appear here, per request. Số dư keeps
    # reading pvkh_pstc_dia_ban/pkkh (the "ngày" columns) rather than falling back to the
    # customer-level pvkh_dailyreport path Nhóm phụ trách uses, for the same reason the lũy kế
    # Số dư charts were switched to that table earlier.
    tq_ds_diaban_chart_daily = build_ds_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ds_pkkh_chart_daily = build_ds_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ln_diaban_chart_daily = build_ln_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ln_pkkh_chart_daily = build_ln_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)

    tq_ds_hdls_diaban_chart_daily = build_ds_hdls_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ds_hdls_pkkh_chart_daily = build_ds_hdls_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ln_hdls_diaban_chart_daily = build_ln_hdls_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ln_hdls_pkkh_chart_daily = build_ln_hdls_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)

    tq_ds_tdps_diaban_chart_daily = build_ds_tdps_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ds_tdps_pkkh_chart_daily = build_ds_tdps_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ln_tdps_diaban_chart_daily = build_ln_tdps_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_ln_tdps_pkkh_chart_daily = build_ln_tdps_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)

    tq_nim_diaban_chart_daily = build_nim_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_nim_pkkh_chart_daily = build_nim_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_nim_hdls_diaban_chart_daily = build_nim_hdls_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_nim_hdls_pkkh_chart_daily = build_nim_hdls_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_nim_tdps_diaban_chart_daily = build_nim_tdps_diaban_chart_daily(selected_date, date_2025, pool_nhom=True)
    tq_nim_tdps_pkkh_chart_daily = build_nim_tdps_pkkh_chart_daily(selected_date, date_2025, pool_nhom=True)

    tq_sodu_hdls_diaban_chart_daily = build_tq_so_du_hdls_diaban_chart_daily(selected_date)
    tq_sodu_hdls_pkkh_chart_daily = build_tq_so_du_hdls_pkkh_chart_daily(selected_date)
    tq_sodu_tdps_diaban_chart_daily = build_tq_so_du_tdps_diaban_chart_daily(selected_date)
    tq_sodu_tdps_pkkh_chart_daily = build_tq_so_du_tdps_pkkh_chart_daily(selected_date)

    # Tỷ trọng đóng góp donuts, trong ngày — same _build_contribution_chart, fed from the same
    # single-day dimension data the amount charts above use instead of the YTD one.
    tq_ds_diaban_contrib_chart_daily = _build_contribution_chart(
        daily_ds_mbnt_by_nhom_diaban(selected_date), "dia_ban", "doanh_so"
    )
    tq_ds_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(daily_ds_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT), "pkkh", "doanh_so"
    )
    tq_ds_hdls_diaban_contrib_chart_daily = _build_contribution_chart(
        daily_ds_hdls_by_nhom_diaban(selected_date), "dia_ban", "doanh_so"
    )
    tq_ds_hdls_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(daily_ds_hdls_by_nhom_pkkh(selected_date)), "pkkh", "doanh_so"
    )
    tq_ds_tdps_diaban_contrib_chart_daily = _build_contribution_chart(
        daily_ds_tdps_by_nhom_diaban(selected_date), "dia_ban", "doanh_so"
    )
    tq_ds_tdps_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(daily_ds_tdps_by_nhom_pkkh(selected_date)), "pkkh", "doanh_so"
    )

    tq_ln_mbnt_diaban_contrib_chart_daily = _build_contribution_chart(
        daily_ln_mbnt_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan"
    )
    tq_ln_mbnt_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(daily_ln_mbnt_by_nhom_pkkh(selected_date), PKKH_EXCLUDED_MBNT), "pkkh", "loi_nhuan"
    )
    tq_ln_hdls_diaban_contrib_chart_daily = _build_contribution_chart(
        daily_ln_hdls_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan"
    )
    tq_ln_hdls_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(daily_ln_hdls_by_nhom_pkkh(selected_date)), "pkkh", "loi_nhuan"
    )
    tq_ln_tdps_diaban_contrib_chart_daily = _build_contribution_chart(
        daily_ln_tdps_by_nhom_diaban(selected_date), "dia_ban", "loi_nhuan"
    )
    tq_ln_tdps_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(daily_ln_tdps_by_nhom_pkkh(selected_date)), "pkkh", "loi_nhuan"
    )

    tq_sodu_ccs_hdls_diaban_contrib_chart_daily = _build_contribution_chart(
        so_du_ccs_pstc_ngay_by_diaban(selected_date), "dia_ban", "so_du"
    )
    tq_sodu_irs_hdls_diaban_contrib_chart_daily = _build_contribution_chart(
        so_du_irs_pstc_ngay_by_diaban(selected_date), "dia_ban", "so_du"
    )
    tq_sodu_ccs_hdls_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(so_du_ccs_pstc_ngay_by_pkkh(selected_date)), "pkkh", "so_du"
    )
    tq_sodu_irs_hdls_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(so_du_irs_pstc_ngay_by_pkkh(selected_date)), "pkkh", "so_du"
    )
    tq_sodu_tdps_diaban_contrib_chart_daily = _build_contribution_chart(
        so_du_tdps_pstc_ngay_by_diaban(selected_date), "dia_ban", "so_du"
    )
    tq_sodu_tdps_pkkh_contrib_chart_daily = _build_contribution_chart(
        _drop_excluded_pkkh(so_du_tdps_pstc_ngay_by_pkkh(selected_date)), "pkkh", "so_du"
    )

    nav_html = build_nav_html(active_tab)
    theme_js = build_theme_js(nhom, active_tab)

    tab_sanpham = f"""
        <div class="kpi-row" id="sanpham-kpi-row-ytd">{''.join(kpi_cards)}</div>
        <div class="kpi-row" id="sanpham-kpi-row-daily" style="display:none;">{''.join(kpi_cards_daily)}</div>

        <div class="charts-panel">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Sản phẩm</label>
                    <select class="filter-select" id="tq-sanpham-select" onchange="onTqChartFilterChange()">
                        <option value="mbnt">Mua bán ngoại tệ</option>
                        <option value="hdls">Hoán đổi lãi suất</option>
                        <option value="tdps">Tín dụng phái sinh</option>
                    </select>
                </div>
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" id="tq-chitieu-select" onchange="onTqChartFilterChange()">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                        <option value="nim">NIM</option>
                        <option value="sodu" disabled hidden>Số Dư</option>
                    </select>
                </div>
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tq-diaban-mbnt-ds">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo địa bàn</h2>
                        {tq_ds_diaban_chart}
                    </div>
                    <div id="tq-diaban-mbnt-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo địa bàn</h2>
                        {tq_ln_diaban_chart}
                    </div>
                    <div id="tq-diaban-mbnt-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo địa bàn</h2>
                        {tq_nim_diaban_chart}
                    </div>
                    <div id="tq-diaban-hdls-ds" style="display:none;">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo địa bàn</h2>
                        {tq_ds_hdls_diaban_chart}
                    </div>
                    <div id="tq-diaban-hdls-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo địa bàn</h2>
                        {tq_ln_hdls_diaban_chart}
                    </div>
                    <div id="tq-diaban-hdls-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo địa bàn</h2>
                        {tq_nim_hdls_diaban_chart}
                    </div>
                    <div id="tq-diaban-hdls-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư hoán đổi lãi suất theo địa bàn</h2>
                        {tq_sodu_hdls_diaban_chart}
                    </div>
                    <div id="tq-diaban-tdps-ds" style="display:none;">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo địa bàn</h2>
                        {tq_ds_tdps_diaban_chart}
                    </div>
                    <div id="tq-diaban-tdps-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo địa bàn</h2>
                        {tq_ln_tdps_diaban_chart}
                    </div>
                    <div id="tq-diaban-tdps-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo địa bàn</h2>
                        {tq_nim_tdps_diaban_chart}
                    </div>
                    <div id="tq-diaban-tdps-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư tín dụng phái sinh theo địa bàn</h2>
                        {tq_sodu_tdps_diaban_chart}
                    </div>
                    <div id="tq-diaban-mbnt-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo địa bàn (trong ngày)</h2>
                        {tq_ds_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-mbnt-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo địa bàn (trong ngày)</h2>
                        {tq_ln_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-mbnt-nim-daily" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo địa bàn (trong ngày)</h2>
                        {tq_nim_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-hdls-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo địa bàn (trong ngày)</h2>
                        {tq_ds_hdls_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-hdls-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo địa bàn (trong ngày)</h2>
                        {tq_ln_hdls_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-hdls-nim-daily" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo địa bàn (trong ngày)</h2>
                        {tq_nim_hdls_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-hdls-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Số dư hoán đổi lãi suất theo địa bàn (trong ngày)</h2>
                        {tq_sodu_hdls_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-tdps-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo địa bàn (trong ngày)</h2>
                        {tq_ds_tdps_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-tdps-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo địa bàn (trong ngày)</h2>
                        {tq_ln_tdps_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-tdps-nim-daily" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo địa bàn (trong ngày)</h2>
                        {tq_nim_tdps_diaban_chart_daily}
                    </div>
                    <div id="tq-diaban-tdps-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Số dư tín dụng phái sinh theo địa bàn (trong ngày)</h2>
                        {tq_sodu_tdps_diaban_chart_daily}
                    </div>
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tq-pkkh-mbnt-ds">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo PKKH</h2>
                        {tq_ds_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-mbnt-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo PKKH</h2>
                        {tq_ln_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-mbnt-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo PKKH</h2>
                        {tq_nim_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-hdls-ds" style="display:none;">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo PKKH</h2>
                        {tq_ds_hdls_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-hdls-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo PKKH</h2>
                        {tq_ln_hdls_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-hdls-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo PKKH</h2>
                        {tq_nim_hdls_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-hdls-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư hoán đổi lãi suất theo PKKH</h2>
                        {tq_sodu_hdls_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-tdps-ds" style="display:none;">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo PKKH</h2>
                        {tq_ds_tdps_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-tdps-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo PKKH</h2>
                        {tq_ln_tdps_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-tdps-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo PKKH</h2>
                        {tq_nim_tdps_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-tdps-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư tín dụng phái sinh theo PKKH</h2>
                        {tq_sodu_tdps_pkkh_chart}
                    </div>
                    <div id="tq-pkkh-mbnt-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo PKKH (trong ngày)</h2>
                        {tq_ds_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-mbnt-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo PKKH (trong ngày)</h2>
                        {tq_ln_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-mbnt-nim-daily" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo PKKH (trong ngày)</h2>
                        {tq_nim_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-hdls-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo PKKH (trong ngày)</h2>
                        {tq_ds_hdls_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-hdls-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo PKKH (trong ngày)</h2>
                        {tq_ln_hdls_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-hdls-nim-daily" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo PKKH (trong ngày)</h2>
                        {tq_nim_hdls_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-hdls-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Số dư hoán đổi lãi suất theo PKKH (trong ngày)</h2>
                        {tq_sodu_hdls_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-tdps-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo PKKH (trong ngày)</h2>
                        {tq_ds_tdps_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-tdps-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo PKKH (trong ngày)</h2>
                        {tq_ln_tdps_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-tdps-nim-daily" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo PKKH (trong ngày)</h2>
                        {tq_nim_tdps_pkkh_chart_daily}
                    </div>
                    <div id="tq-pkkh-tdps-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Số dư tín dụng phái sinh theo PKKH (trong ngày)</h2>
                        {tq_sodu_tdps_pkkh_chart_daily}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="tq-contrib-panel">
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tq-diaban-contrib-mbnt-ds">
                        <h2 style="text-align:center;">Tỷ trọng doanh số mua bán ngoại tệ theo địa bàn</h2>
                        {tq_ds_diaban_contrib_chart}
                    </div>
                    <div id="tq-diaban-contrib-mbnt-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận mua bán ngoại tệ theo địa bàn</h2>
                        {tq_ln_mbnt_diaban_contrib_chart}
                    </div>
                    <div id="tq-diaban-contrib-hdls-ds" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số hoán đổi lãi suất theo địa bàn</h2>
                        {tq_ds_hdls_diaban_contrib_chart}
                    </div>
                    <div id="tq-diaban-contrib-hdls-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận hoán đổi lãi suất theo địa bàn</h2>
                        {tq_ln_hdls_diaban_contrib_chart}
                    </div>
                    <div id="tq-diaban-contrib-hdls-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư hoán đổi lãi suất theo địa bàn</h2>
                        <div style="display:flex; flex-wrap:wrap;">
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">CCS</h3>
                                {tq_sodu_ccs_hdls_diaban_contrib_chart}
                            </div>
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">IRS</h3>
                                {tq_sodu_irs_hdls_diaban_contrib_chart}
                            </div>
                        </div>
                    </div>
                    <div id="tq-diaban-contrib-tdps-ds" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số tín dụng phái sinh theo địa bàn</h2>
                        {tq_ds_tdps_diaban_contrib_chart}
                    </div>
                    <div id="tq-diaban-contrib-tdps-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận tín dụng phái sinh theo địa bàn</h2>
                        {tq_ln_tdps_diaban_contrib_chart}
                    </div>
                    <div id="tq-diaban-contrib-tdps-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư tín dụng phái sinh theo địa bàn</h2>
                        {tq_sodu_tdps_diaban_contrib_chart}
                    </div>
                    <div id="tq-diaban-contrib-mbnt-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số mua bán ngoại tệ theo địa bàn (trong ngày)</h2>
                        {tq_ds_diaban_contrib_chart_daily}
                    </div>
                    <div id="tq-diaban-contrib-mbnt-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận mua bán ngoại tệ theo địa bàn (trong ngày)</h2>
                        {tq_ln_mbnt_diaban_contrib_chart_daily}
                    </div>
                    <div id="tq-diaban-contrib-hdls-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số hoán đổi lãi suất theo địa bàn (trong ngày)</h2>
                        {tq_ds_hdls_diaban_contrib_chart_daily}
                    </div>
                    <div id="tq-diaban-contrib-hdls-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận hoán đổi lãi suất theo địa bàn (trong ngày)</h2>
                        {tq_ln_hdls_diaban_contrib_chart_daily}
                    </div>
                    <div id="tq-diaban-contrib-hdls-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư hoán đổi lãi suất theo địa bàn (trong ngày)</h2>
                        <div style="display:flex; flex-wrap:wrap;">
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">CCS</h3>
                                {tq_sodu_ccs_hdls_diaban_contrib_chart_daily}
                            </div>
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">IRS</h3>
                                {tq_sodu_irs_hdls_diaban_contrib_chart_daily}
                            </div>
                        </div>
                    </div>
                    <div id="tq-diaban-contrib-tdps-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số tín dụng phái sinh theo địa bàn (trong ngày)</h2>
                        {tq_ds_tdps_diaban_contrib_chart_daily}
                    </div>
                    <div id="tq-diaban-contrib-tdps-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận tín dụng phái sinh theo địa bàn (trong ngày)</h2>
                        {tq_ln_tdps_diaban_contrib_chart_daily}
                    </div>
                    <div id="tq-diaban-contrib-tdps-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư tín dụng phái sinh theo địa bàn (trong ngày)</h2>
                        {tq_sodu_tdps_diaban_contrib_chart_daily}
                    </div>
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tq-pkkh-contrib-mbnt-ds">
                        <h2 style="text-align:center;">Tỷ trọng doanh số mua bán ngoại tệ theo PKKH</h2>
                        {tq_ds_pkkh_contrib_chart}
                    </div>
                    <div id="tq-pkkh-contrib-mbnt-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận mua bán ngoại tệ theo PKKH</h2>
                        {tq_ln_mbnt_pkkh_contrib_chart}
                    </div>
                    <div id="tq-pkkh-contrib-hdls-ds" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số hoán đổi lãi suất theo PKKH</h2>
                        {tq_ds_hdls_pkkh_contrib_chart}
                    </div>
                    <div id="tq-pkkh-contrib-hdls-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận hoán đổi lãi suất theo PKKH</h2>
                        {tq_ln_hdls_pkkh_contrib_chart}
                    </div>
                    <div id="tq-pkkh-contrib-hdls-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư hoán đổi lãi suất theo PKKH</h2>
                        <div style="display:flex; flex-wrap:wrap;">
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">CCS</h3>
                                {tq_sodu_ccs_hdls_pkkh_contrib_chart}
                            </div>
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">IRS</h3>
                                {tq_sodu_irs_hdls_pkkh_contrib_chart}
                            </div>
                        </div>
                    </div>
                    <div id="tq-pkkh-contrib-tdps-ds" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số tín dụng phái sinh theo PKKH</h2>
                        {tq_ds_tdps_pkkh_contrib_chart}
                    </div>
                    <div id="tq-pkkh-contrib-tdps-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận tín dụng phái sinh theo PKKH</h2>
                        {tq_ln_tdps_pkkh_contrib_chart}
                    </div>
                    <div id="tq-pkkh-contrib-tdps-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư tín dụng phái sinh theo PKKH</h2>
                        {tq_sodu_tdps_pkkh_contrib_chart}
                    </div>
                    <div id="tq-pkkh-contrib-mbnt-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số mua bán ngoại tệ theo PKKH (trong ngày)</h2>
                        {tq_ds_pkkh_contrib_chart_daily}
                    </div>
                    <div id="tq-pkkh-contrib-mbnt-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận mua bán ngoại tệ theo PKKH (trong ngày)</h2>
                        {tq_ln_mbnt_pkkh_contrib_chart_daily}
                    </div>
                    <div id="tq-pkkh-contrib-hdls-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số hoán đổi lãi suất theo PKKH (trong ngày)</h2>
                        {tq_ds_hdls_pkkh_contrib_chart_daily}
                    </div>
                    <div id="tq-pkkh-contrib-hdls-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận hoán đổi lãi suất theo PKKH (trong ngày)</h2>
                        {tq_ln_hdls_pkkh_contrib_chart_daily}
                    </div>
                    <div id="tq-pkkh-contrib-hdls-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư hoán đổi lãi suất theo PKKH (trong ngày)</h2>
                        <div style="display:flex; flex-wrap:wrap;">
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">CCS</h3>
                                {tq_sodu_ccs_hdls_pkkh_contrib_chart_daily}
                            </div>
                            <div style="flex:1; min-width:220px;">
                                <h3 style="text-align:center; font-size:13px; color:var(--muted-foreground);">IRS</h3>
                                {tq_sodu_irs_hdls_pkkh_contrib_chart_daily}
                            </div>
                        </div>
                    </div>
                    <div id="tq-pkkh-contrib-tdps-ds-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng doanh số tín dụng phái sinh theo PKKH (trong ngày)</h2>
                        {tq_ds_tdps_pkkh_contrib_chart_daily}
                    </div>
                    <div id="tq-pkkh-contrib-tdps-ln-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng lợi nhuận tín dụng phái sinh theo PKKH (trong ngày)</h2>
                        {tq_ln_tdps_pkkh_contrib_chart_daily}
                    </div>
                    <div id="tq-pkkh-contrib-tdps-sodu-daily" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng số dư tín dụng phái sinh theo PKKH (trong ngày)</h2>
                        {tq_sodu_tdps_pkkh_contrib_chart_daily}
                    </div>
                </div>
            </div>
        </div>
    """

    tab_nhom_pt = f"""
        <div id="product-mbnt">

        <div class="kpi-row" id="mbnt-kpi-ytd">{''.join(ds_mbnt_cards)}</div>
        <div class="kpi-row" id="mbnt-kpi-daily" style="display:none;">{''.join(ds_mbnt_cards_daily)}</div>

        <div id="mbnt-nim-luykke-wrap" class="charts-panel">
            <div class="chart-card" style="max-width:{CHART_TARGET_WIDTH + 40}px; margin:0 auto;">
                <h2 style="text-align:center;">NIM lũy kế không gồm chia sẻ</h2>
                {mbnt_nim_charts}
            </div>
        </div>
        <div id="mbnt-nim-daily-wrap" style="display:none; flex-wrap:wrap; gap:16px; margin-bottom:var(--section-gap);">
            <div class="charts-panel" style="flex:1; min-width:300px; margin-bottom:0;">
                <div class="chart-card">
                    <h2 style="text-align:center;">NIM Spot Mua/Bán</h2>
                    {mbnt_nim_charts_daily['spot']}
                </div>
            </div>
            <div class="charts-panel" style="flex:1; min-width:300px; margin-bottom:0;">
                <div class="chart-card">
                    <h2 style="text-align:center;">NIM trong ngày</h2>
                    {mbnt_nim_charts_daily['ngay']}
                </div>
            </div>
        </div>

        <div class="charts-panel" id="mbnt-dim-charts">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onMbntChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                        <option value="nim">NIM</option>
                    </select>
                </div>
                {build_nhom_select_html("mbnt-nhom-select", nhom)}
                <div style="font-style:italic; font-size:12px; color:var(--primary); margin-left:auto;">*Lợi nhuận và NIM lũy kế đã trừ chia sẻ; tất cả chỉ tiêu không bao gồm Kho bạc</div>
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="mbnt-diaban-chart-ds">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo địa bàn</h2>
                        {ds_diaban_chart}
                    </div>
                    <div id="mbnt-diaban-chart-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo địa bàn</h2>
                        {nim_diaban_chart}
                    </div>
                    <div id="mbnt-diaban-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo địa bàn</h2>
                        {ln_diaban_chart}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="mbnt-pkkh-chart-ds">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo PKKH</h2>
                        {ds_pkkh_chart}
                    </div>
                    <div id="mbnt-pkkh-chart-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo PKKH</h2>
                        {nim_pkkh_chart}
                    </div>
                    <div id="mbnt-pkkh-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo PKKH</h2>
                        {ln_pkkh_chart}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="mbnt-dim-charts-daily" style="display:none;">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onMbntDailyChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                        <option value="nim">NIM</option>
                    </select>
                </div>
                {build_nhom_select_html("mbnt-nhom-select-daily", nhom)}
                <div style="font-style:italic; font-size:12px; color:var(--primary); margin-left:auto;">*Lợi nhuận và NIM trong ngày chưa trừ chia sẻ; tất cả chỉ tiêu không bao gồm Kho bạc</div>
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="mbnt-diaban-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo địa bàn</h2>
                        {ds_diaban_chart_daily}
                    </div>
                    <div id="mbnt-diaban-chart-daily-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo địa bàn</h2>
                        {nim_diaban_chart_daily}
                    </div>
                    <div id="mbnt-diaban-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo địa bàn</h2>
                        {ln_diaban_chart_daily}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="mbnt-pkkh-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số mua bán ngoại tệ theo PKKH</h2>
                        {ds_pkkh_chart_daily}
                    </div>
                    <div id="mbnt-pkkh-chart-daily-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM mua bán ngoại tệ theo PKKH</h2>
                        {nim_pkkh_chart_daily}
                    </div>
                    <div id="mbnt-pkkh-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận mua bán ngoại tệ theo PKKH</h2>
                        {ln_pkkh_chart_daily}
                    </div>
                </div>
            </div>
        </div>

        <!-- Tỷ trọng đóng góp theo Chỉ tiêu hiện chọn — không có bản NIM (tỷ lệ, không cộng
             dồn được), nên chỉ để trống khi NIM đang chọn thay vì báo lỗi thiếu phần tử. Always
             lũy kế data regardless of Lũy kế/Trong ngày toggle (no daily contribution % source
             exists yet) — moved below both dim-charts panels per user request so it reads as a
             trailing summary instead of interrupting the Trong ngày charts positionally. -->
        <div class="charts-panel">
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="mbnt-diaban-contrib-chart-ds">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo địa bàn (%)</h2>
                        {ds_mbnt_contrib_diaban_chart}
                    </div>
                    <div id="mbnt-diaban-contrib-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Lợi nhuận theo địa bàn (%)</h2>
                        {ln_mbnt_contrib_diaban_chart}
                    </div>
                    <div id="mbnt-diaban-contrib-chart-nim" style="display:none;"></div>
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="mbnt-pkkh-contrib-chart-ds">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo PKKH (%)</h2>
                        {ds_mbnt_contrib_pkkh_chart}
                    </div>
                    <div id="mbnt-pkkh-contrib-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Lợi nhuận theo PKKH (%)</h2>
                        {ln_mbnt_contrib_pkkh_chart}
                    </div>
                    <div id="mbnt-pkkh-contrib-chart-nim" style="display:none;"></div>
                </div>
            </div>
        </div>

        </div>

        <div id="product-hdls" style="display:none;">

        <div class="kpi-row" id="hdls-kpi-ytd">{''.join(ds_hdls_cards)}</div>
        <div class="kpi-row" id="hdls-kpi-daily" style="display:none;">{''.join(ds_hdls_cards_daily)}</div>

        <div style="display:flex; flex-wrap:wrap; gap:16px; margin-bottom:var(--section-gap);">
            <div class="charts-panel" id="hdls-sodu-panel" style="flex:1; min-width:400px; margin-bottom:0;">
                <div class="charts-toolbar">
                    <div class="filter-group-compact">
                        <label class="filter-label">Loại</label>
                        <select class="filter-select" onchange="onHdlsSoDuLoaiChange(this.value)">
                            <option value="all">Tất cả</option>
                            <option value="ccs">CCS</option>
                            <option value="irs">IRS</option>
                        </select>
                    </div>
                </div>
                <div class="chart-card">
                    <h2 id="hdls-sodu-title-binhquan" style="text-align:center;">Số dư HĐLS bình quân</h2>
                    <h2 id="hdls-sodu-title-ngay" style="text-align:center; display:none;">Số dư HĐLS ngày</h2>
                    <div id="hdls-sodu-chart-binhquan-all">{hdls_sodu_charts['binhquan-all']}</div>
                    <div id="hdls-sodu-chart-binhquan-ccs" style="display:none;">{hdls_sodu_charts['binhquan-ccs']}</div>
                    <div id="hdls-sodu-chart-binhquan-irs" style="display:none;">{hdls_sodu_charts['binhquan-irs']}</div>
                    <div id="hdls-sodu-chart-ngay-all" style="display:none;">{hdls_sodu_charts['ngay-all']}</div>
                    <div id="hdls-sodu-chart-ngay-ccs" style="display:none;">{hdls_sodu_charts['ngay-ccs']}</div>
                    <div id="hdls-sodu-chart-ngay-irs" style="display:none;">{hdls_sodu_charts['ngay-irs']}</div>
                </div>
            </div>

            <div class="charts-panel" id="hdls-nim-panel" style="flex:1; min-width:400px; margin-bottom:0;">
                <div class="chart-card">
                    <h2 id="hdls-nim-title-binhquan" style="text-align:center;">NIM lũy kế 2026</h2>
                    <h2 id="hdls-nim-title-ngay" style="text-align:center; display:none;">NIM trong ngày</h2>
                    <div id="hdls-nim-chart-binhquan">{hdls_nim_chart}</div>
                    <div id="hdls-nim-chart-ngay" style="display:none;">{hdls_nim_chart_daily}</div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="hdls-dim-charts">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onHdlsChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                        <option value="nim">NIM</option>
                        <option value="sodu">Số Dư</option>
                    </select>
                </div>
                {build_nhom_select_html("hdls-nhom-select", nhom)}
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="hdls-diaban-chart-ds">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo địa bàn</h2>
                        {ds_hdls_diaban_chart}
                    </div>
                    <div id="hdls-diaban-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo địa bàn</h2>
                        {ln_hdls_diaban_chart}
                    </div>
                    <div id="hdls-diaban-chart-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo địa bàn</h2>
                        {nim_hdls_diaban_chart}
                    </div>
                    <div id="hdls-diaban-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư bình quân năm hoán đổi lãi suất theo địa bàn</h2>
                        {so_du_hdls_diaban_chart_luy_ke}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="hdls-pkkh-chart-ds">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo PKKH</h2>
                        {ds_hdls_pkkh_chart}
                    </div>
                    <div id="hdls-pkkh-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo PKKH</h2>
                        {ln_hdls_pkkh_chart}
                    </div>
                    <div id="hdls-pkkh-chart-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo PKKH</h2>
                        {nim_hdls_pkkh_chart}
                    </div>
                    <div id="hdls-pkkh-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư bình quân năm hoán đổi lãi suất theo PKKH</h2>
                        {so_du_hdls_pkkh_chart_luy_ke}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="hdls-dim-charts-daily" style="display:none;">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onHdlsDailyChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                        <option value="nim">NIM</option>
                        <option value="sodu">Số Dư</option>
                    </select>
                </div>
                {build_nhom_select_html("hdls-nhom-select-daily", nhom)}
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="hdls-diaban-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo địa bàn</h2>
                        {ds_hdls_diaban_chart_daily}
                    </div>
                    <div id="hdls-diaban-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo địa bàn</h2>
                        {ln_hdls_diaban_chart_daily}
                    </div>
                    <div id="hdls-diaban-chart-daily-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo địa bàn</h2>
                        {nim_hdls_diaban_chart_daily}
                    </div>
                    <div id="hdls-diaban-chart-daily-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư hoán đổi lãi suất theo địa bàn</h2>
                        {so_du_hdls_diaban_chart_daily}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="hdls-pkkh-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số hoán đổi lãi suất theo PKKH</h2>
                        {ds_hdls_pkkh_chart_daily}
                    </div>
                    <div id="hdls-pkkh-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận hoán đổi lãi suất theo PKKH</h2>
                        {ln_hdls_pkkh_chart_daily}
                    </div>
                    <div id="hdls-pkkh-chart-daily-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM hoán đổi lãi suất theo PKKH</h2>
                        {nim_hdls_pkkh_chart_daily}
                    </div>
                    <div id="hdls-pkkh-chart-daily-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư hoán đổi lãi suất theo PKKH</h2>
                        {so_du_hdls_pkkh_chart_daily}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel">
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="hdls-diaban-contrib-chart-ds">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo địa bàn (%)</h2>
                        {ds_hdls_contrib_diaban_chart}
                    </div>
                    <div id="hdls-diaban-contrib-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Lợi nhuận theo địa bàn (%)</h2>
                        {ln_hdls_contrib_diaban_chart}
                    </div>
                    <div id="hdls-diaban-contrib-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Số dư theo địa bàn (%)</h2>
                        {sodu_hdls_contrib_diaban_chart}
                    </div>
                    <div id="hdls-diaban-contrib-chart-nim" style="display:none;"></div>
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="hdls-pkkh-contrib-chart-ds">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo PKKH (%)</h2>
                        {ds_hdls_contrib_pkkh_chart}
                    </div>
                    <div id="hdls-pkkh-contrib-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Lợi nhuận theo PKKH (%)</h2>
                        {ln_hdls_contrib_pkkh_chart}
                    </div>
                    <div id="hdls-pkkh-contrib-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Số dư theo PKKH (%)</h2>
                        {sodu_hdls_contrib_pkkh_chart}
                    </div>
                    <div id="hdls-pkkh-contrib-chart-nim" style="display:none;"></div>
                </div>
            </div>
        </div>
        </div>

        <div id="product-tdps" style="display:none;">

        <div class="kpi-row" id="tdps-kpi-ytd">{''.join(tdps_cards_ytd)}</div>
        <div class="kpi-row" id="tdps-kpi-daily" style="display:none;">{''.join(tdps_cards_daily)}</div>

        <div style="display:flex; flex-wrap:wrap; gap:16px; margin-bottom:var(--section-gap);">
            <div class="charts-panel" id="tdps-sodu-panel" style="flex:1; min-width:400px; margin-bottom:0;">
                <div class="chart-card">
                    <h2 id="tdps-sodu-title-binhquan" style="text-align:center;">Số dư TDPS bình quân</h2>
                    <h2 id="tdps-sodu-title-ngay" style="text-align:center; display:none;">Số dư TDPS ngày</h2>
                    <div id="tdps-sodu-chart-binhquan">{tdps_sodu_charts['binhquan']}</div>
                    <div id="tdps-sodu-chart-ngay" style="display:none;">{tdps_sodu_charts['ngay']}</div>
                </div>
            </div>

            <div class="charts-panel" id="tdps-nim-panel" style="flex:1; min-width:400px; margin-bottom:0;">
                <div class="chart-card">
                    <h2 id="tdps-nim-title-binhquan" style="text-align:center;">NIM lũy kế 2026</h2>
                    <h2 id="tdps-nim-title-ngay" style="text-align:center; display:none;">NIM trong ngày</h2>
                    <div id="tdps-nim-chart-binhquan">{tdps_nim_chart}</div>
                    <div id="tdps-nim-chart-ngay" style="display:none;">{tdps_nim_chart_daily}</div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="tdps-dim-charts">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onTdpsChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                        <option value="nim">NIM</option>
                        <option value="sodu">Số Dư</option>
                    </select>
                </div>
                {build_nhom_select_html("tdps-nhom-select", nhom)}
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tdps-diaban-chart-ds">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo địa bàn</h2>
                        {ds_tdps_diaban_chart}
                    </div>
                    <div id="tdps-diaban-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo địa bàn</h2>
                        {ln_tdps_diaban_chart}
                    </div>
                    <div id="tdps-diaban-chart-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo địa bàn</h2>
                        {nim_tdps_diaban_chart}
                    </div>
                    <div id="tdps-diaban-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư bình quân năm tín dụng phái sinh theo địa bàn</h2>
                        {so_du_tdps_diaban_chart_luy_ke}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tdps-pkkh-chart-ds">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo PKKH</h2>
                        {ds_tdps_pkkh_chart}
                    </div>
                    <div id="tdps-pkkh-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo PKKH</h2>
                        {ln_tdps_pkkh_chart}
                    </div>
                    <div id="tdps-pkkh-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư bình quân năm tín dụng phái sinh theo PKKH</h2>
                        {so_du_tdps_pkkh_chart_luy_ke}
                    </div>
                    <div id="tdps-pkkh-chart-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo PKKH</h2>
                        {nim_tdps_pkkh_chart}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="tdps-dim-charts-daily" style="display:none;">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onTdpsDailyChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                        <option value="sodu">Số Dư</option>
                        <option value="nim">NIM</option>
                    </select>
                </div>
                {build_nhom_select_html("tdps-nhom-select-daily", nhom)}
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tdps-diaban-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo địa bàn</h2>
                        {ds_tdps_diaban_chart_daily}
                    </div>
                    <div id="tdps-diaban-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo địa bàn</h2>
                        {ln_tdps_diaban_chart_daily}
                    </div>
                    <div id="tdps-diaban-chart-daily-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư tín dụng phái sinh theo địa bàn</h2>
                        {so_du_tdps_diaban_chart_daily}
                    </div>
                    <div id="tdps-diaban-chart-daily-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo địa bàn</h2>
                        {nim_tdps_diaban_chart_daily}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tdps-pkkh-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số tín dụng phái sinh theo PKKH</h2>
                        {ds_tdps_pkkh_chart_daily}
                    </div>
                    <div id="tdps-pkkh-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận tín dụng phái sinh theo PKKH</h2>
                        {ln_tdps_pkkh_chart_daily}
                    </div>
                    <div id="tdps-pkkh-chart-daily-sodu" style="display:none;">
                        <h2 style="text-align:center;">Số dư tín dụng phái sinh theo PKKH</h2>
                        {so_du_tdps_pkkh_chart_daily}
                    </div>
                    <div id="tdps-pkkh-chart-daily-nim" style="display:none;">
                        <h2 style="text-align:center;">NIM tín dụng phái sinh theo PKKH</h2>
                        {nim_tdps_pkkh_chart_daily}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel">
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tdps-diaban-contrib-chart-ds">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo địa bàn (%)</h2>
                        {ds_tdps_contrib_diaban_chart}
                    </div>
                    <div id="tdps-diaban-contrib-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Lợi nhuận theo địa bàn (%)</h2>
                        {ln_tdps_contrib_diaban_chart}
                    </div>
                    <div id="tdps-diaban-contrib-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Số dư theo địa bàn (%)</h2>
                        {sodu_tdps_contrib_diaban_chart}
                    </div>
                    <div id="tdps-diaban-contrib-chart-nim" style="display:none;"></div>
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="tdps-pkkh-contrib-chart-ds">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo PKKH (%)</h2>
                        {ds_tdps_contrib_pkkh_chart}
                    </div>
                    <div id="tdps-pkkh-contrib-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Lợi nhuận theo PKKH (%)</h2>
                        {ln_tdps_contrib_pkkh_chart}
                    </div>
                    <div id="tdps-pkkh-contrib-chart-sodu" style="display:none;">
                        <h2 style="text-align:center;">Tỷ trọng đóng góp Số dư theo PKKH (%)</h2>
                        {sodu_tdps_contrib_pkkh_chart}
                    </div>
                    <div id="tdps-pkkh-contrib-chart-nim" style="display:none;"></div>
                </div>
            </div>
        </div>
        </div>

        <div id="product-pshh" style="display:none;">

        <div class="kpi-row" id="pshh-kpi-ytd">{''.join(pshh_cards_ytd)}</div>
        <div class="kpi-row" id="pshh-kpi-daily" style="display:none;">{''.join(pshh_cards_daily)}</div>

        <div class="charts-panel" id="pshh-dim-charts">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onPshhChartMetricChange(this.value)">
                        <option value="ds_tlhh">Doanh Số TLHH</option>
                        <option value="ds_otc">Doanh Số OTC</option>
                        <option value="ln">Lợi Nhuận</option>
                    </select>
                </div>
                {build_nhom_select_html("pshh-nhom-select", nhom)}
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="pshh-diaban-chart-ds_tlhh">
                        <h2 style="text-align:center;">Doanh số TLHH phái sinh hàng hóa theo địa bàn</h2>
                        {ds_tlhh_pshh_diaban_chart}
                    </div>
                    <div id="pshh-diaban-chart-ds_otc" style="display:none;">
                        <h2 style="text-align:center;">Doanh số OTC phái sinh hàng hóa theo địa bàn</h2>
                        {ds_otc_pshh_diaban_chart}
                    </div>
                    <div id="pshh-diaban-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận phái sinh hàng hóa theo địa bàn</h2>
                        {ln_pshh_diaban_chart}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="pshh-pkkh-chart-ds_tlhh">
                        <h2 style="text-align:center;">Doanh số TLHH phái sinh hàng hóa theo PKKH</h2>
                        {ds_tlhh_pshh_pkkh_chart}
                    </div>
                    <div id="pshh-pkkh-chart-ds_otc" style="display:none;">
                        <h2 style="text-align:center;">Doanh số OTC phái sinh hàng hóa theo PKKH</h2>
                        {ds_otc_pshh_pkkh_chart}
                    </div>
                    <div id="pshh-pkkh-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận phái sinh hàng hóa theo PKKH</h2>
                        {ln_pshh_pkkh_chart}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="pshh-dim-charts-daily" style="display:none;">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onPshhDailyChartMetricChange(this.value)">
                        <option value="ds_tlhh">Doanh Số TLHH</option>
                        <option value="ds_otc">Doanh Số OTC</option>
                        <option value="ln">Lợi Nhuận</option>
                    </select>
                </div>
                {build_nhom_select_html("pshh-nhom-select-daily", nhom)}
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="pshh-diaban-chart-daily-ds_tlhh">
                        <h2 style="text-align:center;">Doanh số TLHH phái sinh hàng hóa theo địa bàn</h2>
                        {ds_tlhh_pshh_diaban_chart_daily}
                    </div>
                    <div id="pshh-diaban-chart-daily-ds_otc" style="display:none;">
                        <h2 style="text-align:center;">Doanh số OTC phái sinh hàng hóa theo địa bàn</h2>
                        {ds_otc_pshh_diaban_chart_daily}
                    </div>
                    <div id="pshh-diaban-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận phái sinh hàng hóa theo địa bàn</h2>
                        {ln_pshh_diaban_chart_daily}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="pshh-pkkh-chart-daily-ds_tlhh">
                        <h2 style="text-align:center;">Doanh số TLHH phái sinh hàng hóa theo PKKH</h2>
                        {ds_tlhh_pshh_pkkh_chart_daily}
                    </div>
                    <div id="pshh-pkkh-chart-daily-ds_otc" style="display:none;">
                        <h2 style="text-align:center;">Doanh số OTC phái sinh hàng hóa theo PKKH</h2>
                        {ds_otc_pshh_pkkh_chart_daily}
                    </div>
                    <div id="pshh-pkkh-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận phái sinh hàng hóa theo PKKH</h2>
                        {ln_pshh_pkkh_chart_daily}
                    </div>
                </div>
            </div>
        </div>
        </div>

        <div id="product-all" style="display:none;">
        <div class="kpi-row" id="all-kpi-ytd">{''.join(ds_all_cards)}</div>
        <div class="kpi-row" id="all-kpi-daily" style="display:none;">{''.join(ds_all_cards_daily)}</div>

        <div class="charts-panel" id="all-dim-charts">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onAllChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                    </select>
                </div>
                {build_nhom_select_html("all-nhom-select", nhom)}
                <div style="font-style:italic; font-size:12px; color:var(--primary); margin-left:auto;">*Không bao gồm Phái sinh hàng hóa (PSHH) — xem riêng ở tab Phái sinh hàng hóa</div>
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="all-diaban-chart-ds">
                        <h2 style="text-align:center;">Doanh số theo địa bàn</h2>
                        {ds_all_diaban_chart}
                    </div>
                    <div id="all-diaban-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận theo địa bàn</h2>
                        {ln_all_diaban_chart}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="all-pkkh-chart-ds">
                        <h2 style="text-align:center;">Doanh số theo PKKH</h2>
                        {ds_all_pkkh_chart}
                    </div>
                    <div id="all-pkkh-chart-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận theo PKKH</h2>
                        {ln_all_pkkh_chart}
                    </div>
                </div>
            </div>
        </div>

        <!-- Tỷ trọng đóng góp is always Doanh số, independent of the Chỉ tiêu toggle above
             (same convention as the Tổng quan tab's own contribution panels) — its own panel,
             not gated by the -ds/-ln divs, so it doesn't hide under Lợi Nhuận. Still follows
             Lũy kế/Trong ngày (onAllAggChange), same as all-dim-charts next to it. -->
        <div class="charts-panel" id="all-contrib-charts">
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo địa bàn (%)</h2>
                    {ds_contribution_diaban_chart}
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo PKKH (%)</h2>
                    {ds_contribution_pkkh_chart}
                </div>
            </div>
        </div>

        <div class="charts-panel" id="all-dim-charts-daily" style="display:none;">
            <div class="charts-toolbar">
                <div class="filter-group-compact">
                    <label class="filter-label">Chỉ tiêu</label>
                    <select class="filter-select" onchange="onAllDailyChartMetricChange(this.value)">
                        <option value="ds">Doanh Số</option>
                        <option value="ln">Lợi Nhuận</option>
                    </select>
                </div>
                {build_nhom_select_html("all-nhom-select-daily", nhom)}
                <div style="font-style:italic; font-size:12px; color:var(--primary); margin-left:auto;">*Không bao gồm Phái sinh hàng hóa (PSHH) — xem riêng ở tab Phái sinh hàng hóa</div>
            </div>
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="all-diaban-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số theo địa bàn</h2>
                        {ds_all_diaban_chart_daily}
                    </div>
                    <div id="all-diaban-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận theo địa bàn</h2>
                        {ln_all_diaban_chart_daily}
                    </div>
                </div>

                <div class="chart-card" style="flex:1; min-width:400px;">
                    <div id="all-pkkh-chart-daily-ds">
                        <h2 style="text-align:center;">Doanh số theo PKKH</h2>
                        {ds_all_pkkh_chart_daily}
                    </div>
                    <div id="all-pkkh-chart-daily-ln" style="display:none;">
                        <h2 style="text-align:center;">Lợi nhuận theo PKKH</h2>
                        {ln_all_pkkh_chart_daily}
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-panel" id="all-contrib-charts-daily" style="display:none;">
            <div style="display:flex; flex-wrap:wrap;">
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo địa bàn (%)</h2>
                    {ds_contribution_diaban_chart_daily}
                </div>
                <div class="chart-card" style="flex:1; min-width:400px;">
                    <h2 style="text-align:center;">Tỷ trọng đóng góp Doanh số theo PKKH (%)</h2>
                    {ds_contribution_pkkh_chart_daily}
                </div>
            </div>
        </div>

        </div>
    """

    tab_nhomphutrach = f"""
        <div id="kqkd-chinhanh">
        <div class="charts-panel">
            <div class="table-card">{cn_trong_diem_table}</div>
        </div>
        </div>

        <div id="kqkd-canbo" style="display:none;">
        <div class="charts-panel">
            <div class="table-card">{cn_canbo_table}</div>
        </div>
        </div>
    """

    tab_khachhang = f"""

        <div id="khachhang-mbnt">
        <div class="charts-panel">
            <div id="mbnt-tangtruong-wrap">
                <div id="mbnt-pct-sections">{''.join(mbnt_pct_sections)}</div>
                <div id="mbnt-abs-sections" style="display:none;">{''.join(mbnt_abs_sections)}</div>
            </div>
            <div id="mbnt-top10-wrap" style="display:none;">
                <div id="mbnt-ds-sections">{''.join(mbnt_ds_sections)}</div>
                <div id="mbnt-ln-sections">{''.join(mbnt_ln_sections)}</div>
                <div id="mbnt-ds-sections-daily" style="display:none;">{''.join(mbnt_ds_sections_daily)}</div>
                <div id="mbnt-ln-sections-daily" style="display:none;">{''.join(mbnt_ln_sections_daily)}</div>
            </div>
        </div>
        <div style="font-style:italic; font-size:12px; color:var(--primary); text-decoration:underline; margin-bottom:var(--section-gap);">*Bảng tính chỉ hiện thị những địa bàn và PKKH có phát sinh giao dịch</div>
        </div>

        <div id="khachhang-hdls" style="display:none;">
        <div class="charts-panel">
            <div id="hdls-tangtruong-wrap">
                <div id="hdls-pct-sections">{''.join(hdls_pct_sections)}</div>
                <div id="hdls-abs-sections" style="display:none;">{''.join(hdls_abs_sections)}</div>
            </div>
            <div id="hdls-top10-wrap" style="display:none;">
                <div id="hdls-ds-sections">{''.join(hdls_ds_sections)}</div>
                <div id="hdls-ln-sections">{''.join(hdls_ln_sections)}</div>
                <div id="hdls-ds-sections-daily" style="display:none;">{''.join(hdls_ds_sections_daily)}</div>
                <div id="hdls-ln-sections-daily" style="display:none;">{''.join(hdls_ln_sections_daily)}</div>
            </div>
        </div>
        <div style="font-style:italic; font-size:12px; color:var(--primary); text-decoration:underline; margin-bottom:var(--section-gap);">*Bảng tính chỉ hiện thị những địa bàn và PKKH có phát sinh giao dịch</div>
        </div>
    """

    return f"""
    <html{' class="export-mode"' if export_mode else ''}>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>PTKD Data — BIDV Global Markets</title>
        <style>{THEME_CSS}</style>
        <script>{theme_js}</script>
    </head>
    <body>
        <div class="app-shell">
            <nav class="sidebar" id="app-sidebar">
                <div class="sidebar-brand">
                    <img src="{LOGO_DATA_URI}" alt="BIDV Global Markets" class="sidebar-brand-logo" />
                </div>
                {nav_html}
            </nav>
            <div class="sidebar-backdrop" id="sidebar-backdrop" onclick="closeSidebar()"></div>
            <div class="main">
                <header class="topbar">
                    <div class="topbar-row">
                        <div style="display:flex; align-items:center;">
                            <button class="sidebar-toggle-btn" id="sidebar-toggle-btn" onclick="toggleSidebar()" aria-label="Menu">☰</button>
                            <h1 class="topbar-title" id="topbar-title">Tổng quan</h1>
                        </div>
                        <div class="topbar-actions">
                            <button class="toggle-btn" id="export-html-btn" onclick="exportHtml()" title="Lưu file HTML vào thư mục Gửi đi tài liệu">⬇ Xuất HTML</button>
                            <button class="toggle-btn" id="theme-toggle-btn" onclick="toggleTheme()">☀</button>
                        </div>
                    </div>
                    <div class="topbar-filters">
                        <div class="topbar-filter-group">
                            <label class="filter-label">Kỳ báo cáo</label>
                            <select class="filter-select" id="header-date-select" onchange="onDateChange(this.value)"{" disabled" if export_mode else ""}>
                                {date_options}
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-tq-loai-group" style="display:none;">
                            <label class="filter-label">Loại số liệu</label>
                            <select class="filter-select" id="tq-loai-select" onchange="onTqChartFilterChange()">
                                <option value="ytd">Lũy kế</option>
                                <option value="ngay">Trong ngày</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-nhom-group">
                            <label class="filter-label">Nhóm phụ trách</label>
                            <select class="filter-select" id="header-nhom-select" onchange="onHeaderNhomChange(this.value)">
                                <option value="Tất cả"{" selected" if nhom == "Tất cả" else ""}>Tất cả</option>
                                <option value="PTKD 1"{" selected" if nhom == "PTKD 1" else ""}>PTKD 1</option>
                                <option value="PTKD 2"{" selected" if nhom == "PTKD 2" else ""}>PTKD 2</option>
                                <option value="VPV"{" selected" if nhom == "VPV" else ""}>VPV</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-sanpham-group">
                            <label class="filter-label">Sản phẩm</label>
                            <select class="filter-select" id="header-sanpham-select" onchange="onHeaderSanPhamChange(this.value)">
                                <option value="all" id="sanpham-option-all">Tất cả</option>
                                <option value="mbnt">Mua bán ngoại tệ</option>
                                <option value="hdls">Hoán đổi lãi suất</option>
                                <option value="tdps" id="sanpham-option-tdps">Tín dụng phái sinh</option>
                                <option value="pshh" id="sanpham-option-pshh">Phái sinh hàng hóa</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-agg-group" style="display:none;">
                            <label class="filter-label">Loại số liệu</label>
                            <select class="filter-select" id="header-agg-select" onchange="onHeaderAggChange(this.value)">
                                <option value="ytd">Lũy kế</option>
                                <option value="ngay">Trong ngày</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-khtablemode-group" style="display:none;">
                            <label class="filter-label">Loại bảng</label>
                            <select class="filter-select" onchange="onKhachHangTableModeChange(this.value)">
                                <option value="tangtruong">Top 10 KH tăng trưởng</option>
                                <option value="top10">Top 10 KH</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-loaitangtruong-group" style="display:none;">
                            <label class="filter-label">Loại tăng trưởng</label>
                            <select class="filter-select" onchange="onKhachHangRankingChange(this.value)">
                                <option value="pct">Phần trăm</option>
                                <option value="abs">Tuyệt đối</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-khtop10-agg-group" style="display:none;">
                            <label class="filter-label">Loại số liệu</label>
                            <select class="filter-select" onchange="onKhachHangTop10AggChange(this.value)">
                                <option value="ytd">Lũy kế</option>
                                <option value="ngay">Trong ngày</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-export-excel-group" style="display:none; margin-left:auto;">
                            <button class="toggle-btn" id="export-excel-btn" onclick="exportExcelKhachHang()" title="Xuất đầy đủ dữ liệu MBNT/HĐLS ra Excel và lưu vào thư mục Gửi đi tài liệu">📊 Xuất Excel</button>
                        </div>
                        <div class="topbar-filter-group" id="header-kqkd-group" style="display:none;">
                            <label class="filter-label">Báo cáo</label>
                            <select class="filter-select" onchange="onHeaderKqkdChange(this.value)">
                                <option value="chinhanh">Chi nhánh trọng điểm</option>
                                <option value="canbo">Cán bộ</option>
                            </select>
                        </div>
                        <div class="topbar-filter-group" id="header-export-image-group" style="margin-left:auto;">
                            <button class="toggle-btn" id="export-image-btn" onclick="exportTongQuanImage()" title="Xuất Tổng quan sang JPEG và lưu vào thư mục Gửi đi JPEG">🖼 Xuất Tổng quan JPEG</button>
                        </div>
                    </div>
                </header>
                <div class="content">
                    <div id="tab-sanpham" class="tab-page">{tab_sanpham}</div>
                    <div id="tab-nhom_pt" class="tab-page" style="display:none;">{tab_nhom_pt}</div>
                    <div id="tab-nhomphutrach" class="tab-page" style="display:none;">{tab_nhomphutrach}</div>
                    <div id="tab-khachhang" class="tab-page" style="display:none;">{tab_khachhang}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

JPEG_EXPORT_DIR = r"\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC PTKD\Gửi đi JPEG"
HTML_EXPORT_DIR = r"\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC PTKD\Gửi đi tài liệu"


EXCEL_EXPORT_DIR = HTML_EXPORT_DIR  # same "Gửi đi tài liệu" share the manual BC chi tiết files already live in


@app.route("/export_excel_khachhang", methods=["POST"])
def export_excel_khachhang():
    """Full (untruncated) MBNT and HDLS customer-level rows for the selected date, one sheet
    each — the same two tables the Khách hàng tab's Top khách hàng rankings are built from,
    but every row/column rather than the top/bottom 5 per nhóm the UI shows."""
    if not os.path.isdir(EXCEL_EXPORT_DIR):
        return jsonify(status="error", message=f"Không truy cập được thư mục mạng: {EXCEL_EXPORT_DIR}"), 500

    date = request.args.get("date") or latest_date()
    mbnt_df = bao_cao_ket_qua_mbnt_2025_2026(date)
    hdls_df = bao_cao_ket_qua_hdls_2025_2026(date)

    # dd.mm.yyyy, matching the existing manual "BC chi tiết PTKD_11.08.2026.pdf" files already
    # saved in this folder, so the automated export sits alongside them under the same naming.
    date_label = pd.to_datetime(date).strftime("%d.%m.%Y")
    filename = f"BC chi tiết PTKD_{date_label}.xlsx"
    dest_path = os.path.join(EXCEL_EXPORT_DIR, filename)

    try:
        with pd.ExcelWriter(dest_path, engine="openpyxl") as writer:
            mbnt_df.to_excel(writer, sheet_name="MBNT", index=False)
            hdls_df.to_excel(writer, sheet_name="HDLS", index=False)
    except OSError as e:
        return jsonify(status="error", message=str(e)), 500

    return jsonify(status="ok", filename=filename, path=dest_path)


@app.route("/save_html_export", methods=["POST"])
def save_html_export():
    if not os.path.isdir(HTML_EXPORT_DIR):
        return jsonify(status="error", message=f"Không truy cập được thư mục mạng: {HTML_EXPORT_DIR}"), 500

    date = request.args.get("date") or latest_date()
    html_content = request.get_data(as_text=True)
    if not html_content:
        return jsonify(status="error", message="Không có nội dung HTML để lưu"), 400

    filename = f"PTKD_Dashboard_{date}.html"
    dest_path = os.path.join(HTML_EXPORT_DIR, filename)
    try:
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except OSError as e:
        return jsonify(status="error", message=str(e)), 500

    return jsonify(status="ok", filename=filename, path=dest_path)


def _find_msedge() -> str:
    patterns = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\*\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\*\msedge.exe",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    raise FileNotFoundError("msedge.exe not found under Program Files")


JPEG_EXPORT_DPI = 144  # 2x the PDF's native 72dpi — readable text without a huge file


def _trim_blank_bands(img: Image.Image, keep_rows: int = 24, min_run: int = 60):
    """Squeeze the vertical dead space out of a rendered page.

    Can't just crop top/bottom against a background colour: a page has several stacked bands
    (white print margin, then page background, then the content panel's own slightly
    different background), so no single colour identifies "blank", and the gap left when a
    panel gets pushed to the next page sits in the middle rather than at an edge.

    What blank space does look like is a long run of consecutive identical rows. So collapse
    any run longer than min_run down to keep_rows, leaving normal spacing (short runs)
    untouched. Returns None if nothing survives."""
    arr = np.asarray(img)
    n = arr.shape[0]
    if n < 2:
        return None

    row_repeats = np.all(arr[1:] == arr[:-1], axis=(1, 2))  # row i+1 identical to row i
    keep = np.ones(n, dtype=bool)
    start = 0
    while start < n:
        end = start
        while end + 1 < n and row_repeats[end]:
            end += 1
        run = end - start + 1
        if run > 1 and (start == 0 or end == n - 1):
            # A run touching a page edge is print margin / leftover space at a page break.
            # Drop it outright so consecutive pages butt together and the stitched image
            # reads as one continuous page instead of showing a seam.
            keep[start : end + 1] = False
        elif run > min_run:
            keep[start + keep_rows : end + 1] = False
        start = end + 1

    trimmed = arr[keep]
    if trimmed.shape[0] < 2:
        return None
    return Image.fromarray(trimmed)


def _pdf_to_image(pdf_path: str) -> Image.Image:
    """Rasterise every page of a print-to-PDF render and stack them into one tall image.
    The PDF paginates the full page, so this captures content that scrolled past the
    viewport — the thing a plain --screenshot missed."""
    zoom = JPEG_EXPORT_DPI / 72
    matrix = pymupdf.Matrix(zoom, zoom)
    with pymupdf.open(pdf_path) as doc:
        pages = []
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            trimmed = _trim_blank_bands(img)
            if trimmed is not None:
                pages.append(trimmed)

    if not pages:
        raise ValueError("PDF render produced no content")
    if len(pages) == 1:
        return pages[0]

    width = max(p.width for p in pages)
    stitched = Image.new("RGB", (width, sum(p.height for p in pages)), "white")
    y = 0
    for p in pages:
        stitched.paste(p, (0, y))
        y += p.height
    return stitched


@app.route("/export_image", methods=["POST"])
def export_image():
    if not os.path.isdir(JPEG_EXPORT_DIR):
        return jsonify(status="error", message=f"Không truy cập được thư mục mạng: {JPEG_EXPORT_DIR}"), 500

    date = request.form.get("date") or latest_date()
    nhom = request.form.get("nhom", "PTKD 1")

    tmp_dir = tempfile.gettempdir()
    tag = f"tongquan_{os.getpid()}_{abs(hash((date, nhom)))}"
    tmp_html = os.path.join(tmp_dir, f"_export_{tag}.html")
    tmp_pdf = os.path.join(tmp_dir, f"_export_{tag}.pdf")

    try:
        with app.test_client() as client:
            resp = client.get(f"/?date={quote(date)}&nhom={quote(nhom)}&tab=sanpham&export_img=1")
            if resp.status_code != 200:
                return jsonify(status="error", message=f"Không render được trang (HTTP {resp.status_code})"), 500
            html_content = resp.get_data(as_text=True)

        with open(tmp_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Print to PDF rather than --screenshot: a screenshot only captures the viewport, so
        # any content past it was silently cut off. Printing paginates the full page, and the
        # pages are then rasterised and stitched back into one tall JPEG below.
        msedge = _find_msedge()
        file_url = "file:///" + tmp_html.replace(os.sep, "/")
        subprocess.run(
            [msedge, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={tmp_pdf}", file_url],
            check=True, timeout=60, capture_output=True,
        )

        img = _pdf_to_image(tmp_pdf)
        bg_color = img.getpixel((img.width - 1, img.height - 1))
        bg = Image.new("RGB", img.size, bg_color)
        bbox = ImageChops.difference(img, bg).getbbox()
        if bbox:
            pad = 20
            img = img.crop((
                max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(img.width, bbox[2] + pad), min(img.height, bbox[3] + pad),
            ))

        filename = f"PTKD_TongQuan_{date}.jpg"
        dest_path = os.path.join(JPEG_EXPORT_DIR, filename)
        img.save(dest_path, "JPEG", quality=92)

        return jsonify(status="ok", filename=filename, path=dest_path)
    except subprocess.TimeoutExpired:
        return jsonify(status="error", message="Xuất ảnh quá thời gian chờ (msedge treo)"), 500
    except subprocess.CalledProcessError as e:
        return jsonify(status="error", message=f"msedge lỗi: {e.stderr.decode(errors='replace')[:300]}"), 500
    except Exception as e:
        return jsonify(status="error", message=str(e)), 500
    finally:
        for p in (tmp_html, tmp_pdf):
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
