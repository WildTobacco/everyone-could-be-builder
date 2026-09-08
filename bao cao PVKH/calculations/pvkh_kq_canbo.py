"""Python port of the 'pvkh_KQ_CanBo' Power Query.

Source: bronze_baocaotudong.pvkh_kq_canbo. After the M query's column-removal
steps every original metric column is dropped, leaving only (Ngay, CB_phu_trach,
Nhóm phụ trách) — so this loader only ever selects those two source columns.
"""

import pandas as pd

from data_connect.db_connect import get_connection

DS_VPV = {
    "Hoàng Mai Linh", "Huỳnh Thị Thanh Quỳnh", "Lê Ngọc Minh Thu",
    "Lê Ngọc Vinh", "Ngô Thanh Vân", "Nguyễn Hữu Phương Nam",
    "Nguyễn Ngọc Trâm", "Hoàng Thị Thu Nga", "Lương Thanh Hà",
    "Thái Doãn Tuấn",
}

DS_PTKD1 = {
    "Cao Hồng Quân", "Chu Ngọc Duy", "Lê Việt Dũng",
    "Phạm Duy Hưng", "Lê Thanh Lương",
}

DS_PTKD2 = {
    "Đặng Đức Lương", "Nguyễn Minh Anh", "Nguyễn Phương Hoa",
    "Phạm Quang Lâm", "Tạ Phương Linh", "Từ Quốc Hưng",
    "Vũ Thúy Lan Anh", "Đặng Thùy Linh",
}

DS_PTKD1_CoDinh = DS_PTKD1 - {"Lê Thanh Lương"}
DS_PTKD2_CoDinh = DS_PTKD2 - {"Đặng Thùy Linh", "Từ Quốc Hưng", "Vũ Thúy Lan Anh"}

# (ASCII source value in Postgres) -> (proper Vietnamese diacritics), applied in this order
NAME_FIXES = [
    ("Cao Hong Quan", "Cao Hồng Quân"),
    ("Chu Ngoc Duy", "Chu Ngọc Duy"),
    ("Dang Duc Luong", "Đặng Đức Lương"),
    ("Dang Thuy Linh", "Đặng Thùy Linh"),
    ("Dao Duy Linh", "Đào Duy Linh"),
    ("Duong Duc Minh", "Dương Đức Minh"),
    ("Hoang Mai Linh", "Hoàng Mai Linh"),
    ("Hoang Thi Thu Nga", "Hoàng Thị Thu Nga"),
    ("Huynh Thi Thanh Quynh", "Huỳnh Thị Thanh Quỳnh"),
    ("Le Ngoc Minh Thu", "Lê Ngọc Minh Thu"),
    ("Le Ngoc Vinh", "Lê Ngọc Vinh"),
    ("Le Viet Dung", "Lê Việt Dũng"),
    ("Ngo Thanh Van", "Ngô Thanh Vân"),
    ("Nguyen Duc Anh", "Nguyễn Đức Anh"),
    ("Nguyen Huu Phuong Nam", "Nguyễn Hữu Phương Nam"),
    ("Nguyen Minh Anh", "Nguyễn Minh Anh"),
    ("Nguyen Ngoc Tram", "Nguyễn Ngọc Trâm"),
    ("Nguyen Phuong Hoa", "Nguyễn Phương Hoa"),
    ("Pham Duy Hung", "Phạm Duy Hưng"),
    ("Pham Quang Lam", "Phạm Quang Lâm"),
    ("Ta Phuong Linh", "Tạ Phương Linh"),
    ("Thai Doan Tuan", "Thái Doãn Tuấn"),
    ("Luong Thanh Ha", "Lương Thanh Hà"),
    ("Ngo Thi Thao Huong", "Ngô Thị Thảo Hương"),
    ("Nguyen Tuan Phong", "Nguyễn Tuấn Phong"),
]

# staff (already diacritic-fixed) -> (start date, group), backfilled through the latest data date
MANUAL_STAFF = [
    ("Từ Quốc Hưng", pd.Timestamp(2026, 7, 1), "PTKD 2"),
    ("Vũ Thúy Lan Anh", pd.Timestamp(2026, 7, 1), "PTKD 2"),
    ("Nguyễn Tuấn Phong", pd.Timestamp(2026, 7, 15), "PTKD 2"),
    ("Lê Thanh Lương", pd.Timestamp(2026, 7, 1), "PTKD 1"),
]


def _assign_nhom_phu_trach(row) -> str | None:
    cb, ngay = row["CB_phu_trach"], row["Ngay"]

    if cb == "Dương Đức Minh":
        return "KHÔNG CÒN CÔNG TÁC" if ngay >= pd.Timestamp(2026, 4, 1) else "PTKD 2"
    if cb in DS_VPV:
        return "VPV"
    if cb == "Đặng Thùy Linh":
        return "PTKD 2" if ngay >= pd.Timestamp(2026, 4, 1) else "PTKD 1"
    if cb == "Ngô Thị Thảo Hương" and pd.Timestamp(2026, 4, 1) <= ngay < pd.Timestamp(2026, 7, 1):
        return "PTKD 2"
    if cb == "Nguyễn Đức Anh" and ngay < pd.Timestamp(2026, 7, 1):
        return "PTKD 2"
    if cb == "Từ Quốc Hưng" and ngay >= pd.Timestamp(2026, 7, 1):
        return "PTKD 2"
    if cb == "Vũ Thúy Lan Anh" and ngay >= pd.Timestamp(2026, 7, 1):
        return "PTKD 2"
    if cb == "Nguyễn Tuấn Phong" and ngay >= pd.Timestamp(2026, 7, 15):
        return "PTKD 2"
    if cb == "Đào Duy Linh" and ngay < pd.Timestamp(2026, 7, 1):
        return "PTKD 1"
    if cb == "Lê Thanh Lương" and ngay >= pd.Timestamp(2026, 7, 1):
        return "PTKD 1"
    if cb in DS_PTKD2_CoDinh:
        return "PTKD 2"
    if cb in DS_PTKD1_CoDinh:
        return "PTKD 1"
    return None


def pvkh_KQ_CanBo() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT cb_phu_trach, ngay FROM bronze_baocaotudong.pvkh_kq_canbo;", conn)
    conn.close()

    df = df.rename(columns={"ngay": "Ngay", "cb_phu_trach": "CB_phu_trach"})
    df = df[df["CB_phu_trach"].notna() & ~df["CB_phu_trach"].isin(["0", "TOTAL"])]

    df["Ngay"] = pd.to_datetime(df["Ngay"])
    df["CB_phu_trach"] = df["CB_phu_trach"].astype(str)

    for old, new in NAME_FIXES:
        df["CB_phu_trach"] = df["CB_phu_trach"].str.replace(old, new, regex=False)

    df["Nhóm phụ trách"] = df.apply(_assign_nhom_phu_trach, axis=1)

    max_data_date = df["Ngay"].max() if len(df) else pd.Timestamp.now().normalize()

    manual_rows = []
    existing_keys = set(zip(df["CB_phu_trach"], df["Ngay"]))
    for staff, start_date, group in MANUAL_STAFF:
        if start_date > max_data_date:
            continue
        for d in pd.date_range(start_date, max_data_date, freq="D"):
            if (staff, d) not in existing_keys:
                manual_rows.append({"CB_phu_trach": staff, "Ngay": d, "Nhóm phụ trách": group})

    if manual_rows:
        df = pd.concat([df, pd.DataFrame(manual_rows)], ignore_index=True)

    df["Ngay"] = df["Ngay"].dt.date
    return df.sort_values(["Ngay", "CB_phu_trach"]).reset_index(drop=True)


if __name__ == "__main__":
    d = pvkh_KQ_CanBo()
    print("rows:", len(d))
    print(d["Nhóm phụ trách"].value_counts(dropna=False))
    print(d.tail(20).to_string())
