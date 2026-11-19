"""eval.py - chạy đánh giá hàng loạt và ghi quantitative_results.csv (Thành viên 3).

Quy ước thư mục (xem README.md):
  test_cases/<DATASET>/input/   ảnh thiếu sáng
  test_cases/<DATASET>/gt/      ảnh chuẩn (chỉ bộ có cặp)
  results/<DATASET>/<METHOD>/   ảnh đầu ra của từng phương pháp, TÊN FILE TRÙNG ảnh input

Hai lệnh:

1) Tạo ảnh đầu ra của các thuật toán cổ điển (cùng tham số: CLAHE clip 2.0, lưới 8x8, Gamma 0.4):
     python eval.py baselines --datasets LOLv1 LOLv2_Real DICM LIME custom_night   # OpenCV
     python eval.py scratch   --datasets LOLv1 LOLv2_Real DICM LIME custom_night   # tự code của TV1
   (scratch dùng file color_space_scratch.py của TV1 đặt cạnh eval.py, hoặc chỉ định --tv1-file)

   Ảnh của HVI-CIDNet: chạy mã chính thức (github.com/Fediory/HVI-CIDNet) trên
   test_cases/<DATASET>/input rồi chép ảnh ra results/<DATASET>/HVI-CIDNet/.

2) Đo và ghi CSV:
     python eval.py evaluate --datasets LOLv1 LOLv2_Real DICM LIME custom_night

   Mặc định GT Mean chỉ dùng cho LOLv1 (đúng như bài báo, Mục 10.2); đổi bằng
   --gt-mean-datasets. Kết quả = các dòng trích từ bài báo (paper_reference.csv)
   + các dòng nhóm tự chạy, cột `source` phân biệt hai loại.
"""
import argparse
import csv
import math
import os
import sys

import cv2
import numpy as np

from measure import DeepMetrics, list_images, measure_folder, summarize

import asciiout  # noqa: F401  (in man hinh khong dau)

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["dataset", "method", "n_images", "psnr", "ssim", "lpips", "niqe", "brisque",
          "gt_mean", "source", "note"]

# Tham số dùng chung cho bản OpenCV và bản tự code của TV1 (khớp enhance_classical_scratch)
CLAHE_CLIP = 2.0
CLAHE_TILE = (8, 8)
GAMMA = 0.4


def opencv_clahe(bgr):
    """CLAHE của OpenCV trên kênh V của HSV (giống cách làm của bản tự code TV1)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_TILE)
    hsv[..., 2] = clahe.apply(hsv[..., 2])
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def opencv_gamma(bgr):
    """Gamma correction (out = 255 * (x/255)^GAMMA) bằng bảng tra cv2.LUT."""
    lut = np.array([255.0 * (i / 255.0) ** GAMMA for i in range(256)]).clip(0, 255).astype(np.uint8)
    return cv2.LUT(bgr, lut)


def run_baselines(test_dir, results_dir, datasets):
    for ds in datasets:
        src = os.path.join(test_dir, ds, "input")
        if not os.path.isdir(src):
            print(f"[bỏ qua] không thấy {src}")
            continue
        for name, fn in (("opencv_clahe", opencv_clahe), ("opencv_gamma", opencv_gamma)):
            dst = os.path.join(results_dir, ds, name)
            os.makedirs(dst, exist_ok=True)
            n = 0
            for f in list_images(src):
                bgr = cv2.imread(os.path.join(src, f), cv2.IMREAD_COLOR)
                cv2.imwrite(os.path.join(dst, os.path.splitext(f)[0] + ".png"), fn(bgr))
                n += 1
            print(f"{ds}/{name}: {n} ảnh -> {dst}")


def run_scratch(test_dir, results_dir, datasets, tv1_file):
    """Chạy CLAHE và Gamma tự code của TV1 (color_space_scratch.py) trên ảnh input."""
    import importlib.util
    if not os.path.exists(tv1_file):
        sys.exit(f"Không thấy {tv1_file}. Chép color_space_scratch.py của TV1 vào cạnh eval.py "
                 f"hoặc dùng --tv1-file.")
    spec = importlib.util.spec_from_file_location("color_space_scratch", tv1_file)
    tv1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tv1)
    fns = {
        "scratch_clahe": lambda rgb: tv1.clahe_scratch(rgb, clip_limit=CLAHE_CLIP, grid_size=CLAHE_TILE),
        "scratch_gamma": lambda rgb: tv1.gamma_correction_scratch(rgb, gamma=GAMMA),
    }
    for ds in datasets:
        src = os.path.join(test_dir, ds, "input")
        if not os.path.isdir(src):
            print(f"[bỏ qua] không thấy {src}")
            continue
        for name, fn in fns.items():
            dst = os.path.join(results_dir, ds, name)
            os.makedirs(dst, exist_ok=True)
            n = 0
            for f in list_images(src):
                bgr = cv2.imread(os.path.join(src, f), cv2.IMREAD_COLOR)
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)   # code TV1 nhận ảnh RGB
                out = fn(rgb)
                cv2.imwrite(os.path.join(dst, os.path.splitext(f)[0] + ".png"),
                            cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
                n += 1
            print(f"{ds}/{name}: {n} ảnh -> {dst}")


def fmt(x):
    return "" if (x is None or (isinstance(x, float) and math.isnan(x))) else f"{x:.4f}" \
        if isinstance(x, float) else x


def run_evaluate(test_dir, results_dir, datasets, gt_mean_ds, out_csv, per_image_csv):
    deep = DeepMetrics()
    own, per_image = [], []
    for ds in datasets:
        res_ds = os.path.join(results_dir, ds)
        if not os.path.isdir(res_ds):
            print(f"[bỏ qua] chưa có {res_ds}")
            continue
        gt_dir = os.path.join(test_dir, ds, "gt")
        paired = os.path.isdir(gt_dir) and len(list_images(gt_dir)) > 0
        for method in sorted(os.listdir(res_ds)):
            pred = os.path.join(res_ds, method)
            if not os.path.isdir(pred) or not list_images(pred):
                continue
            use_gm = paired and ds in gt_mean_ds
            rows = measure_folder(pred, gt_dir if paired else None, use_gm, deep)
            s = summarize(rows)
            own.append({"dataset": ds, "method": method, "n_images": s["n_images"],
                        "psnr": s["psnr"], "ssim": s["ssim"], "lpips": s["lpips"],
                        "niqe": s["niqe"], "brisque": s["brisque"],
                        "gt_mean": "yes" if use_gm else "no", "source": "nhom_tu_chay",
                        "note": "" if paired else "không có ảnh chuẩn: chỉ NIQE/BRISQUE"})
            for r in rows:
                per_image.append({"dataset": ds, "method": method, **r})
            print(f"{ds:14s} {method:16s} n={s['n_images']:3d} PSNR={fmt(s['psnr']) or '-'} "
                  f"SSIM={fmt(s['ssim']) or '-'} LPIPS={fmt(s['lpips']) or '-'} "
                  f"NIQE={fmt(s['niqe']) or '-'}")

    paper = []
    ref = os.path.join(HERE, "paper_reference.csv")
    if os.path.exists(ref):
        with open(ref, newline="", encoding="utf-8") as fh:
            paper = list(csv.DictReader(fh))
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in paper:
            w.writerow({k: r.get(k, "") for k in FIELDS})
        for r in own:
            w.writerow({k: fmt(r.get(k, "")) for k in FIELDS})
    with open(per_image_csv, "w", newline="", encoding="utf-8") as fh:
        cols = ["dataset", "method", "image", "psnr", "ssim", "lpips", "niqe", "brisque"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in per_image:
            w.writerow({k: fmt(r[k]) if k not in ("dataset", "method", "image") else r[k] for k in cols})
    print(f"\nĐã ghi {out_csv} ({len(paper)} dòng bài báo + {len(own)} dòng nhóm tự chạy)")
    print(f"Đã ghi {per_image_csv}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("cmd", choices=["baselines", "scratch", "evaluate"])
    ap.add_argument("--test-dir", default=os.path.join(HERE, "test_cases"))
    ap.add_argument("--results-dir", default=os.path.join(HERE, "results"))
    ap.add_argument("--datasets", nargs="+",
                    default=["LOLv1", "LOLv2_Real", "DICM", "LIME", "custom_night"])
    ap.add_argument("--gt-mean-datasets", nargs="*", default=["LOLv1"])
    ap.add_argument("--tv1-file", default=os.path.join(HERE, "color_space_scratch.py"))
    ap.add_argument("--out-csv", default=os.path.join(HERE, "quantitative_results.csv"))
    ap.add_argument("--per-image-csv", default=os.path.join(HERE, "per_image_results.csv"))
    a = ap.parse_args()
    if a.cmd == "baselines":
        run_baselines(a.test_dir, a.results_dir, a.datasets)
    elif a.cmd == "scratch":
        run_scratch(a.test_dir, a.results_dir, a.datasets, a.tv1_file)
    else:
        run_evaluate(a.test_dir, a.results_dir, a.datasets, set(a.gt_mean_datasets),
                     a.out_csv, a.per_image_csv)


if __name__ == "__main__":
    sys.exit(main())
