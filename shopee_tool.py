import csv
import json
from pathlib import Path
from collections import defaultdict


def load_config(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text):
    return text.strip().lower()


def parse_account_file(input_file, exclude_keywords):
    """
    Đọc và parse dữ liệu của 1 account.
    Trả về:
        records: danh sách giao dịch
        total_earn: tổng xu nhận được
        total_spent: tổng xu đã dùng
    """

    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    records = []
    total_earn = 0
    total_spent = 0

    # ===== PARSE DATA =====
    for i in range(0, len(lines), 4):
        block = lines[i:i + 4]

        if len(block) < 4:
            continue

        chuong_trinh = block[0].strip()
        hoat_dong = block[1].strip()
        thoi_gian = block[2].strip()
        xu_raw = block[3].strip()

        text = (chuong_trinh + " " + hoat_dong).lower()

        # ❌ FILTER theo config
        if any(keyword in text for keyword in exclude_keywords):
            continue

        try:
            xu_clean = int(
                xu_raw.replace("+", "")
                      .replace("-", "")
                      .replace(".", "")
                      .replace(",", "")
            )
        except ValueError:
            continue

        xu = -xu_clean if xu_raw.startswith("-") else xu_clean

        records.append({
            "Chương trình": chuong_trinh,
            "Hoạt động": hoat_dong,
            "Thời gian": thoi_gian,
            "Xu": xu
        })

        # ===== TÍNH TỔNG ACCOUNT =====
        if xu > 0:
            total_earn += xu
        else:
            total_spent += abs(xu)

    return records, total_earn, total_spent


def parse_shopee_xu(input_folder, output_file, config_file):
    config = load_config(config_file)

    # Chuẩn hóa keyword về lowercase
    exclude_keywords = [
        k.lower() for k in config.get("exclude_keywords", [])
    ]

    input_path = Path(input_folder)

    if not input_path.exists():
        print(f"❌ Không tìm thấy folder: {input_folder}")
        return

    if not input_path.is_dir():
        print(f"❌ Đây không phải folder: {input_folder}")
        return

    # ===== TÌM TẤT CẢ FILE TXT =====
    txt_files = sorted(input_path.glob("*.txt"))

    if not txt_files:
        print(f"❌ Không có file .txt nào trong folder: {input_folder}")
        return

    # ===== BIẾN TỔNG =====
    all_records = []

    total_earn = 0
    total_spent = 0

    category_net = defaultdict(int)
    category_display = {}

    # Lưu tổng xu theo từng account
    account_earn = {}

    # ===== LOOP TỪNG ACCOUNT =====
    for txt_file in txt_files:

        # Ví dụ:
        # kiennv12_t1.txt -> kiennv12_t1
        account_name = txt_file.stem

        print(f"Đang xử lý: {txt_file.name}")

        records, account_total_earn, account_total_spent = parse_account_file(
            txt_file,
            exclude_keywords
        )

        # Lưu tổng của account
        account_earn[account_name] = account_total_earn

        # ===== CỘNG DỒN TỔNG =====
        total_earn += account_total_earn
        total_spent += account_total_spent

        # ===== PHÂN TÍCH CATEGORY =====
        for r in records:
            xu = r["Xu"]

            raw_cat = r["Chương trình"]
            cat = normalize_text(raw_cat)

            # lưu tên hiển thị (giữ cái đầu tiên gặp)
            if cat not in category_display:
                category_display[cat] = raw_cat

            category_net[cat] += xu

        # Gộp record vào output chung
        all_records.extend(records)

    # ===== GHI CSV =====
    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Chương trình", "Hoạt động", "Thời gian", "Xu"]
        )

        writer.writeheader()
        writer.writerows(all_records)

    # ===== CHỈ LẤY CATEGORY KIẾM XU =====
    positive_categories = {
        k: v for k, v in category_net.items()
        if v > 0
    }

    total_positive = sum(positive_categories.values())

    # ===== SORT CATEGORY =====
    sorted_categories = sorted(
        positive_categories.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # ===== IN THỐNG KÊ TỔNG =====
    print("\n===== THỐNG KÊ =====")
    print(f"Tổng xu nhận được: {total_earn}")
    print(f"Tổng xu đã dùng: {total_spent}")

    print("\nPhần trăm theo Chương trình (giảm dần):")

    for cat, value in sorted_categories:
        display_name = category_display[cat]

        percent = (
            (value / total_positive) * 100
            if total_positive
            else 0
        )

        print(
            f"- {display_name}: "
            f"{value} xu ({percent:.2f}%)"
        )

    # ===== THỐNG KÊ TỪNG ACCOUNT =====
    print("\n===== XU NHẬN ĐƯỢC THEO ACCOUNT =====")

    for account_name, xu in account_earn.items():
        print(f"{account_name}: {xu}")

    # Tổng tất cả account
    print("==========")
    print(f"Tổng: {total_earn}")


if __name__ == "__main__":
    parse_shopee_xu(
        "input",
        "output.csv",
        "config.json"
    )

    print("\n✅ Done!")