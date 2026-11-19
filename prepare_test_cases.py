"""prepare_test_cases.py - chuẩn bị thư mục test_cases/ (Thành viên 3).

Ba lệnh:

  check   Kiểm tra cấu trúc thư mục và số ảnh so với bài báo (Bảng 8).
            python prepare_test_cases.py check

  custom  Chuẩn hóa 20 ảnh tự chụp: cắt giữa theo tỉ lệ 3:2, thu về cạnh dài 600 px,
          lưu PNG vào test_cases/custom_night/input, ghi manifest.csv.
          Ảnh gốc đặt tên theo nhóm: red_01.jpg, night_01.jpg, backlit_01.jpg, dark_01.jpg
            python prepare_test_cases.py custom --raw ~/anh_goc_dien_thoai

  hist    Thống kê lược đồ xám của ảnh input: % điểm ảnh có độ xám <= 40 (thang 0-255)
          và độ xám trung bình, ghi histogram_stats.csv. Dùng để kiểm chứng (hoặc sửa)
          nhận định "trên 85% điểm ảnh nằm ở dải [0, 40]" trong Mục 3 của báo cáo.
            python prepare_test_cases.py hist
"""
import argparse
import csv
import os
import sys

import cv2
import numpy as np

from measure import IMG_EXT, list_images

import asciiout  # noqa: F401  (in man hinh khong dau)

HERE = os.path.dirname(os.path.abspath(__file__))

# Số ảnh test theo Bảng 8 của bài báo; custom_night theo bảng phân công (20 ảnh)
EXPECTED = {
    "LOLv1": {"input": 15, "gt": 15},
    "LOLv2_Real": {"input": 100, "gt": 100},
    "DICM": {"input": 69},
    "LIME": {"input": 10},
    "MEF": {"input": 17},
    "custom_night": {"input": 20},
}
CATEGORIES = {"red": "vật thể màu đỏ", "night": "cảnh đêm",
              "backlit": "ngược sáng / có đèn pha", "dark": "tối kín"}
DARK_THRESHOLD = 40


def cmd_check(test_dir):
    ok = True
    for ds, parts in EXPECTED.items():
        for part, want in parts.items():
            folder = os.path.join(test_dir, ds, part)
            have = len(list_images(folder)) if os.path.isdir(folder) else 0
            flag = "OK " if have == want else "THIẾU" if have < want else "THỪA"
            ok &= have == want
            print(f"[{flag}] {ds}/{part}: {have}/{want} ảnh")
        if "gt" in parts and os.path.isdir(os.path.join(test_dir, ds, "input")):
            a = {os.path.splitext(f)[0] for f in list_images(os.path.join(test_dir, ds, "input"))}
            b = {os.path.splitext(f)[0] for f in list_images(os.path.join(test_dir, ds, "gt"))} \
                if os.path.isdir(os.path.join(test_dir, ds, "gt")) else set()
            if a != b:
                ok = False
                print(f"  [LỆCH TÊN] {ds}: input và gt khác nhau {sorted(a ^ b)[:5]}...")
    print("\nSẵn sàng." if ok else "\nCòn thiếu/lệch, xem các dòng trên.")
    return 0 if ok else 1


def center_crop_resize(img, long_side=600):
    h, w = img.shape[:2]
    landscape = w >= h
    ar = 3 / 2  # dài / ngắn
    if landscape:
        tw = min(w, int(round(h * ar)))
        th = int(round(tw / ar))
    else:
        th = min(h, int(round(w * ar)))
        tw = int(round(th / ar))
    x0, y0 = (w - tw) // 2, (h - th) // 2
    crop = img[y0:y0 + th, x0:x0 + tw]
    scale = long_side / max(tw, th)
    return cv2.resize(crop, (int(round(tw * scale)), int(round(th * scale))), interpolation=cv2.INTER_AREA)


def cmd_custom(raw_dir, test_dir):
    dst = os.path.join(test_dir, "custom_night", "input")
    os.makedirs(dst, exist_ok=True)
    rows = []
    for f in sorted(os.listdir(raw_dir)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in IMG_EXT:
            continue
        cat = stem.split("_")[0]
        if cat not in CATEGORIES:
            print(f"[bỏ qua] {f}: tên phải bắt đầu bằng {sorted(CATEGORIES)} (vd red_01.jpg)")
            continue
        img = cv2.imread(os.path.join(raw_dir, f), cv2.IMREAD_COLOR)  # OpenCV tự xoay theo EXIF
        if img is None:
            print(f"[bỏ qua] không đọc được {f}")
            continue
        oh, ow = img.shape[:2]
        out = center_crop_resize(img)
        cv2.imwrite(os.path.join(dst, stem + ".png"), out)
        gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
        rows.append({"file": stem + ".png", "category": cat, "meaning": CATEGORIES[cat],
                     "orig_w": ow, "orig_h": oh, "out_w": out.shape[1], "out_h": out.shape[0],
                     "mean_gray": round(float(gray.mean()), 2),
                     "pct_gray_le_40": round(100.0 * float((gray <= DARK_THRESHOLD).mean()), 2),
                     "camera_phone": "", "note": ""})
    man = os.path.join(test_dir, "custom_night", "manifest.csv")
    with open(man, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["file"])
        w.writeheader()
        w.writerows(rows)
    by_cat = {c: sum(r["category"] == c for r in rows) for c in CATEGORIES}
    print(f"Đã xử lý {len(rows)} ảnh -> {dst}\nTheo nhóm: {by_cat}\nManifest: {man}")
    print("Gợi ý phân bổ 20 ảnh: red 6, night 6, backlit 4, dark 4. Điền cột camera_phone (tên điện thoại).")


def cmd_hist(test_dir, out_csv):
    rows = []
    for ds in sorted(os.listdir(test_dir)):
        folder = os.path.join(test_dir, ds, "input")
        if not os.path.isdir(folder) or not list_images(folder):
            continue
        n_total = 0
        n_dark = 0
        means = []
        for f in list_images(folder):
            g = cv2.cvtColor(cv2.imread(os.path.join(folder, f)), cv2.COLOR_BGR2GRAY)
            n_total += g.size
            n_dark += int((g <= DARK_THRESHOLD).sum())
            means.append(float(g.mean()))
        rows.append({"dataset": ds, "n_images": len(means), "mean_gray": round(float(np.mean(means)), 2),
                     "pct_pixels_gray_le_40": round(100.0 * n_dark / n_total, 2)})
        print(rows[-1])
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "n_images", "mean_gray", "pct_pixels_gray_le_40"])
        w.writeheader()
        w.writerows(rows)
    print(f"Đã ghi {out_csv}. Dùng số này thay cho '85%' trong báo cáo nếu khác.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("cmd", choices=["check", "custom", "hist"])
    ap.add_argument("--test-dir", default=os.path.join(HERE, "test_cases"))
    ap.add_argument("--raw", help="thư mục ảnh gốc chụp bằng điện thoại (lệnh custom)")
    ap.add_argument("--out-csv", default=os.path.join(HERE, "histogram_stats.csv"))
    a = ap.parse_args()
    if a.cmd == "check":
        return cmd_check(a.test_dir)
    if a.cmd == "custom":
        if not a.raw:
            ap.error("lệnh custom cần --raw")
        return cmd_custom(a.raw, a.test_dir)
    return cmd_hist(a.test_dir, a.out_csv)


if __name__ == "__main__":
    sys.exit(main())
