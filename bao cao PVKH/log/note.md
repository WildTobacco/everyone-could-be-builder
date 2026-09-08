# Note

# Dashboard 5(3)
    - LN_luy_ke_KDNTPS_PTKD1/PTKD2/VPV
        + Table: pvkh_kdntps_nhom_phu_trach
        + Column: sum_LN_KDNTPS_luy_ke
        + MAX('bronze_baocaotudong pvkh_kdntps_nhom_phu_trach'[sum_LN_KDNTPS_luy_ke])
        'bronze_baocaotudong pvkh_kdntps_nhom_phu_trach'[Nhom_phu_trach] = "PTKD 1/PTKD 2/VPV"

    - (Score_Card)(Y-1)Tong_LN_Nhom_PTKD1/PTKD2/VPV
        + Table: bronze_baocaotudong pvkh_fx
        + Column: loinhuan, monthyear, bdscif
        + Table: bronze_baocaotudong pvkh_pstc
        + Column: loinhuan, monthyear, bdscif, sanpham (filtered to "IRS" / "CCS" / "AIRS" / "TDPS" — same table queried 4 times)
        + Table: bronze_baocaotudong pvkh_pshh, 
        + Column: loinhuan, monthyear, bdscif
        + Filter by nhom_phu_trach using bds
        + Prorapation logic: Full months (Jan 1 → last complete month) + Partial current month × ProrationRatio
        ProrationRatio = selected day / total days in that month
        + Same day last year: 2026-07-30 → compare with 2025-07-30
        2025 value = Jan-Jun full months + July * 30/31
        + FX — table pvkh_fx (2025), column loinhuan
        IRS — table pvkh_pstc (2025), column loinhuan, filter sanpham = "IRS"
        CCS — table pvkh_pstc (2025), column loinhuan, filter sanpham = "CCS"
        AIRS — table pvkh_pstc (2025), column loinhuan, filter sanpham = "AIRS"
        TDPS — table pvkh_pstc (2025), column loinhuan, filter sanpham = "TDPS"
        PSHH — table pvkh_pshh (2025), column loinhuan
        + _Full = SUM(loinhuan) where monthyear >= FirstDayLastYear AND monthyear < RefMonthLastYear
        _Partial = SUM(loinhuan) where monthyear = RefMonthLastYear, × ProrationRatio

    - (Score_Card)%_Change_LN_Nhom_PTKD1/PTKD2/VPV
        + Measurement: LN_luy_ke_KDNTPS_PTKD1/PTKD2/VPV
        + Measurement: (Score_Card)(Y-1)Tong_LN_Nhom_PTKD1/PTKD2/VPV

    - (Y)PTKD1/PTKD2/VPV_LN_Hoan_Thanh_Thang
        + Measurement: [LN_luy_ke_KDNTPS_PTKD1/PTKD2/VPV] 
        + Table: (ke_hoach_using)ke_hoach_theo_ptkd ("\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC Dashboard PVKH ngày\Dữ liệu\KHKD PTKD 2026.xlsx")
        + Column: ke_hoach (summed), nhom_phu_trach (filtered "PTKD 1"), san_pham (filtered "LN KDNT&PS"), month (filtered to current month as text)

    - (Y)PTKD1/PTKD2/VPV_LN_Hoan_Thanh
         + Measurement: [LN_luy_ke_KDNTPS_PTKD1/PTKD2/VPV] 
        + Table: (ke_hoach_using)ke_hoach_theo_ptkd ("\\10.21.17.45\RSTeam Private\4. BÁO CÁO DASHBOARD_ DATA\BC Dashboard PVKH ngày\Dữ liệu\KHKD PTKD 2026.xlsx")
        + Column: ke_hoach (summed), nhom_phu_trach (filtered "PTKD 1"), san_pham (filtered "LN KDNT&PS"), month (filtered to literal "total" — not tied to a specific month, unlike the previous measure)
        
