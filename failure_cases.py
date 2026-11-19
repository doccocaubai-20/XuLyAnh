"""failure_cases.py - phân tích 4 trường hợp thất bại (Thành viên 3).

Mỗi ca có thư mục test_cases/failure_cases/<ca>/ chứa ảnh input (và gt nếu có), và
results/failure_cases/<ca>/<METHOD>/ chứa ảnh đầu ra cùng tên file. Các lệnh:

  panel      Ghép ảnh [input | phương pháp 1 | phương pháp 2 | ... | gt] để đưa vào báo cáo.
               python failure_cases.py panel --case case2_k_alpha --methods opencv_clahe HVI-CIDNet

  metrics    Số đo khách quan cho từng ảnh của một ca, ghi failure_case_metrics.csv:
               sat_pct     % điểm ảnh cháy sáng (min(R,G,B) >= 250)           -> ca 4
               dark_detail độ biến thiên Laplacian trong vùng gốc rất tối      -> ca 3
               rg_ratio, bg_ratio  tỉ lệ kênh R/G, B/G trung bình (so với gt)  -> ca 1
               noise_dark  độ lệch chuẩn của nền ảnh ở vùng tối                -> ca 2
               python failure_cases.py metrics --case case4_backlit --methods HVI-CIDNet

  k_sweep    Tái hiện Hình 9 của bài báo bằng NumPy (KHÔNG cần mạng): bản đồ HV của một ảnh
             ở k = 1, 3, 10, 50 và độ lệch chuẩn của H_hat, V_hat trong vùng tối.
               python failure_cases.py k_sweep --image test_cases/LOLv1/input/22.png

Ghi chú về k: ở mọi cường độ I trong (0, 1), sin(pi*I/2) < 1 nên C_k = sin(pi*I/2)^(1/k)
tăng khi k tăng, tức là bán kính mặt phẳng HV ở vùng tối to ra và nhiễu màu ít bị nén.
Đây là suy luận từ công thức, trùng với nhận xét ở Hình 7 và Hình 9 của bài báo.
"""
import argparse
import csv
import os
import sys

import cv2
import numpy as np

from measure import list_images, read_rgb

import asciiout  # noqa: F401  (in man hinh khong dau)

HERE = os.path.dirname(os.path.abspath(__file__))
SAT_THR = 250
DARK_THR = 20  # ngưỡng xám (0-255) của ảnh input để coi là "vùng rất tối"


# ---------- HVI chuyển thuận (NumPy), theo Eq. 1-5 của bài báo ----------
def rgb_to_hvi(img01, k=1.0, eps=1e-8):
    r, g, b = img01[..., 0], img01[..., 1], img01[..., 2]
    v = img01.max(-1)
    d = v - img01.min(-1)
    s = np.where(v > 0, d / np.maximum(v, eps), 0.0)
    dd = np.maximum(d, eps)
    h = np.where(v == r, ((g - b) / dd) % 6,
                 np.where(v == g, 2 + (b - r) / dd, 4 + (r - g) / dd))
    h = np.where(s == 0, 0.0, h)
    hh, vv = np.cos(np.pi * h / 3), np.sin(np.pi * h / 3)
    ck = (np.sin(np.pi * v / 2) + eps) ** (1.0 / k)
    return np.stack([ck * s * hh, ck * s * vv, v], -1)


def cmd_k_sweep(image_path, out_dir, ks=(1, 3, 10, 50), dark_i=0.1):
    os.makedirs(out_dir, exist_ok=True)
    img = read_rgb(image_path).astype(np.float64) / 255.0
    stem = os.path.splitext(os.path.basename(image_path))[0]
    dark = img.max(-1) < dark_i
    rows, tiles = [], []
    for k in ks:
        hvi = rgb_to_hvi(img, k)
        # Ánh xạ H_hat, V_hat từ [-1, 1] sang [0, 255] để xem; kênh thứ 3 = 0.5 (xám)
        vis = np.stack([(hvi[..., 0] + 1) / 2, (hvi[..., 1] + 1) / 2, np.full(dark.shape, 0.5)], -1)
        vis8 = (vis.clip(0, 1) * 255).astype(np.uint8)
        cv2.imwrite(os.path.join(out_dir, f"{stem}_k{k}_HVmap.png"), cv2.cvtColor(vis8, cv2.COLOR_RGB2BGR))
        tile = vis8.copy()
        cv2.putText(tile, f"k={k}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        tiles.append(tile)
        sd_h = float(hvi[..., 0][dark].std()) if dark.any() else float("nan")
        sd_v = float(hvi[..., 1][dark].std()) if dark.any() else float("nan")
        rows.append({"image": stem, "k": k, "pct_dark_pixels": round(float(100 * dark.mean()), 2),
                     "std_Hhat_dark": round(sd_h, 5), "std_Vhat_dark": round(sd_v, 5)})
        print(rows[-1])
    cv2.imwrite(os.path.join(out_dir, f"{stem}_k_sweep_strip.png"),
                cv2.cvtColor(np.concatenate(tiles, 1), cv2.COLOR_RGB2BGR))
    csv_path = os.path.join(out_dir, f"{stem}_k_sweep.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Đã ghi {out_dir}")


def _find(folder, stem):
    """Tìm ảnh theo tên (bỏ đuôi) trong thư mục, bất kể đuôi .png/.jpg/.JPG."""
    if os.path.isdir(folder):
        for f in list_images(folder):
            if os.path.splitext(f)[0] == stem:
                return os.path.join(folder, f)
    return None


# ---------- ghép ảnh ----------
def _label(img_rgb, text):
    out = img_rgb.copy()
    cv2.rectangle(out, (0, 0), (min(out.shape[1], 14 * len(text) + 12), 30), (0, 0, 0), -1)
    cv2.putText(out, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    return out


def _fit(img, h):
    w = int(round(img.shape[1] * h / img.shape[0]))
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)


def cmd_panel(case, methods, test_dir, results_dir, out_dir, height=360):
    in_dir = os.path.join(test_dir, "failure_cases", case, "input")
    gt_dir = os.path.join(test_dir, "failure_cases", case, "gt")
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    for f in list_images(in_dir):
        stem = os.path.splitext(f)[0]
        tiles = [_label(_fit(read_rgb(os.path.join(in_dir, f)), height), "input")]
        for m in methods:
            p = _find(os.path.join(results_dir, "failure_cases", case, m), stem)
            if p:
                tiles.append(_label(_fit(read_rgb(p), height), m))
            else:
                print(f"[thiếu] ảnh của {m} cho {stem}")
        if os.path.isdir(gt_dir):
            g = [x for x in list_images(gt_dir) if os.path.splitext(x)[0] == stem]
            if g:
                tiles.append(_label(_fit(read_rgb(os.path.join(gt_dir, g[0])), height), "gt"))
        panel = np.concatenate(tiles, 1)
        cv2.imwrite(os.path.join(out_dir, f"{case}_{stem}.png"), cv2.cvtColor(panel, cv2.COLOR_RGB2BGR))
        n += 1
    print(f"Đã ghép {n} bảng ảnh -> {out_dir}")


# ---------- số đo ----------
def img_metrics(out, inp, gt=None):
    gray_in = cv2.cvtColor(inp, cv2.COLOR_RGB2GRAY)
    if out.shape[:2] != inp.shape[:2]:
        raise ValueError("ảnh ra và ảnh input khác kích thước")
    mask = gray_in <= DARK_THR
    gray_out = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY).astype(np.float64)
    lap = cv2.Laplacian(gray_out, cv2.CV_64F)
    f = out.astype(np.float64)
    m = {
        "sat_pct": 100.0 * float((out.min(-1) >= SAT_THR).mean()),
        "dark_pixels_pct": 100.0 * float(mask.mean()),
        "dark_detail": float(lap[mask].var()) if mask.sum() > 10 else float("nan"),
        "noise_dark": float(gray_out[mask].std()) if mask.sum() > 10 else float("nan"),
        "rg_ratio": float(f[..., 0].mean() / max(f[..., 1].mean(), 1e-8)),
        "bg_ratio": float(f[..., 2].mean() / max(f[..., 1].mean(), 1e-8)),
    }
    if gt is not None:
        g = gt.astype(np.float64)
        m["rg_ratio_gt"] = float(g[..., 0].mean() / max(g[..., 1].mean(), 1e-8))
        m["bg_ratio_gt"] = float(g[..., 2].mean() / max(g[..., 1].mean(), 1e-8))
    return m


def cmd_metrics(case, methods, test_dir, results_dir, out_csv):
    in_dir = os.path.join(test_dir, "failure_cases", case, "input")
    gt_dir = os.path.join(test_dir, "failure_cases", case, "gt")
    rows = []
    for f in list_images(in_dir):
        stem = os.path.splitext(f)[0]
        inp = read_rgb(os.path.join(in_dir, f))
        gt = None
        if os.path.isdir(gt_dir):
            g = [x for x in list_images(gt_dir) if os.path.splitext(x)[0] == stem]
            gt = read_rgb(os.path.join(gt_dir, g[0])) if g else None
        for m in ["input"] + list(methods):
            if m == "input":
                out = inp
            else:
                p = _find(os.path.join(results_dir, "failure_cases", case, m), stem)
                if not p:
                    print(f"[thiếu] ảnh của {m} cho {stem}")
                    continue
                out = read_rgb(p)
            r = {"case": case, "image": stem, "method": m}
            r.update({k: round(v, 4) for k, v in img_metrics(out, inp, gt).items()})
            rows.append(r)
    if not rows:
        print("Không có dữ liệu để đo.")
        return
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    mode = "a" if os.path.exists(out_csv) else "w"
    with open(out_csv, mode, newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval="")
        if mode == "w":
            w.writeheader()
        w.writerows(rows)
    print(f"Đã ghi {len(rows)} dòng vào {out_csv}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("cmd", choices=["panel", "metrics", "k_sweep"])
    ap.add_argument("--case", help="tên thư mục ca, vd case1_color_shift")
    ap.add_argument("--methods", nargs="*", default=["HVI-CIDNet"])
    ap.add_argument("--image", help="ảnh cho k_sweep")
    ap.add_argument("--test-dir", default=os.path.join(HERE, "test_cases"))
    ap.add_argument("--results-dir", default=os.path.join(HERE, "results"))
    ap.add_argument("--out-dir", default=os.path.join(HERE, "failure_figures"))
    ap.add_argument("--out-csv", default=os.path.join(HERE, "failure_case_metrics.csv"))
    a = ap.parse_args()
    if a.cmd == "k_sweep":
        if not a.image:
            ap.error("k_sweep cần --image")
        return cmd_k_sweep(a.image, a.out_dir)
    if not a.case:
        ap.error("cần --case")
    if a.cmd == "panel":
        return cmd_panel(a.case, a.methods, a.test_dir, a.results_dir, a.out_dir)
    return cmd_metrics(a.case, a.methods, a.test_dir, a.results_dir, a.out_csv)


if __name__ == "__main__":
    sys.exit(main())
