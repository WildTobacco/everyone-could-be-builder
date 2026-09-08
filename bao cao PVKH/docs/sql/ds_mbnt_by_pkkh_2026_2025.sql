WITH params AS (
    SELECT DATE '2026-08-13' AS d2026, DATE '2025-08-13' AS d2025
),
per_bdscif_2026 AS (
    SELECT s.bdscif, MAX(s.ds_mbnt_luy_ke_den_ngay_bc) AS ds, MIN(s.cif)::bigint AS cif
    FROM silver."silver_pvkh_DL_KH_luy_ke" s, params p
    WHERE s.ngay = p.d2026 AND s.bdscif <> '1609448630'
    GROUP BY s.bdscif
),
pkkh_lookup_2026 AS (
    SELECT DISTINCT ON (c.cif) c.cif::bigint AS cif, p.tenpkkh AS pkkh_raw
    FROM bronze_baocaotudong.pvkh_listcif c
    LEFT JOIN bronze_baocaotudong.pvkh_pkkh p ON c.mapkkh::bigint = p.mapkkh::bigint
    CROSS JOIN params prm
    WHERE EXTRACT(YEAR FROM c.monthyear) <= EXTRACT(YEAR FROM prm.d2026)
    ORDER BY c.cif, c.monthyear DESC
),
ds_2026 AS (
    SELECT
        CASE WHEN l.pkkh_raw LIKE '%KHCN%' THEN 'KHCN' WHEN l.pkkh_raw = 'ME' THEN 'SME' ELSE l.pkkh_raw END AS pkkh,
        SUM(b.ds) AS doanh_so_2026
    FROM per_bdscif_2026 b
    LEFT JOIN pkkh_lookup_2026 l ON l.cif = b.cif
    GROUP BY 1
),
fx_2025 AS (
    SELECT f.monthyear, f.doanhsoswap2chan, f.bds::text || f.cif::text AS bdscif,
        CASE WHEN p.tenpkkh LIKE '%KHCN%' THEN 'KHCN' WHEN p.tenpkkh = 'ME' THEN 'SME' ELSE p.tenpkkh END AS pkkh
    FROM bronze_baocaotudong.pvkh_fx f
    CROSS JOIN params prm
    LEFT JOIN LATERAL (
        SELECT c.mapkkh::bigint AS mapkkh FROM bronze_baocaotudong.pvkh_listcif c
        WHERE c.cif::bigint = f.cif::bigint AND EXTRACT(YEAR FROM c.monthyear) <= EXTRACT(YEAR FROM prm.d2025)
        ORDER BY c.monthyear DESC LIMIT 1
    ) c ON true
    LEFT JOIN bronze_baocaotudong.pvkh_pkkh p ON p.mapkkh::bigint = c.mapkkh
    WHERE f.sanpham IN ('FW', 'SP', 'SW') AND f.monthyear >= DATE_TRUNC('year', prm.d2025) AND f.monthyear <= prm.d2025
),
ds_2025 AS (
    SELECT f.pkkh,
        SUM(CASE
            WHEN f.monthyear < DATE_TRUNC('month', p.d2025) THEN f.doanhsoswap2chan
            WHEN f.monthyear = DATE_TRUNC('month', p.d2025)
                THEN f.doanhsoswap2chan * EXTRACT(DAY FROM p.d2025) / EXTRACT(DAY FROM (DATE_TRUNC('month', p.d2025) + INTERVAL '1 month' - INTERVAL '1 day'))
            ELSE 0
        END) AS doanh_so_2025
    FROM fx_2025 f CROSS JOIN params p
    WHERE f.bdscif <> '1609448630'
    GROUP BY f.pkkh
)
SELECT
    COALESCE(a.pkkh, b.pkkh) AS pkkh,
    COALESCE(b.doanh_so_2025, 0) AS doanh_so_mbnt_2025,
    COALESCE(a.doanh_so_2026, 0) AS doanh_so_mbnt_2026,
    COALESCE(a.doanh_so_2026, 0) - COALESCE(b.doanh_so_2025, 0) AS delta,
    CASE WHEN COALESCE(b.doanh_so_2025, 0) <> 0 THEN (COALESCE(a.doanh_so_2026, 0) - b.doanh_so_2025) / b.doanh_so_2025 * 100 ELSE NULL END AS pct_change
FROM ds_2026 a
FULL OUTER JOIN ds_2025 b ON a.pkkh = b.pkkh
ORDER BY doanh_so_mbnt_2026 DESC NULLS LAST;
