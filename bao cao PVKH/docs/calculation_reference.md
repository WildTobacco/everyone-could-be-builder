# PVKH Dashboard — Calculation Reference

*Generated 2026-08-24 by reading the live codebase at `C:\Users\hieupg\Downloads\Python HTML Project\`. Reflects the code as of that date — the file is under active concurrent editing by another process, so re-verify against current source before relying on any single line/function name long after this date.*

This document covers every visualization on all four tabs — **Tổng quan**, **Nhóm phụ trách**, **Kết quả chi nhánh/cán bộ**, **Khách hàng** — with its data source, formula, and (per your request) explicit flags for two recurring questions:

- **Chia sẻ** — does the figure subtract MBNT's monthly profit-sharing deduction (`bronze_baocaotudong.pvkh_chiase`)?
- **Kho bạc / KBNN** (State Treasury, cif `9448630`, bds `160`, `bdscif = "1609448630"`) — is this client excluded from the figure?

Jump to the two summary matrices at the bottom if you just need the yes/no answers.

---

## 0. Conventions used throughout the codebase

**2025 vs 2026 sourcing.** Every metric with a year-over-year comparison follows the same split:
- **2026 (`y_*` files)** reads `silver_pvkh_DL_KH_luy_ke` (or another table that already stores true daily-cumulative values) directly — a `MAX`-per-`bdscif` dedup, or a straight sum, for the selected date. No approximation involved.
- **2025 baseline (`y1_*` files)** approximates a same-day-last-year YTD figure from `pvkh_fx`/`pvkh_pstc`/`pvkh_pshh`, which only store **monthly** snapshots: **Full + Partial × ProrationRatio** — every month strictly before the reference month is summed in full, the reference month itself is summed and scaled by `day_of_month / days_in_month`. This is a literal port of the original Power BI DAX (`FirstDayLastYear`/`ProrationRatio` variables), not a simplification — replicating it exactly (including the last-day-of-month edge case for chia sẻ's window) is what makes the numbers match Power BI.

**dia_ban vs PKKH won't reconcile.** `dia_ban` comes from `listbds()` via `bds`; `pkkh` comes from `pvkh_listcif → pvkh_pkkh` via `cif`. A customer with a NULL `cif` has a dia_ban bucket but no PKKH bucket, so the two breakdowns of the same measure sum to different totals. This is confirmed-and-accepted, not a bug.

**Vietnamese terms**: Doanh số = revenue/turnover volume, Lợi nhuận = profit, NIM = net interest margin (here used more generally as a profit/volume ratio), Số dư = balance, HT = hoàn thành (completion %), KH/KHKD = kế hoạch (plan/target), Lũy kế = YTD cumulative, Trong ngày = single day's movement, Nhóm phụ trách = PTKD1/PTKD2/VPV (the three business groups), địa bàn = region, PKKH = customer-segment code, so với cùng kỳ = year-over-year comparison, tr = triệu (million), bn = billion.

---

## 1. Tổng quan tab (`tab_sanpham`, `web_app.py`)

Top-level snapshot: 4 product scorecards (MBNT, HĐLS, TDPS, PSHH), a Sản phẩm/Chỉ tiêu-filtered dia_ban+PKKH chart pair, and doanh-số contribution-% donuts.

### 1.1 Scorecards (`build_kpi_row_by_sanpham`)

| Card | Doanh số | Lợi nhuận | Extra |
|---|---|---|---|
| **Mua bán ngoại tệ (MBNT)** | `tong_ds_mbnt_ytd_by_nhom(date)["TOTAL"]` — `MAX(pvkh_mbnt_nhom_phu_trach[sum_ds_mbnt_luy_ke_den_ngay_bc])`, TOTAL = PTKD1+PTKD2+VPV | `tong_ln_mbnt_ytd_by_nhom(date)["TOTAL"]` — same table's `sum_ln_mbnt_luy_ke_den_ngay_bc`, pre-aggregated bronze column (see §5 caveat) | NIM 2026/2025 badges: `y_/y1_nim_mbnt_nhom_diaban_pkkh(...)["TOTAL"]` |
| **Hoán đổi lãi suất (HĐLS)** | `tong_ds_hdls_ytd_by_nhom(date)["TOTAL"]` — `MAX(pvkh_pstc_nhom_phu_trach[sum_ds_hdls_luy_ke])` | `tong_ln_hdls_ytd_by_nhom(date)["TOTAL"]` — same table's `sum_ln_hdls_luy_ke` | NIM: `nim_hdls_binh_quan_by_nhom["TOTAL"]`; Số dư B/Q CCS + IRS |
| **Tín dụng phái sinh (TDPS)** | `ds_tdps_luy_ke_by_nhom(date)["TOTAL"]` — `SUM(pvkh_dsdaily_temp[doanhsotdps])`, 1/1→date (not the pre-aggregated `pvkh_pstc` column, which is empty for TDPS) | `ln_tdps_luy_ke_by_nhom(date)["TOTAL"]` — `MAX(pvkh_pstc_nhom_phu_trach[sum_ln_tdps_luy_ke])` | NIM + Số dư B/Q TDPS |
| **Phái sinh hàng hóa (PSHH)** | DS TLHH (lots) = `SUM(pvkh_dsdaily_temp[doanhsotlhh])`; DS OTC (USD) = `SUM(pvkh_dsdaily_temp[doanhsootc])`, kept separate — different units | `SUM(pvkh_dailyreport[ln_pshh_theo_mpa_ytd])` | — |

2025 baselines for all four: Full+Partial proration over `pvkh_fx`/`pvkh_pstc`/`pvkh_pshh`'s monthly `doanhso`/`loinhuan` columns, filtered by `sanpham`.

**Reading the sub-metrics** (TOTAL only on this tab — no per-nhóm breakdown, and no Trong ngày toggle; every figure below is lũy kế):

- **So với cùng kỳ (%)** — year-over-year comparison, shown as a colored `+X.X%`/`−X.X%` chip under the big number: `(Actual_2026 − Baseline_2025) / Baseline_2025 × 100` (`web_app.py:1725-1726`, `_pct_html`). `Baseline_2025` is the same-day-last-year approximation described in §0 (Full+Partial×ProrationRatio). Not shown for PSHH's OTC/TLHH split (no `_pct_html` call in that card path) — only the DS TLHH/OTC and LN lines carry their own so-với-cùng-kỳ chip individually.
- **HT tháng (%)** — "hoàn thành tháng", a pace bar: `Actual_YTD_2026 / KH_lũy_kế_đến_tháng_này × 100`. The plan figure is **not** that single month's own target — `ke_hoach_*_thang(month)` is itself a cumulative-through-month plan (the KHKD source column stores it that way), so this is "YTD actual vs YTD plan-to-date". Colored "behind" if the % is under how far the calendar month has elapsed (`ngày_trong_tháng / số_ngày_trong_tháng × 100`) — a pacing signal, not part of the number itself.
- **HT năm (%)** — same idea against the full annual plan: `Actual_YTD_2026 / KH_năm_2026 × 100`, colored "behind" if under `ngày_trong_năm / 365(6) × 100`.
- **NIM** — a profit-to-volume ratio, formula differs by product (see §1.2's NIM column for the exact numerator/denominator and their chia-sẻ/KBNN treatment): MBNT's is `LN(sau chia sẻ) ÷ DS(ex-KBNN)` at TOTAL scope; HĐLS's and TDPS's are balance-weighted (`LN × 365 × 100 ÷ (Số dư bình quân × tỷ giá)`, i.e. an annualized margin against average outstanding balance rather than a same-period DS ratio — see §2.2/§2.3). MBNT shows both "NIM 2026" and "NIM 2025"; HĐLS/TDPS show 2026 only (no reliable 2025 balance/rate history to compare against).
- **Số dư** ("Số dư B/Q CCS/IRS" for HĐLS, "Số dư B/Q TDPS" for TDPS) — outstanding balance, YTD daily average ("bình quân năm"), read directly off `pvkh_pstc_nhom_phu_trach`. No so-với-cùng-kỳ or HT for Số dư — there's no balance line in the KHKD plan and no reliable 2025 balance history. MBNT has no Số dư metric at all (FX doesn't carry an outstanding-balance concept the way a swap/derivative does).

### 1.2 Sản phẩm/Chỉ tiêu filtered dia_ban + PKKH chart pair

12 pre-baked divs per dimension (3 sản phẩm × up to 4 chỉ tiêu: Doanh Số/Lợi Nhuận/NIM/Số Dư — MBNT has no Số Dư), toggled client-side, all `pool_nhom=True` (summed/recomputed across every nhóm, since Tổng quan has no nhóm selector).

| Sản phẩm | Doanh số | Lợi nhuận | NIM | Số dư |
|---|---|---|---|---|
| MBNT | `y_/y1_ds_mbnt_by_nhom_diaban/pkkh` — dedup-max per bdscif, **excludes KBNN** | `y_/y1_ln_mbnt_by_nhom_diaban/pkkh` — **subtracts chia sẻ**, no KBNN filter | `y_nim_diaban/pkkh_pooled` — Σ LN(sau chia sẻ) ÷ Σ DS(ex-KBNN), **asymmetric base** | n/a |
| HĐLS | `y_/y1_ds_hdls_irs_ccs_by_nhom_diaban/pkkh` (IRS+CCS stacked) — **excludes KBNN** | `y_/y1_ln_hdls_by_nhom_diaban/pkkh` — no chia sẻ (product-wide), no KBNN | `nim_hdls_diaban/pkkh_pooled`, 2026-only | `so_du_hdls_diaban/pkkh_chart_luy_ke` (CCS+IRS bình quân năm) |
| TDPS | `y_/y1_ds_tdps_by_nhom_diaban/pkkh` — no KBNN filter | `y_/y1_ln_tdps_by_nhom_diaban/pkkh` — no chia sẻ, no KBNN | `nim_tdps_diaban/pkkh_pooled`, 2026-only | `so_du_tdps_diaban/pkkh_chart_luy_ke` (bình quân năm) |

PKKH variants additionally drop a slice set: `PKKH_EXCLUDED_MBNT = {"KH ao","KHACH HANG KHAC"}` for MBNT, the full `PKKH_EXCLUDED = {"KH ao","KH vang lai","KHCN","KHACH HANG KHAC"}` for HĐLS/TDPS — a UI slice filter, unrelated to KBNN.

### 1.3 "Tỷ trọng đóng góp doanh số" contribution donuts

`_build_contribution_chart(df, dim_col, value_col)` — 2026-only, `pct = groupby(dim)[value].sum() / total × 100`, rendered as a donut sorted descending. Doanh số only (no Lợi nhuận version exists, so the chia-sẻ question doesn't apply). MBNT and HĐLS variants inherit KBNN exclusion from their underlying `y_ds_*_by_nhom_diaban/pkkh` source; TDPS's does not (its source has no KBNN filter).

---

## 2. Nhóm phụ trách tab (`tab_nhom_pt`, `web_app.py`)

Per-product deep-dive: MBNT / HĐLS / TDPS / Tất cả (combined), each with Lũy kế and Trong ngày views. Same 4 cards as Tổng quan (PTKD 1, PTKD 2, VPV, TOTAL), but here they're **per-nhóm**, not TOTAL-only, and each product has a **Trong ngày** counterpart with a different (simpler) pace metric.

**Reading the sub-metrics — lũy kế cards** (identical definitions to §1.1, now per-nhóm as well as TOTAL):

- **So với cùng kỳ (%)** — `(Actual_2026 − Baseline_2025) / Baseline_2025 × 100`, one value per PTKD1/PTKD2/VPV/TOTAL.
- **HT tháng (%)** / **HT năm (%)** — same YTD-actual-vs-YTD-plan-to-date / vs-annual-plan formulas as §1.1, per nhóm. Pace bar "behind" threshold is the same elapsed-calendar-time check.
- **"So với KH LK tháng" (forecast badge)** — a sub-metric that does **not** exist on Tổng quan. Rendered by `_forecast_badge_row()` under the HT tháng/HT năm bars: extrapolates `Forecast_end_of_month = YTD_actual ÷ working_days_elapsed × working_days_in_month` (`mbnt_forecast_end_of_month.py` and its HĐLS/TDPS siblings), then shows the gap (`▲`/`▼` + absolute difference) against `KH_tháng` (that month's cumulative plan). Answers "if the rest of the month keeps pace with what's happened so far, will we hit this month's target?" — as opposed to HT tháng, which only says where YTD actual stands *today* relative to the plan-to-date. When a product has no KH to compare (TDPS's Doanh số has no KHKD plan line at all), the forecasted figure still shows but with no gap.
- **NIM / Số dư** — same formulas as §1.1's NIM/Số dư, but broken out per nhóm as well as TOTAL: MBNT's NIM lũy kế panel is a clustered bar (2026 vs 2025) per nhóm; HĐLS/TDPS's NIM and Số dư are single-series bars/donuts per nhóm (see §2.2/§2.3 tables for the exact source columns).

**Reading the sub-metrics — trong ngày cards** (a different, simpler metric set — see `_daily_paces_block`, `web_app.py:1500`):

- **No so-với-cùng-kỳ.** A single day's movement has no meaningful "same day last year" comparison in this dashboard (no daily-granularity 2025 source), so the chip is simply absent on Trong ngày cards.
- **"HT so với KH/ngày" replaces HT tháng/HT năm** — one pace bar, not two: `DS_current_day / (KH_tháng ÷ working_days_in_month_YTD) × 100`, i.e. today's actual against a flat daily slice of this month's plan (`_ds_current_and_kh_per_day`, `hoanthanh_kh_ds_mbnt.py`). The row also shows the absolute gap (`▲`/`▼` + value) against that same daily target, via `hoanthanh_kh_ds_mbnt()`.
- **No forecast badge** on Trong ngày cards (that's a lũy kế-only concept — extrapolating a single day forward doesn't make sense).
- **NIM/Số dư panels** switch to their own "ngày" variant (that day's own snapshot / differenced figure) via the same lũy kế↔ngày toggle described in §2.1-§2.3's tables, rather than anything on the scorecard itself.

### 2.1 MBNT section

| Visualization | Type | Source | Formula | Chia sẻ | KBNN |
|---|---|---|---|---|---|
| Scorecard DS/LN lũy kế (4 cards) | KPI cards | `pvkh_mbnt_nhom_phu_trach[sum_ds/ln_mbnt_luy_ke_den_ngay_bc]` | `MAX` per nhóm | LN: pre-aggregated bronze column — netting (if any) happens upstream in SQL, not visible here (see §5) | not excluded |
| Scorecard DS/LN trong ngày | KPI cards | `pvkh_mbnt_nhom_phu_trach[sum_ds/ln_mbnt_ngay_bao_cao]` | `MAX` per nhóm | **Gross** — straight column read, no subtraction | not excluded |
| NIM lũy kế panel | Clustered bar (2026 vs 2025) | `y_/y1_nim_mbnt_nhom_diaban_pkkh` | LN(sau chia sẻ) ÷ DS(ex-KBNN) | **Subtracted** | **DS leg only** |
| NIM Spot Mua/Bán, NIM trong ngày | Clustered bar / single bar | `pvkh_mbnt_nhom_phu_trach[nim_mbnt_buy/sell_spot_ngay_bc]`, `[nim_mbnt_ngay_bc]` | Pre-computed ratio columns, straight read | n/a (no Python math) | not excluded |
| DS/LN/NIM theo địa bàn — lũy kế | Clustered bar (+ KHKD dashed target on LN) | `y_/y1_ds/ln/nim_mbnt_by_nhom_diaban` | DS: dedup-max, **KBNN excluded**. LN: `LNtrướcChiaSẻ − LNChiaSẻ`, **no KBNN filter**. NIM: ratio of the two. | LN & NIM: **subtracted** | DS & NIM-denominator: **excluded**; LN: not |
| DS/LN/NIM theo PKKH — lũy kế | same, grouped by PKKH | same functions, `_pkkh` variant | same as above | same as above | same as above, plus `PKKH_EXCLUDED_MBNT` slice drop |
| DS/LN/NIM theo địa bàn/PKKH — trong ngày | Single-series bar (can go negative) | `daily_diaban_pkkh.py`: `cumulative(date) − cumulative(prev trading day)` | LN differences `_ln_mbnt_truoc_chiase` (gross, no bdscif filter); DS differences the KBNN-excluded cumulative | **Deliberately gross** — see explanation below | DS: excluded (inherited); LN: not |

**Why trong-ngày LN is deliberately gross of chia sẻ**: chia sẻ is a *monthly* deduction applied on a window that jumps forward only on the last calendar day of the month. Differencing the sau-chia-sẻ cumulative would dump an entire month's chia sẻ into the month-end day's "daily" number — measured example: 31/07/2026 PTKD2/HN showed 1.07bn against ~4.82bn of real trading, a 3.75bn distortion. The daily series is documented to sum to LN *trước* chia sẻ over a month, not to the lũy kế (net) total — that gap is intentional. This is stated on-screen too: the panel footnote reads *"Lợi nhuận và NIM lũy kế đã trừ chia sẻ"* vs *"...trong ngày chưa trừ chia sẻ"*.

### 2.2 HĐLS section

| Visualization | Type | Source | Chia sẻ | KBNN |
|---|---|---|---|---|
| Scorecard DS/LN (lũy kế + trong ngày) | KPI cards | `pvkh_pstc_nhom_phu_trach[sum_ds/ln_hdls_luy_ke]` / `[..._ngay_bc]` | n/a (HĐLS has no chia sẻ concept anywhere) | not excluded |
| Số dư panel (donut, bình quân/ngày × Tất cả/CCS/IRS) | Donut per nhóm | `pvkh_pstc_nhom_phu_trach[so_du_ccs/irs_binh_quan]`, `[sum_so_du_ccs/irs_ngay_bc]` | n/a | n/a (nhóm-level, not customer-level) |
| NIM panel (bình quân/ngày) | Single-series bar | `nim_hdls_binh_quan_nhom.py` / `nim_hdls_ngay_nhom.py` — `LN×365×100 / (Σ so_du × rate)` | n/a | not excluded |
| DS theo địa bàn/PKKH — lũy kế | **Stacked**-clustered bar (IRS+CCS) | `y_/y1_ds_hdls_irs_ccs_by_nhom_diaban/pkkh` | n/a | **Excluded** |
| LN theo địa bàn/PKKH — lũy kế | Clustered bar + KHKD target | `y_/y1_ln_hdls_by_nhom_diaban/pkkh` | **No deduction** (explicit docstring: "no chiase deduction on this measure, unlike the MBNT LN one") | not excluded |
| NIM theo địa bàn/PKKH — lũy kế | Single-series bar, 2026-only | `nim_hdls_diaban/pkkh_pooled` | n/a | not excluded |
| Số dư theo địa bàn/PKKH — bình quân năm | Single-series bar | `so_du_hdls_luy_ke_by_nhom_diaban/pkkh` (CCS+IRS, `pvkh_dailyreport`) | n/a | not excluded |
| All of the above — trong ngày | Single-series bar (DS stacked) | day-over-day diff, same mechanism as MBNT | n/a | inherits lũy kế source's exclusion |

### 2.3 TDPS section

| Visualization | Type | Source | Chia sẻ | KBNN |
|---|---|---|---|---|
| Scorecard DS/LN (lũy kế + trong ngày) | KPI cards | DS: `pvkh_dsdaily_temp[doanhsotdps]` summed; LN: `pvkh_pstc_nhom_phu_trach[sum_ln_tdps_luy_ke]` | n/a | not excluded |
| Số dư panel (donut) | Donut per nhóm | `pvkh_pstc_nhom_phu_trach[so_du_tdps_binh_quan]` / ngày column | n/a | n/a |
| NIM panel (bình quân/ngày) | Single-series bar | `nim_tdps_binh_quan_nhom.py` / `nim_tdps_ngay_nhom.py` | n/a | not excluded |
| DS/LN theo địa bàn/PKKH — lũy kế | Clustered bar (+ KHKD target on LN) | `y_/y1_ds/ln_tdps_by_nhom_diaban/pkkh` | **"No chia sẻ deduction (that is MBNT-only) and no bdscif exclusion, matching the HĐLS LN measure"** (explicit docstring) | not excluded |
| NIM theo địa bàn/PKKH — lũy kế | Single-series bar, 2026-only | `nim_tdps_diaban/pkkh_pooled` | n/a | not excluded |
| Số dư theo địa bàn/PKKH — bình quân năm | Single-series bar | `so_du_tdps_luy_ke_by_nhom_diaban/pkkh` (`pvkh_dailyreport`) | n/a | not excluded |
| DS trong ngày | Single-series bar | `pvkh_dsdaily_temp` is already daily — **read directly, not differenced** | n/a | not excluded |
| LN/NIM trong ngày | Single-series bar | day-over-day diff | n/a | not excluded |

### 2.4 "Tất cả" (combined) section

- **Doanh số = MBNT + HĐLS** (TDPS has no doanh số figure of its own). **Lợi nhuận = MBNT + HĐLS + TDPS.**
- Combined so-với-cùng-kỳ % is computed on the *summed* actual/baseline totals, not an average of the three products' own percentages.
- The combined figures inherit each product's own chia-sẻ/KBNN treatment described above — i.e. the combined LN is "MBNT (sau chia sẻ) + HĐLS (gross, n/a) + TDPS (gross, n/a)", and combined DS is "MBNT (ex-KBNN) + HĐLS (ex-KBNN)".
- Also has DS/LN theo địa bàn/PKKH combined charts and doanh-số contribution-% donuts (`build_ds_contribution_diaban/pkkh_chart`), same `_build_contribution_chart`, MBNT+HĐLS combined, 2026-only.

### 2.5 Completion % (Hoàn thành kế hoạch) and plan source

All `HT tháng`/`HT năm` badges = `actual / kế_hoạch × 100`, plan from `excel_connect.ke_hoach_theo_ptkd()` reading `KHKD PTKD 2026.xlsx` (network share), filtered by `san_pham` ∈ {DS MBNT, DS HDLS, DS PSHH, LN MBNT, LN HDLS, LN TDPS, LN PSHH, LN KDNT&PS} and `nhom_phu_trach`. Forecast-end-of-month badges (`*_forecast_end_of_month.py`) extrapolate `YTD ÷ working_days_passed × working_days_to_month_end`, compared against the same plan.

---

## 3. Kết quả chi nhánh/cán bộ tab (`tab_nhomphutrach`)

Two tables: **Chi nhánh** (branch-level, `cn_trong_diem_scorecard.py`) and **Cán bộ** (staff-level, `cn_canbo_scorecard.py`). This is the **only** place in the dashboard with an explicit "kho bạc"/KBNN deduction.

### 3.1 Chi nhánh (branch) table

| Column | Source | Formula |
|---|---|---|
| STT | derived | Dense rank of `% năm` within nhóm; global rank when "Tất cả" selected |
| Chi nhánh, Cán bộ phụ trách | `CN_trong_diem()` (`DS CN trọng điểm 2026.xlsx`) | passthrough |
| KH KDNT&PS 2026 | `khkd_cn_ht()` → `KHKD KDNT&PS 2026`, summed per BDS | — |
| KQ MBNT / HĐLS / TDPS / PSHH / KDNT&PS | `pvkh_kq_chinhanh[sum_ln_*_luy_ke]`, filtered to selected date, /1,000,000 | — |
| % tháng | derived | `KQ KDNT&PS ÷ KH_T1–T6` (hardcoded month range, not derived from selected date) |
| % năm | derived | `KQ KDNT&PS ÷ KH KDNT&PS 2026` |

**No KBNN exclusion anywhere in this file** — confirmed by full-file grep. Branch-level figures, including for the branch that owns KBNN's account, are shown raw. No `_ko_KBNN` variant, no `LoiNhuan_KBNN()` call.

### 3.2 Cán bộ (staff) table — the KBNN deduction lives here

Constants: `KBNN_BDS = 160`, `KBNN_ANNUAL_DEDUCTION = 110,000` (triệu đồng — a literal ported DAX constant, not derived), `KBNN_T7_DEDUCTION = 110,000/100×57 ≈ 62,700` (also a literal port — the "57" isn't independently derivable from the code, it's a hardcoded business constant from the original DAX). `LoiNhuan_KBNN()` is a **live** query: `SELECT SUM(loinhuanchiase) FROM pvkh_chiase WHERE cif=9448630 AND bds=160 AND year=2026` — this is the actual profit deduction subtracted from the columns below (the two constants above are only used for the plan-side, KH, deductions).

| Column | Uses `_ko_KBNN`? | Formula |
|---|---|---|
| KH KDNT&PS 2026 | **Yes** | `KH_KDNTPS_2026_CB − (is_bds_160 × 110,000)` |
| KQ MBNT | **Yes** | `(sum_ln_mbnt_luy_ke_den_ngay_bc − is_bds_160 × LoiNhuan_KBNN()) / 1,000,000` |
| KQ HĐLS | No | raw, `/1,000,000` |
| KQ TDPS | No | raw, `/1,000,000` |
| KQ PSHH | No | raw, `/1,000,000` |
| KQ KDNT&PS | **Yes** | `(sum_ln_kdntps_luy_ke − is_bds_160 × LoiNhuan_KBNN()) / 1,000,000` |
| % tháng | **Yes** | `KQ_KDNTPS_ko_KBNN ÷ KH_T1–T7_ko_KBNN` |
| % năm | **Yes** | `KQ_KDNTPS_ko_KBNN ÷ KH_2026_ko_KBNN` |

So exactly **five** displayed figures net out KBNN for whichever staff member currently owns bds 160 (attribution can shift day to day per the KHKD roster): `KH KDNT&PS 2026`, `KQ MBNT`, `KQ KDNT&PS`, `% tháng`, `% năm`. `KQ HĐLS`/`KQ TDPS`/`KQ PSHH` are shown raw — makes sense, since KBNN's chia-sẻ/plan deduction is scoped to KDNT&PS/MBNT specifically.

Ranking: `STT` = dense rank of `% năm (ko KBNN)` within nhóm (global when "Tất cả"). `Thay đổi` = today's rank vs. yesterday's rank using yesterday's %-completion (staff with no row a day back default to 0%, not excluded), formatted as ▲/▼/—.

**Open question flagged by the research**: this table's `KQ MBNT` reads `pvkh_kq_chinhanh[sum_ln_mbnt_luy_ke_den_ngay_bc]` — a **third, separate** bronze table from the one the Nhóm phụ trách/Tổng quan MBNT LN figures use (`pvkh_mbnt_nhom_phu_trach`) and from the one the dia_ban/PKKH charts use (`silver_pvkh_dl_kh_luy_ke`, which the code explicitly nets against `pvkh_chiase`). Nothing in `cn_trong_diem_scorecard.py`/`cn_canbo_scorecard.py` calls `pvkh_chiase()` for a general chia-sẻ subtraction (only the KBNN-specific one above). **Whether `pvkh_kq_chinhanh`'s MBNT column is gross or net of chia sẻ upstream cannot be determined from this codebase** — worth confirming with whoever owns that table's ETL, since every other MBNT LN figure on the dashboard is explicit about this and this one isn't.

---

## 4. Khách hàng tab (`tab_khachhang`)

Top-10 customer rankings, MBNT and HĐLS sections, each with 4 panels (tăng trưởng %, tăng trưởng tuyệt đối, top DS, top LN) × up to 4 nhóm cards.

**Important scope note**: none of this tab's growth/ranking math is implemented in this Python codebase. The four `calculations/top_kh_*.py` files only **rank and filter** columns that arrive pre-computed from a Postgres view (`bao_cao_ket_qua_mbnt_2025_2026_view` / `..._hdls_...`), exported to a static CSV (`data/bao_cao_ket_qua_mbnt_2025_2026.csv`, frozen as of 2026-08-17 17:43, not live-refreshed). The actual delta/percentage formula, and whether it nets chia sẻ, lives only in that Postgres view's definition — not visible here.

| Panel | Function | Ranked on | Threshold |
|---|---|---|---|
| Top tăng trưởng % | `top_kh_mbnt/hdls_tang_truong.get_top_bottom_by_group` | `▲LN%` (positive-only for Top, all for Bottom) | LN 2025 > 2000tr (MBNT) / 500tr (HĐLS) |
| Top tăng trưởng tuyệt đối | `..._by_group_abs` | `▲LN` (tr VND) | none |
| Top doanh số | `top_kh_*_by_value.get_top_bottom_by_group_ds` | `DS 2026 (tr USD)` | none, top-only |
| Top lợi nhuận | `..._by_group_ln` | `LN 2026 (tr VND)` | none, top-only |

**Chia sẻ**: not referenced anywhere in these four files or in how `db_connect.py` loads these two tables — no subtraction happens in this repo's code for this tab.

**Kho bạc/KBNN**: **no exclusion code anywhere** in this pipeline (confirmed by full-file search for "KBNN"/"kho bac"/"9448630"/"bds==160"). The text "kho bạc" that shows up in the source CSVs is literally a customer row: `ten_khach_hang = "KHO BAC NHA NUOC"`, `cif=9448630`, `bds=160`. For MBNT it has real, large activity (e.g. LN 2026 ≈ 53.6bn, comfortably above the 2000tr threshold) and **is fully included** in the rankings on equal footing with every other customer — it isn't filtered out anywhere. For HĐLS it happens to show 0 balance/profit in the sampled data, so it simply doesn't rank — that's a data fact, not an exclusion rule.

---

## 5. Summary — Chia sẻ (MBNT profit-sharing) treatment, dashboard-wide

| Figure | Subtracts chia sẻ? |
|---|---|
| Tổng quan / Nhóm phụ trách MBNT scorecard **Lợi nhuận** (lũy kế) — `tong_ln_mbnt_ytd_by_nhom` | **Unclear from Python** — reads pre-aggregated bronze `pvkh_mbnt_nhom_phu_trach.sum_ln_mbnt_luy_ke_den_ngay_bc` directly; any netting would happen upstream in SQL, not in this repo |
| Same scorecard, Trong ngày view — `ln_mbnt_ngay_by_nhom` | **No — gross**, straight column read |
| MBNT NIM (scorecard, lũy kế, dia_ban/PKKH — all `y_/y1_nim_mbnt_...`) | **Yes**, explicit subtraction of `pvkh_chiase` in the LN leg |
| MBNT dia_ban/PKKH **Lợi nhuận** chart, lũy kế (`y_/y1_ln_mbnt_by_nhom_diaban/pkkh`) | **Yes**, explicit (`TotalLNsauChiaSe = TotalLNtruocChiaSe − LNChiaSe`) |
| MBNT dia_ban/PKKH Lợi nhuận/NIM, Trong ngày (`daily_diaban_pkkh.py`) | **No — deliberately gross** (see §2.1 explanation; differencing the net cumulative would dump a month's chia sẻ into the last day) |
| Kết quả chi nhánh/cán bộ, **KQ MBNT** (branch and staff tables) | **Unclear from Python** — third source table (`pvkh_kq_chinhanh`), no `pvkh_chiase` call in either scorecard file (flagged as open question in §3.2) |
| Khách hàng tab, MBNT LN figures | **Unclear from Python** — arrives pre-computed from a Postgres view not present in this codebase |
| HĐLS — any Lợi nhuận/NIM figure, anywhere | **N/A** — chia sẻ is an MBNT-only concept; multiple files state this explicitly |
| TDPS — any Lợi nhuận/NIM figure, anywhere | **N/A** — same, explicit docstring: "No chia sẻ deduction (that is MBNT-only)" |
| PSHH — Lợi nhuận | **N/A** — not referenced in `ds_ln_pshh.py` |

## 6. Summary — Kho bạc / KBNN treatment, dashboard-wide

**Bdscif-level exclusion** (`bdscif != "1609448630"`, i.e. the client is dropped from the calculation entirely) applies **only** to:
- MBNT Doanh số — scorecard, dia_ban/PKKH charts, contribution donuts (both 2026 and 2025 baseline)
- MBNT NIM — but **only the doanh số leg** of the ratio; the lợi nhuận leg has no filter, so KBNN's profit still counts in MBNT NIM's numerator while its volume is excluded from the denominator (an asymmetry, not obviously intentional — worth confirming)
- HĐLS Doanh số — dia_ban/PKKH charts and contribution donuts (both years)

**Deduction-style exclusion** (KBNN's contribution is subtracted back out of an otherwise-inclusive total, rather than filtered at the row level) applies **only** to the **Cán bộ (staff)** table on Kết quả chi nhánh/cán bộ: `KH KDNT&PS 2026`, `KQ MBNT`, `KQ KDNT&PS`, `% tháng`, `% năm` — via the `_ko_KBNN` variants described in §3.2.

**No exclusion of any kind** applies to:
- Any Lợi nhuận figure for MBNT (dia_ban/PKKH charts, scorecards) outside the staff table above
- HĐLS or TDPS Lợi nhuận, NIM, or Số dư — anywhere, any tab
- TDPS Doanh số — anywhere
- The **Chi nhánh (branch)** table on Kết quả chi nhánh/cán bộ — confirmed no KBNN logic at all, staff-level only
- The Khách hàng tab — KBNN's customer row participates in the Top-10 rankings like any other customer
- PSHH — any figure

---

## 7. Data dictionary — every source table/file and the exact columns read from it

Column names below are read directly from the query/access code (`data_connect/db_connect.py`, `data_connect/excel_connect.py`, and each `calculations/*.py` file), not paraphrased — where a table is fetched with `SELECT *`, only the columns actually referenced downstream in pandas are listed, since those are the ones that feed a number on screen.

### Postgres — customer-level (silver / one row per customer per day)

**`silver."silver_pvkh_DL_KH_luy_ke"`** — via `silver_pvkh_dl_kh_luy_ke(date_str)`, `WHERE ngay = date_str`. The 2026 "true daily cumulative" source for MBNT/HĐLS/TDPS.
| Column | Used for |
|---|---|
| `bdscif` (= `bds`+`cif` concatenated) | dedup key; KBNN exclusion filters `bdscif != "1609448630"` |
| `bds`, `cif` | joined to `listbds()` (→ nhóm/địa bàn) and `pkkh_lookup()` (→ PKKH) |
| `ds_mbnt_luy_ke_den_ngay_bc` | MBNT doanh số, dia_ban/PKKH charts (`MAX` per bdscif) |
| `ln_mbnt_luy_ke_den_ngay_bc` | MBNT lợi nhuận *trước chia sẻ* — dia_ban/PKKH LN/NIM charts, then `pvkh_chiase` subtracted |
| `ds_hdls_luy_ke_den_ngay_bc`, `ds_irs_luy_ke_den_ngay_bc`, `ds_ccs_luy_ke_den_ngay_bc` | HĐLS doanh số stacked (IRS+CCS) dia_ban/PKKH chart |
| `ln_hdls_luy_ke_den_ngay_bc` | HĐLS lợi nhuận dia_ban/PKKH chart (no chia sẻ subtraction) |
| `ln_tdps_luy_ke_den_ngay_bc` | TDPS lợi nhuận dia_ban/PKKH chart (no chia sẻ subtraction) |
| `dia_ban` (needs cleanup: "Ha Noi"→"HN" etc.) | dia_ban dimension |

**`bronze_baocaotudong.pvkh_dailyreport`** — via `pvkh_dailyreport(date_str)`, `WHERE ngay = date_str`. One row per customer per day; carries `nhom_phu_trach`/`dia_ban`/`pkkh` natively (no join needed). Only customer-level source for TDPS balances and PSHH profit.
| Column | Used for |
|---|---|
| `ln_pshh_theo_mpa_ytd` | PSHH lợi nhuận (already YTD-cumulative per row, summed for the day) |
| `so_du_tdps_ngay_bc`, `so_du_tdps_bq_nam` | TDPS số dư dia_ban/PKKH charts (ngày / bình quân năm) |
| `so_du_ccs_ngay_bc`, `so_du_irs_ngay_bc`, `so_du_ccs_bq_nam`, `so_du_irs_bq_nam` | HĐLS số dư CCS/IRS dia_ban/PKKH charts |
| `dia_ban`, `pkkh`, `nhom_phu_trach` | dimensions (native on this table, unlike the silver table) |

**`bronze_baocaotudong.pvkh_dsdaily_temp`** — via `pvkh_dsdaily_temp(start_date, end_date)`. Daily (non-accumulative) doanh số, one row per (bds, cif, day) — despite its name, `monthyear` actually holds a real transaction date here.
| Column | Used for |
|---|---|
| `doanhsotdps` | TDPS doanh số (scorecards + dia_ban/PKKH), summed 1/1→date |
| `doanhsotlhh` | PSHH doanh số TLHH (lots), summed 1/1→date |
| `doanhsootc` | PSHH doanh số OTC (USD), summed 1/1→date |
| `bds`, `cif` | join key for dia_ban/pkkh enrichment |

**`bronze_baocaotudong.pvkh_fx`, `pvkh_pstc`, `pvkh_pshh`, `pvkh_chiase`** — all four fetched through the same helper, `_fx_or_pstc_merged(table, date_str)`, `WHERE monthyear` in `[year-start, date_str]`, left-joined to `pvkh_listcif`→`pvkh_pkkh` (for `pkkh`) and to `listbds()` (for `nhomphutrach`/`diaban`). Monthly snapshots — the source for every 2025 baseline (`y1_*`) via Full+Partial×ProrationRatio.
| Table | Columns used | Used for |
|---|---|---|
| `pvkh_fx` | `doanhsoswap2chan`, `loinhuan`, `sanpham` (∈ FW/SP/SW), `monthyear`, `bds`, `cif` | MBNT 2025 doanh số/lợi nhuận baseline |
| `pvkh_pstc` | `doanhso`, `loinhuan`, `sanpham` (HĐLS products / `'TDPS'`), `monthyear` | HĐLS and TDPS 2025 doanh số/lợi nhuận baseline |
| `pvkh_pshh` | `doanhso`, `loinhuan`, `sanpham` (∈ TLHH/OTC), `monthyear` | PSHH 2025 doanh số/lợi nhuận baseline |
| `pvkh_chiase` | `loinhuanchiase`, `monthyear`, `cif`, `bds` | subtracted from MBNT lợi nhuận (both years) to get "sau chia sẻ"; also the sole source for `LoiNhuan_KBNN()`'s `WHERE cif=9448630 AND bds=160` deduction |

**`bronze_baocaotudong.pvkh_listcif`** / **`pvkh_pkkh`** — joined inside the helper above and inside `pkkh_lookup(date_str)`: `pvkh_listcif[cif, mapkkh, monthyear]` (latest row per cif, year-filtered) → `pvkh_pkkh[mapkkh, tenpkkh]`. Supplies the `pkkh` dimension everywhere it's used. `KHCN*` variants collapsed to `"KHCN"`; `"ME"` and `"SME"` are kept as separate pkkh values (not merged), per user request.

### Postgres — nhóm-level (bronze, one row per nhóm phụ trách per day)

**`bronze_baocaotudong.pvkh_mbnt_nhom_phu_trach`** — via `pvkh_mbnt_nhom_phu_trach(date_str)` / `_range(start,end)`.
| Column | Used for |
|---|---|
| `sum_ds_mbnt_luy_ke_den_ngay_bc`, `sum_ln_mbnt_luy_ke_den_ngay_bc` | MBNT scorecard DS/LN, lũy kế (TOTAL summed from PTKD1+2+VPV) |
| `sum_ds_mbnt_ngay_bc` | MBNT scorecard DS, trong ngày |
| `sum_ln_mbnt_ngay_bao_cao` | MBNT scorecard LN, trong ngày — gross, no chia sẻ subtraction |
| `nim_mbnt_buy_spot_ngay_bc`, `nim_mbnt_sell_spot_ngay_bc` | NIM Spot Mua/Bán chart — pre-computed ratio columns |
| `nim_mbnt_ngay_bc` | NIM trong ngày (combined) chart — pre-computed ratio |

**`bronze_baocaotudong.pvkh_pstc_nhom_phu_trach`** — via `pvkh_pstc_nhom_phu_trach(date_str)` (latest snapshot on/before date) / `_range(start,end)` (every day in range, for NIM's balance-weighted average).
| Column | Used for |
|---|---|
| `sum_ds_hdls_luy_ke`, `sum_ln_hdls_luy_ke` | HĐLS scorecard DS/LN, lũy kế |
| `sum_ln_tdps_luy_ke` | TDPS scorecard/dia_ban charts LN, lũy kế |
| `sum_ds_hdls_ngay_bc`, `sum_ln_hdls_ngay_bc` | HĐLS scorecard DS/LN, trong ngày; also NIM HĐLS ngày's LN term |
| `sum_ln_tdps_ngay_bc` | TDPS scorecard LN, trong ngày; NIM TDPS ngày's LN term |
| `sum_so_du_ccs_ngay_bc`, `sum_so_du_irs_ngay_bc` | HĐLS số dư CCS/IRS, ngày (nhóm-level donut); NIM HĐLS's balance term |
| `so_du_ccs_binh_quan`, `so_du_irs_binh_quan` | HĐLS số dư CCS/IRS, bình quân năm (nhóm-level donut + scorecard) |
| `sum_so_du_tdps_ngay_bc` | TDPS số dư, ngày (nhóm-level donut) |
| `so_du_tdps_binh_quan` | TDPS số dư, bình quân năm (scorecard + donut); NIM TDPS's balance term |

**`bronze_baocaotudong.pvkh_kq_chinhanh`** — via `pvkh_kq_chinhanh()` (no date filter at fetch — filtered in pandas after; excludes `chi_nhanh == "TOTAL"` row). Feeds **only** the Kết quả chi nhánh/cán bộ tab.
| Column | Used for |
|---|---|
| `ngay`, `bds`, `chi_nhanh` | filter/join keys |
| `sum_ln_mbnt_luy_ke_den_ngay_bc` | Branch/Staff table "KQ MBNT" — a **third, separate** source table from the two MBNT LN columns above; no chia sẻ subtraction visible in this repo (open question, §3.2/§8) |
| `sum_ln_hdls_luy_ke` | "KQ HĐLS" |
| `sum_ln_tdps_luy_ke` | "KQ TDPS" |
| `sum_ln_pshh_luy_ke` | "KQ PSHH" |
| `sum_ln_kdntps_luy_ke` | "KQ KDNT&PS" |

**`bronze_baocaotudong.pvkh_kq_canbo`** — via `pvkh_KQ_CanBo()`: `SELECT cb_phu_trach, ngay`. Only supplies the staff roster (which `CB_phu_trach` values exist on which `ngay`) for the Cán bộ table — every actual figure in that table comes from `pvkh_kq_chinhanh` above, exploded from branch (BDS) to staff via `khkd_cn_ht`'s BDS↔staff mapping.

**`bronze_reuter_domestic.daily_currency_domestic`** — via `usd_vnd_rate(date_str)` / `usd_vnd_rate_range(start,end)`, column `"vndtom=d3"` (USD/VND rate). Used as the currency-conversion denominator in every NIM formula that needs to compare a VND profit against a USD-denominated balance (`nim_hdls_binh_quan_nhom.py`, `nim_tdps_binh_quan_nhom.py`, and their `_diaban_pkkh`/`_ngay` siblings). Gaps (weekends/holidays, occasional null) are forward-filled from the latest known trading-day rate.

### Excel (network share `\\10.21.17.45\RSTeam Private\...\Dữ liệu\`)

**`KHKD PTKD 2026.xlsx`** — via `ke_hoach_theo_ptkd()`. One row per (`san_pham`, `Nhóm phụ trách`), melted from monthly (`T1`.."T12".2026, cumulative-through-month) and annual/`"total"` plan columns, gated through three separate filter lists (`REQUIRED_SUBSTRINGS`, `INDICATOR_MAP`, `ANNUAL_COLUMNS`) that must all agree a column belongs before it's kept. Feeds every `HT tháng`/`HT năm` badge and every dashed KHKD target line on the dia_ban charts, for `san_pham` ∈ {DS MBNT, DS HDLS, DS PSHH, LN MBNT, LN HDLS, LN TDPS, LN PSHH, LN KDNT&PS}.

**`KHKD CN 2026.xlsx`** — via `khkd_cn_ht(path=CN_PATH)`. One row per BDS (branch/point-of-sale), columns `STT`, `BDS`, `Chi nhánh`, `Địa bàn`, `Nhóm phụ trách`, `Cán bộ phụ trách`, `KHKD KDNT&PS 2026`, `KHKD KDNT&PS T1.2026`..`T12.2026`. Feeds Kết quả chi nhánh/cán bộ's plan figures (`KH KDNT&PS 2026`, monthly-plan sums) for both the branch and staff tables, and supplies the BDS↔staff attribution map (`_staff_bds_sets()`) used for `is_bds_160`/KBNN detection.

**`DS CN trọng điểm 2026.xlsx`** — via `CN_trong_diem()`. The 64-branch roster (`STT`, `BDS`, `Chi nhánh`, `Nhóm phụ trách`, `Cán bộ phụ trách`) for the **branch** table specifically — the staff table's roster instead comes from Postgres (`pvkh_kq_canbo`).

**`KHKD CN 2026.xlsx`** (again, different sheet columns) — via `listbds(path=CN_PATH)`, columns `BDS`→`bds`, `Chi_nhánh`→`tencn`, `Địa bàn`→`diaban`, `Nhóm phụ trách`→`nhomphutrach`, `Cán bộ phụ trách`→`tencb`. This is the branch→nhóm/địa bàn lookup merged onto every `pvkh_fx`/`pvkh_pstc`/`pvkh_pshh`/`pvkh_chiase` row and onto `y_ds/ln_mbnt_by_nhom_diaban` (via `bds`) — i.e. this is *the* source of the "Nhóm phụ trách"/"địa bàn" labels for every dia_ban chart on the dashboard.

### Static CSV exports (Khách hàng tab only)

**`data/bao_cao_ket_qua_mbnt_2025_2026.csv`** / **`data/bao_cao_ket_qua_hdls_2025_2026.csv`** — frozen exports of a Postgres view (`bao_cao_ket_qua_mbnt/hdls_2025_2026_view`), last refreshed 2026-08-17, read via `_fetch_csv_for_date()` (not a live query). Raw CSV columns (snake_case) are renamed on load:

| Raw CSV column | Renamed to | Notes |
|---|---|---|
| `ngay` | Ngày | date filter |
| `ten_khach_hang` | Tên khách hàng | customer name — this is where `"KHO BAC NHA NUOC"` appears as a literal row |
| `loi_nhuan_2026_tr_vnd`, `loi_nhuan_2025_tr_vnd` | Lợi nhuận 2026/2025 (tr VND) | ranking basis for "Top LN" and threshold check |
| `tang_truong_loi_nhuan`, `tang_truong_loi_nhuan_pct` | Tăng trưởng lợi nhuận (+ %) | **pre-computed in the view**, not derived in this repo — ranking basis for the growth panels |
| `doanh_so_2026_tr_usd`, `doanh_so_2025_tr_usd` | Doanh số 2026/2025 (tr USD) | ranking basis for "Top DS" |
| `tang_truong_doanh_so`, `tang_truong_doanh_so_pct` | Tăng trưởng doanh số (+ %) | pre-computed, unused by the current panel set but present |
| `nim_2026`, `nim_2025`, `tang_truong_nim`, `tang_truong_nim_pct` | NIM columns | present in the MBNT CSV, not currently surfaced on the tab |
| `phan_khuc_khach_hang` | Phân khúc khách hàng | HĐLS CSV only |
| `so_du_irs_binh_quan_nam`, `so_du_ccs_binh_quan_nam` | Số dư IRS/CCS bình quân năm | HĐLS CSV only, not currently surfaced on this tab |
| `bds`, `cif` → derived `bdscif` | — | dedup key, and the `9448630`/`160` pair identifying KBNN's row |

`nhom_phu_trach`/`dia_ban`/`pkkh`/`Cán bộ phụ trách` are **not** present in the CSV (dropped in the 2026-08-17 export) and are re-enriched in Python (`_enrich_customer_attributes`) the same way as everywhere else — `listbds()` via `bds`, `pkkh_lookup()` via `cif`.

---

## 8. Open questions worth resolving with whoever owns the source data/ETL

1. **`pvkh_kq_chinhanh`'s MBNT column** (used by both Kết quả chi nhánh/cán bộ tables) — is it gross or net of chia sẻ? No code in this repo answers this, unlike every other MBNT LN path which is explicit either way.
2. **MBNT NIM's asymmetric KBNN treatment** — DS leg excludes KBNN, LN leg doesn't. Confirm whether this is intentional (e.g. "we want NIM without KBNN's low-margin volume, but its profit should still count") or an oversight.
3. **`KBNN_T7_DEDUCTION`'s "57"** — hardcoded as `110,000/100×57`, ported literally from the original DAX with no derivation visible in code. If anyone ever needs to extend this pattern to a different month, the source of "57" (looks like it should represent 7/12 of the year but doesn't exactly match) should be tracked down from whoever wrote the original DAX measure.
4. **Khách hàng tab's underlying Postgres view** (`bao_cao_ket_qua_mbnt/hdls_2025_2026_view`) — the actual growth-delta formula and any chia-sẻ/KBNN handling live only in that view's SQL definition, not in this Python codebase, and the CSV export is static (last refreshed 2026-08-17) rather than live.
