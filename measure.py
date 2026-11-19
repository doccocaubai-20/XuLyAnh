"""measure.py - các hàm đo chất lượng ảnh cho phần Thành viên 3.

Có thể dùng như thư viện (eval.py import từ đây) hoặc chạy trực tiếp:

  # Có ảnh chuẩn (paired): PSNR, SSIM, LPIPS (+ NIQE, BRISQUE nếu cài pyiqa)
  python measure.py --pred results/LOLv1/HVI-CIDNet --gt test_cases/LOLv1/gt --gt-mean

  # Không có ảnh chuẩn (unpaired): chỉ NIQE, BRISQUE
  python measure.py --pred results/DICM/HVI-CIDNet --noref

Cài thêm khi cần LPIPS / NIQE / BRISQUE (cần mạng):  pip install torch lpips pyiqa
Thiếu thư viện nào thì chỉ số đó là NaN và có cảnh báo, các chỉ số còn lại vẫn chạy.
"""
import argparse
import csv
import math
import os
import sys
import warnings

import cv2
import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

import asciiout  # noqa: F401  (in man hinh khong dau)

IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
NAN = float("nan")


def list_images(folder):
    return sorted(f for f in os.listdir(folder)
                  if os.path.splitext(f)[1].lower() in IMG_EXT)


def read_rgb(path):
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def gt_mean_align(out, gt):
    """Chuẩn hóa độ sáng theo 'GT Mean' (bài báo, Mục 10.2).

    Đưa ảnh ra và ảnh chuẩn về ảnh xám, nhân ảnh ra với q = mean(gt) / mean(out)
    rồi clip về [0, 255], để độ sáng trung bình hai ảnh bằng nhau.

    Lưu ý: Công thức (21) trong bài báo ghi q = mean(out) / mean(gt) và I_q = q * I_out.
    Viết đúng như vậy thì độ sáng trung bình sau chỉnh KHÔNG khớp ảnh chuẩn, trái với
    mục đích đã nêu ("aligns the overall brightness of the output image with the
    GroundTruth"). Ở đây dùng chiều q = mean(gt) / mean(out), là cách các phương pháp
    LLIE khác (LLFlow, RetinexFormer...) cài đặt.
    """
    g_out = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY).astype(np.float64).mean()
    g_gt = cv2.cvtColor(gt, cv2.COLOR_RGB2GRAY).astype(np.float64).mean()
    q = g_gt / max(g_out, 1e-8)
    return np.clip(np.rint(out.astype(np.float64) * q), 0, 255).astype(np.uint8)


def psnr(out, gt):
    return float(peak_signal_noise_ratio(gt, out, data_range=255))


def ssim(out, gt):
    # Cấu hình Gaussian 11x11, sigma = 1.5 (SSIM gốc của Wang et al.)
    return float(structural_similarity(
        gt, out, channel_axis=2, data_range=255,
        gaussian_weights=True, sigma=1.5, use_sample_covariance=False))


class DeepMetrics:
    """LPIPS (AlexNet) và NIQE/BRISQUE (pyiqa) - nạp lười, thiếu thư viện thì NaN."""

    def __init__(self, use_lpips=True, use_iqa=True, device=None):
        self.lpips_fn = None
        self.niqe_fn = None
        self.brisque_fn = None
        self.torch = None
        self.device = device
        if not (use_lpips or use_iqa):
            return
        try:
            import torch
            self.torch = torch
            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        except Exception:
            warnings.warn("Chưa cài torch -> LPIPS, NIQE, BRISQUE sẽ là NaN.")
            return
        if use_lpips:
            try:
                import lpips
                self.lpips_fn = lpips.LPIPS(net="alex", verbose=False).to(self.device).eval()
            except Exception:
                warnings.warn("Chưa cài lpips (pip install lpips) -> LPIPS là NaN.")
        if use_iqa:
            try:
                import pyiqa
                self.niqe_fn = pyiqa.create_metric("niqe", device=self.device)
                self.brisque_fn = pyiqa.create_metric("brisque", device=self.device)
            except Exception:
                warnings.warn("Chưa cài pyiqa (pip install pyiqa) -> NIQE, BRISQUE là NaN.")

    def _tensor(self, img, signed=False):
        t = self.torch.from_numpy(img.astype(np.float32) / 255.0).permute(2, 0, 1)[None]
        if signed:
            t = t * 2 - 1
        return t.to(self.device)

    def lpips(self, out, gt):
        if self.lpips_fn is None:
            return NAN
        with self.torch.no_grad():
            return float(self.lpips_fn(self._tensor(out, True), self._tensor(gt, True)).item())

    def niqe(self, out):
        if self.niqe_fn is None:
            return NAN
        with self.torch.no_grad():
            return float(self.niqe_fn(self._tensor(out)).item())

    def brisque(self, out):
        if self.brisque_fn is None:
            return NAN
        with self.torch.no_grad():
            return float(self.brisque_fn(self._tensor(out)).item())


def measure_pair(out, gt, deep, use_gt_mean=False):
    """Đo một cặp (ảnh ra, ảnh chuẩn). Trả dict PSNR, SSIM, LPIPS, NIQE, BRISQUE."""
    if out.shape != gt.shape:
        raise ValueError(f"Kích thước ảnh ra {out.shape} khác ảnh chuẩn {gt.shape}")
    if use_gt_mean:
        out = gt_mean_align(out, gt)
    return {"psnr": psnr(out, gt), "ssim": ssim(out, gt), "lpips": deep.lpips(out, gt),
            "niqe": deep.niqe(out), "brisque": deep.brisque(out)}


def measure_noref(out, deep):
    return {"psnr": NAN, "ssim": NAN, "lpips": NAN,
            "niqe": deep.niqe(out), "brisque": deep.brisque(out)}


def measure_folder(pred_dir, gt_dir=None, use_gt_mean=False, deep=None):
    """Đo cả thư mục. Ghép ảnh theo tên file (bỏ đuôi). Trả list dict theo từng ảnh."""
    deep = deep or DeepMetrics()
    rows = []
    gt_map = {}
    if gt_dir:
        gt_map = {os.path.splitext(f)[0]: f for f in list_images(gt_dir)}
    for f in list_images(pred_dir):
        stem = os.path.splitext(f)[0]
        out = read_rgb(os.path.join(pred_dir, f))
        if gt_dir:
            if stem not in gt_map:
                raise FileNotFoundError(f"Không có ảnh chuẩn tên '{stem}' trong {gt_dir}")
            gt = read_rgb(os.path.join(gt_dir, gt_map[stem]))
            m = measure_pair(out, gt, deep, use_gt_mean)
        else:
            m = measure_noref(out, deep)
        m["image"] = f
        rows.append(m)
    if gt_dir and not rows:
        raise FileNotFoundError(f"Thư mục {pred_dir} không có ảnh")
    return rows


def summarize(rows):
    """Trung bình từng chỉ số, bỏ qua NaN. Chỉ số nào toàn NaN thì trả NaN."""
    out = {}
    for k in ("psnr", "ssim", "lpips", "niqe", "brisque"):
        vals = [r[k] for r in rows if not math.isnan(r[k])]
        out[k] = float(np.mean(vals)) if vals else NAN
    out["n_images"] = len(rows)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--pred", required=True, help="thư mục ảnh đã làm sáng")
    ap.add_argument("--gt", help="thư mục ảnh chuẩn (bỏ trống nếu dùng --noref)")
    ap.add_argument("--noref", action="store_true", help="chỉ đo NIQE/BRISQUE (không có ảnh chuẩn)")
    ap.add_argument("--gt-mean", action="store_true", help="chuẩn hóa độ sáng theo GT Mean")
    ap.add_argument("--out-csv", help="ghi kết quả từng ảnh ra CSV")
    a = ap.parse_args()
    if not a.noref and not a.gt:
        ap.error("cần --gt, hoặc dùng --noref")
    rows = measure_folder(a.pred, None if a.noref else a.gt, a.gt_mean)
    s = summarize(rows)
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()})
    if a.out_csv:
        with open(a.out_csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["image", "psnr", "ssim", "lpips", "niqe", "brisque"])
            w.writeheader()
            for r in rows:
                w.writerow({k: r[k] for k in w.fieldnames})


if __name__ == "__main__":
    sys.exit(main())
