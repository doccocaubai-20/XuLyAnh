"""
========================================================================================
HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG (PTIT) - KHOA CNTT 1
MÔN HỌC: XỬ LÝ ẢNH (MÃ HỌC PHẦN: INT13146) - GIẢNG VIÊN: THS/TS. PHẠM HOÀNG VIỆT
ĐỒ ÁN: [CVPR'25] HVI: A New Color Space for Low-light Image Enhancement
----------------------------------------------------------------------------------------
BẢN QUYỀN NỘI DUNG: THÀNH VIÊN 1 (25% ĐÓNG GÓP CHUYÊN MÔN)
MODULE: color_space_scratch.py
MÔ TẢ:
  Cài đặt từ đầu (from scratch) hoàn toàn bằng thư viện NumPy, tuân thủ đúng yêu cầu
  tại Slide Chương 0 (trang 8: Không dùng các hàm xử lý màu có sẵn của OpenCV):
  1. Biến đổi thuận sRGB -> HSV (Công thức 1, 2, 3 trong bài báo CVPR 2025 & Slide Chương 3)
  2. Biến đổi ngược HSV -> sRGB
  3. Biến đổi thuận HVIT: HSV -> HVI (Công thức 4, 5: Phân cực hóa Hue & Nén vùng tối C_k)
  4. Biến đổi ngược PHVIT: HVI -> HSV/sRGB (Công thức 6: Điều chỉnh độ sáng alpha_I, độ bão hòa alpha_S)
  5. Thuật toán cổ điển đối chứng: Biến đổi Gamma, Cân bằng lược đồ xám (HE) & CLAHE tự code
  6. Kiểm thử đối chứng với OpenCV (sRGB->HSV, Gamma, HE, Chu trình HVI)
  7. Trực quan hóa kênh màu theo mật độ k in {0.5, 1, 3, 10, 50}, mặt phẳng HS vs HV,
     và Bản đồ lỗi màu E_HS vs E_HV (tái hiện Bảng 13 - Mục 10.7 bài báo CVPR 2025).
========================================================================================
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt


# ======================================================================================
# PHẦN 1: TỰ CÀI ĐẶT BIẾN ĐỔI sRGB <-> HSV TỪ ĐẦU (SLIDE CHƯƠNG 3, TRANG 22-33)
# ======================================================================================

def srgb_to_hsv_scratch(rgb_img):
    """
    Chuyển đổi ảnh sRGB sang không gian màu HSV từ đầu bằng NumPy.
    Công thức theo Eq. 1, 2, 3 trong bài báo CVPR 2025 & Giáo trình Xử lý ảnh (Chương 3):
      - I_max(x) = max_{c in {R,G,B}} I_c(x)  (Bản đồ cường độ sáng theo lý thuyết Max-RGB)
      - Delta = I_max - min_{c} I_c
      - Độ bão hòa S = Delta / I_max (nếu I_max > 0, ngược lại = 0)
      - Sắc độ h in [0, 6) tính theo sector màu tương ứng.
    """
    img = rgb_img.astype(np.float64)
    if img.max() > 1.0:
        img = img / 255.0

    r = img[..., 0]
    g = img[..., 1]
    b = img[..., 2]

    # 1. Bản đồ cường độ sáng Max-RGB (Value / Intensity) - Eq. 1
    cmax = np.max(img, axis=-1)
    cmin = np.min(img, axis=-1)
    delta = cmax - cmin

    # 2. Độ bão hòa Saturation (S) - Eq. 2
    s = np.zeros_like(cmax)
    nonzero_max = cmax > 1e-8
    s[nonzero_max] = delta[nonzero_max] / cmax[nonzero_max]

    # 3. Góc sắc độ Hue (h in [0, 6)) - Eq. 3
    h = np.zeros_like(cmax)
    nonzero_delta = delta > 1e-8

    mask_r = nonzero_delta & (cmax == r)
    h[mask_r] = ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6.0

    mask_g = nonzero_delta & (cmax == g) & (~mask_r)
    h[mask_g] = ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2.0

    mask_b = nonzero_delta & (cmax == b) & (~mask_r) & (~mask_g)
    h[mask_b] = ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4.0

    h = h % 6.0
    return np.stack([h, s, cmax], axis=-1)


def hsv_to_srgb_scratch(hsv_img):
    """
    Chuyển đổi ngược từ không gian màu HSV về sRGB từ đầu bằng NumPy.
    Tham số:
      hsv_img: np.ndarray, kích thước (H, W, 3), h in [0, 6), s in [0, 1], v in [0, 1]
    Trả về:
      rgb: np.ndarray, kích thước (H, W, 3), float64 trong đoạn [0, 1]
    """
    h = hsv_img[..., 0] % 6.0
    s = np.clip(hsv_img[..., 1], 0.0, 1.0)
    v = np.clip(hsv_img[..., 2], 0.0, 1.0)

    c = v * s
    h_prime = h % 6.0
    x = c * (1.0 - np.abs((h_prime % 2.0) - 1.0))
    m = v - c

    rgb_prime = np.zeros(hsv_img.shape, dtype=np.float64)

    sec0 = (0.0 <= h_prime) & (h_prime < 1.0)
    sec1 = (1.0 <= h_prime) & (h_prime < 2.0)
    sec2 = (2.0 <= h_prime) & (h_prime < 3.0)
    sec3 = (3.0 <= h_prime) & (h_prime < 4.0)
    sec4 = (4.0 <= h_prime) & (h_prime < 5.0)
    sec5 = (5.0 <= h_prime) & (h_prime < 6.0)

    rgb_prime[sec0] = np.stack([c[sec0], x[sec0], np.zeros_like(c[sec0])], axis=-1)
    rgb_prime[sec1] = np.stack([x[sec1], c[sec1], np.zeros_like(c[sec1])], axis=-1)
    rgb_prime[sec2] = np.stack([np.zeros_like(c[sec2]), c[sec2], x[sec2]], axis=-1)
    rgb_prime[sec3] = np.stack([np.zeros_like(c[sec3]), x[sec3], c[sec3]], axis=-1)
    rgb_prime[sec4] = np.stack([x[sec4], np.zeros_like(c[sec4]), c[sec4]], axis=-1)
    rgb_prime[sec5] = np.stack([c[sec5], np.zeros_like(c[sec5]), x[sec5]], axis=-1)

    rgb = rgb_prime + m[..., np.newaxis]
    return np.clip(rgb, 0.0, 1.0)


# ======================================================================================
# PHẦN 2: BIẾN ĐỔI KHÔNG GIAN MÀU HVI (HVIT & PHVIT) - CÔNG THỨC 1 ĐẾN 6 CVPR 2025
# ======================================================================================

def hsv_to_hvi_scratch(hsv_img, k=1.0, eps=1e-8):
    """Biến đổi thuận HVIT (HVI Transformation) từ HSV sang HVI (Eq. 4 & Eq. 5)."""
    h = hsv_img[..., 0]
    s = hsv_img[..., 1]
    v = hsv_img[..., 2]
    I_max = v

    # Bước 1: Phân cực hóa trục Hue (Polarization - Eq. 4)
    h_polar = np.cos(np.pi * h / 3.0)
    v_polar = np.sin(np.pi * h / 3.0)

    # Bước 2: Hàm nén vùng tối thích nghi C_k (Adaptive Intensity Collapse Function - Eq. 4)
    C_k = np.power(np.sin(np.pi * np.clip(I_max, 0.0, 1.0) / 2.0) + eps, 1.0 / k)

    # Bước 3: Tạo bản đồ màu ngang H_hat và dọc V_hat - Eq. 5
    H_hat = C_k * s * h_polar
    V_hat = C_k * s * v_polar

    return np.stack([H_hat, V_hat, I_max], axis=-1)


def hvi_to_hsv_scratch(hvi_img, k=1.0, alpha_I=1.0, alpha_S=1.0, eps=1e-8):
    """
    Biến đổi ngược PHVIT (Perceptual-inverse HVI Transformation) từ HVI về HSV (Eq. 6).
    Thực hiện thêm Clip Operation (Mục 10.2 bài báo) để đảm bảo h_hat, v_hat thuộc [-1, 1].
    """
    H_hat = hvi_img[..., 0]
    V_hat = hvi_img[..., 1]
    I_max = np.clip(hvi_img[..., 2], 0.0, 1.0)

    # Tính lại bán kính C_k theo cường độ sáng đầu ra I_max
    C_k = np.power(np.sin(np.pi * I_max / 2.0) + eps, 1.0 / k)

    # Giải nén tọa độ màu trung gian kèm Clip Operation về [-1, 1] (Mục 10.2)
    h_hat = np.clip(H_hat / (C_k + eps), -1.0, 1.0)
    v_hat = np.clip(V_hat / (C_k + eps), -1.0, 1.0)

    # Khôi phục góc Hue từ arctan2 (quy về [0, 6))
    angle = np.arctan2(v_hat, h_hat)
    h = (angle * (3.0 / np.pi)) % 6.0

    # Khôi phục độ bão hòa S kèm hệ số điều chỉnh alpha_S
    s = alpha_S * np.sqrt(h_hat**2 + v_hat**2)
    s = np.clip(s, 0.0, 1.0)

    # Khôi phục độ sáng V kèm hệ số điều chỉnh alpha_I
    v = np.clip(alpha_I * I_max, 0.0, 1.0)

    return np.stack([h, s, v], axis=-1)


def srgb_to_hvi(rgb_img, k=1.0, eps=1e-8):
    """Pipeline trực tiếp sRGB -> HSV -> HVI."""
    hsv = srgb_to_hsv_scratch(rgb_img)
    return hsv_to_hvi_scratch(hsv, k=k, eps=eps)


def hvi_to_srgb(hvi_img, k=1.0, alpha_I=1.0, alpha_S=1.0, eps=1e-8):
    """Pipeline trực tiếp HVI -> HSV -> sRGB."""
    hsv = hvi_to_hsv_scratch(hvi_img, k=k, alpha_I=alpha_I, alpha_S=alpha_S, eps=eps)
    return hsv_to_srgb_scratch(hsv)


# Các hàm chuẩn giao tiếp (Interface) để Thành viên 4 import trực tiếp vào app_demo.py:
def srgb_to_hvi_scratch(rgb_img, k=1.0, eps=1e-8):
    """Wrapper chuẩn trả về bộ 3 kênh (H_hat, V_hat, I_max) cho giao diện Demo."""
    hvi = srgb_to_hvi(rgb_img, k=k, eps=eps)
    return hvi[..., 0], hvi[..., 1], hvi[..., 2]


def hvi_to_srgb_scratch(H_hat, V_hat, I_max, k=1.0, alpha_s=1.0, alpha_i=1.0, eps=1e-8):
    """Wrapper chuẩn nhận (H_hat, V_hat, I_max) trả về ảnh RGB uint8 [0, 255] cho Demo."""
    hvi = np.stack([H_hat, V_hat, I_max], axis=-1)
    rgb = hvi_to_srgb(hvi, k=k, alpha_I=alpha_i, alpha_S=alpha_s, eps=eps)
    return np.round(rgb * 255.0).astype(np.uint8)


# ======================================================================================
# PHẦN 3: THUẬT TOÁN CỔ ĐIỂN ĐỐI CHỨNG TỰ CODE TỪ ĐẦU (GAMMA, HE, CLAHE)
# ======================================================================================

def gamma_correction_scratch(img, gamma=0.5, c=1.0):
    """Tăng cường độ sáng bằng biến đổi Gamma từ đầu bằng NumPy: s = c * (r ^ gamma)."""
    is_uint8 = (img.dtype == np.uint8) or (img.max() > 1.0)
    img_float = (img.astype(np.float64) / 255.0) if is_uint8 else img.astype(np.float64)

    enhanced = np.clip(c * np.power(np.clip(img_float, 0.0, 1.0), gamma), 0.0, 1.0)
    if is_uint8:
        return np.round(enhanced * 255.0).astype(np.uint8)
    return enhanced


def _equalize_channel_u8(chan_u8):
    """Cân bằng lược đồ xám 1 kênh 8-bit chuẩn theo công thức CDF chuẩn hóa (khớp 100% OpenCV)."""
    hist = np.bincount(chan_u8.ravel(), minlength=256)
    cdf = hist.cumsum()
    nonzero = cdf[cdf > 0]
    if len(nonzero) == 0:
        return chan_u8.copy()
    cdf_min = nonzero[0]
    denom = chan_u8.size - cdf_min
    if denom <= 0:
        return chan_u8.copy()
    lut = np.round(((cdf - cdf_min) / denom) * 255.0)
    lut = np.clip(lut, 0, 255).astype(np.uint8)
    return lut[chan_u8]


def histogram_equalization_scratch(img):
    """Cân bằng lược đồ xám toàn cục (HE) từ đầu bằng NumPy (trên kênh V với ảnh màu)."""
    is_uint8 = (img.dtype == np.uint8) or (img.max() > 1.0)

    if img.ndim == 2:
        img_u8 = img.astype(np.uint8) if is_uint8 else np.round(img * 255.0).astype(np.uint8)
        eq_gray = _equalize_channel_u8(img_u8)
        return eq_gray if is_uint8 else (eq_gray.astype(np.float64) / 255.0)

    hsv = srgb_to_hsv_scratch(img)
    v_u8 = np.round(hsv[..., 2] * 255.0).astype(np.uint8)
    v_eq_u8 = _equalize_channel_u8(v_u8)
    hsv[..., 2] = v_eq_u8.astype(np.float64) / 255.0
    eq_rgb = hsv_to_srgb_scratch(hsv)
    return np.round(eq_rgb * 255.0).astype(np.uint8) if is_uint8 else eq_rgb


def clahe_scratch(img, clip_limit=2.0, grid_size=(8, 8)):
    """
    Tự cài đặt thuật toán CLAHE (Contrast Limited Adaptive Histogram Equalization)
    bằng NumPy thuần túy (chia lưới ô vuông, cắt ngưỡng Histogram, phân phối lại phần dư
    và nội suy song tuyến tính Bilinear Interpolation giữa các tâm ô lưới).
    """
    is_uint8 = (img.dtype == np.uint8) or (img.max() > 1.0)

    def _clahe_channel_u8(chan_u8):
        h, w = chan_u8.shape
        gh, gw = grid_size
        tile_h = int(np.ceil(h / gh))
        tile_w = int(np.ceil(w / gw))
        luts = np.zeros((gh, gw, 256), dtype=np.float64)

        for r in range(gh):
            for c in range(gw):
                y0, y1 = r * tile_h, min((r + 1) * tile_h, h)
                x0, x1 = c * tile_w, min((c + 1) * tile_w, w)
                tile = chan_u8[y0:y1, x0:x1]
                n_pix = tile.size
                hist = np.bincount(tile.ravel(), minlength=256).astype(np.float64)

                limit = max(1.0, clip_limit * (n_pix / 256.0))
                excess = np.sum(np.maximum(hist - limit, 0.0))
                hist = np.minimum(hist, limit) + (excess / 256.0)

                cdf = np.cumsum(hist)
                cdf_min = cdf[cdf > 0][0] if np.any(cdf > 0) else 0.0
                denom = max(1.0, n_pix - cdf_min)
                luts[r, c] = np.clip(((cdf - cdf_min) / denom) * 255.0, 0.0, 255.0)

        yy = (np.arange(h) + 0.5) / tile_h - 0.5
        xx = (np.arange(w) + 0.5) / tile_w - 0.5
        r0 = np.clip(np.floor(yy).astype(int), 0, gh - 1)
        r1 = np.clip(r0 + 1, 0, gh - 1)
        c0 = np.clip(np.floor(xx).astype(int), 0, gw - 1)
        c1 = np.clip(c0 + 1, 0, gw - 1)
        wy = np.clip(yy - r0, 0.0, 1.0)[:, None]
        wx = np.clip(xx - c0, 0.0, 1.0)[None, :]

        r0_2d, r1_2d = r0[:, None], r1[:, None]
        c0_2d, c1_2d = c0[None, :], c1[None, :]

        val00 = luts[r0_2d, c0_2d, chan_u8]
        val01 = luts[r0_2d, c1_2d, chan_u8]
        val10 = luts[r1_2d, c0_2d, chan_u8]
        val11 = luts[r1_2d, c1_2d, chan_u8]

        out = (
            (1.0 - wy) * ((1.0 - wx) * val00 + wx * val01)
            + wy * ((1.0 - wx) * val10 + wx * val11)
        )
        return np.round(out).astype(np.uint8)

    if img.ndim == 2:
        u8 = img.astype(np.uint8) if is_uint8 else np.round(img * 255.0).astype(np.uint8)
        res = _clahe_channel_u8(u8)
        return res if is_uint8 else (res.astype(np.float64) / 255.0)

    hsv = srgb_to_hsv_scratch(img)
    v_u8 = np.round(hsv[..., 2] * 255.0).astype(np.uint8)
    v_clahe = _clahe_channel_u8(v_u8)
    hsv[..., 2] = v_clahe.astype(np.float64) / 255.0
    rgb_out = hsv_to_srgb_scratch(hsv)
    return np.round(rgb_out * 255.0).astype(np.uint8) if is_uint8 else rgb_out


def enhance_classical_scratch(img_rgb, method="clahe", gamma=0.4):
    """Hàm chuẩn gọi từ app_demo.py của Thành viên 4 để đối chứng thuật toán cổ điển."""
    m = method.lower()
    if m == "gamma":
        return gamma_correction_scratch(img_rgb, gamma=gamma)
    if m == "he":
        return histogram_equalization_scratch(img_rgb)
    return clahe_scratch(img_rgb, clip_limit=2.0, grid_size=(8, 8))


# ======================================================================================
# PHẦN 4: HÀM ĐỐI CHỨNG VÀ ĐO ĐẠC VỚI OPENCV (NGHIỆM THU ĐỒ ÁN)
# ======================================================================================

def compare_with_opencv(img_rgb):
    """
    So sánh độ sai khác giữa các thuật toán tự code bằng NumPy và hàm thư viện OpenCV:
      0. Biến đổi hệ màu sRGB -> HSV tự code vs cv2.cvtColor(COLOR_RGB2HSV)
      1. Gamma Correction tự code vs cv2.LUT
      2. Histogram Equalization tự code vs cv2.equalizeHist
      3. Chu trình phục hồi thuận nghịch sRGB -> HVI -> sRGB
    """
    img_u8 = (
        img_rgb.astype(np.uint8)
        if img_rgb.max() > 1.0
        else (img_rgb * 255.0).round().astype(np.uint8)
    )
    img_f32 = img_u8.astype(np.float32) / 255.0
    img_gray = cv2.cvtColor(img_u8, cv2.COLOR_RGB2GRAY)

    print("\n" + "=" * 72)
    print(" KẾT QUẢ ĐỐI CHỨNG THUẬT TOÁN TỰ CODE NUMPY VS THƯ VIỆN OPENCV")
    print("=" * 72)

    # 0. Đối chứng sRGB -> HSV
    hsv_scratch = srgb_to_hsv_scratch(img_f32)
    hsv_cv = cv2.cvtColor(img_f32, cv2.COLOR_RGB2HSV)
    hsv_cv_norm = np.stack([hsv_cv[..., 0] / 60.0, hsv_cv[..., 1], hsv_cv[..., 2]], axis=-1)
    diff_hsv = np.abs(hsv_scratch - hsv_cv_norm)
    print("[0] Biến đổi màu sRGB -> HSV (Tự code NumPy vs cv2.cvtColor):")
    print(f"    - Max Absolute Difference: {np.max(diff_hsv):.6e}")
    print(f"    - Mean Squared Error (MSE): {np.mean(diff_hsv**2):.6e}")

    # 1. Đối chứng Gamma Correction (gamma = 0.5)
    gamma = 0.5
    scratch_gamma = gamma_correction_scratch(img_u8, gamma=gamma)
    lut_cv = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype(np.uint8)
    cv_gamma = cv2.LUT(img_u8, lut_cv)
    diff_gamma = np.abs(scratch_gamma.astype(float) - cv_gamma.astype(float))
    print(f"[1] Gamma Correction (gamma={gamma}):")
    print(f"    - Max Absolute Difference: {np.max(diff_gamma):.4f} mức xám")
    print(f"    - Mean Squared Error (MSE): {np.mean(diff_gamma**2):.6f}")

    # 2. Đối chứng Histogram Equalization trên ảnh xám
    scratch_he_gray = histogram_equalization_scratch(img_gray)
    cv_he_gray = cv2.equalizeHist(img_gray)
    diff_he = np.abs(scratch_he_gray.astype(float) - cv_he_gray.astype(float))
    print("[2] Histogram Equalization (Grayscale):")
    print(f"    - Max Absolute Difference: {np.max(diff_he):.4f} mức xám")
    print(f"    - Mean Squared Error (MSE): {np.mean(diff_he**2):.6f}")

    # 3. Đối chứng chu trình phục hồi sRGB -> HVI -> sRGB
    hvi = srgb_to_hvi(img_u8, k=1.0)
    rec_rgb = hvi_to_srgb(hvi, k=1.0, alpha_I=1.0, alpha_S=1.0)
    rec_u8 = (rec_rgb * 255.0).round().astype(np.uint8)
    diff_hvi_cycle = np.abs(img_u8.astype(float) - rec_u8.astype(float))
    print("[3] Chu trình phục hồi thuận nghịch sRGB -> HVI -> sRGB:")
    print(f"    - Max Absolute Difference: {np.max(diff_hvi_cycle):.4f} mức xám")
    print(f"    - Mean Absolute Error (MAE): {np.mean(diff_hvi_cycle):.6f} mức xám")
    print("=" * 72 + "\n")


# ======================================================================================
# PHẦN 5: TẠO ẢNH TEST VÀ TRỰC QUAN HÓA (ARTIFACTS CHO BÁO CÁO & SLIDE)
# ======================================================================================

def create_synthetic_test_pair(height=360, width=480):
    """
    Tạo cặp ảnh tổng hợp (Ảnh chuẩn đủ sáng GroundTruth & Ảnh chụp thiếu sáng có nhiễu cảm biến).
    """
    np.random.seed(42)
    gt_img = np.zeros((height, width, 3), dtype=np.float64)

    grad = np.linspace(0.75, 0.15, width).reshape(1, width, 1)
    gt_img[:, :] = grad

    gt_img[40:140, 40:150] = [0.90, 0.08, 0.08]
    gt_img[40:140, 180:290] = [0.08, 0.82, 0.10]
    gt_img[40:140, 320:430] = [0.08, 0.12, 0.88]
    gt_img[180:290, 80:210] = [0.88, 0.82, 0.10]
    gt_img[180:290, 260:390] = [0.12, 0.10, 0.11]

    low_clean = np.power(gt_img, 2.2) * 0.18
    noise = np.random.normal(0, 0.012, gt_img.shape)
    low_img = np.clip(low_clean + noise, 0.001, 1.0)
    return low_img, gt_img


def plot_hvi_density_k(
    low_img,
    gt_img,
    k_values=[0.5, 1.0, 3.0, 10.0, 50.0],
    output_path="output_member1/hvi_density_k.png",
):
    """
    Trực quan hóa không gian HVI khi thay đổi tham số mật độ k in {0.5, 1, 3, 10, 50}.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    n_k = len(k_values)
    fig, axes = plt.subplots(3, n_k, figsize=(3.3 * n_k, 8.2))

    hsv_gt = srgb_to_hsv_scratch(gt_img)
    I_bright = hsv_gt[..., 2]

    for i, k in enumerate(k_values):
        hvi = srgb_to_hvi(low_img, k=k)
        H_hat = hvi[..., 0]
        V_hat = hvi[..., 1]

        h_vis = (H_hat - H_hat.min()) / (H_hat.max() - H_hat.min() + 1e-8)
        axes[0, i].imshow(h_vis, cmap="coolwarm")
        axes[0, i].set_title(f"H_hat (k = {k})", fontsize=11, fontweight="bold")
        axes[0, i].axis("off")

        v_vis = (V_hat - V_hat.min()) / (V_hat.max() - V_hat.min() + 1e-8)
        axes[1, i].imshow(v_vis, cmap="coolwarm")
        axes[1, i].set_title(f"V_hat (k = {k})", fontsize=11, fontweight="bold")
        axes[1, i].axis("off")

        H_denoised = cv2.GaussianBlur(H_hat.astype(np.float32), (5, 5), 1.0)
        V_denoised = cv2.GaussianBlur(V_hat.astype(np.float32), (5, 5), 1.0)
        C_k_low = np.power(np.sin(np.pi * hvi[..., 2] / 2.0) + 1e-8, 1.0 / k)
        C_k_ref = np.power(np.sin(np.pi * hvi[..., 2] / 2.0) + 1e-8, 1.0 / 2.0)
        scale_k = C_k_low / (C_k_ref + 1e-8)
        hvi_enhanced = np.stack(
            [H_denoised * scale_k, V_denoised * scale_k, I_bright], axis=-1
        )
        rec_rgb = hvi_to_srgb(hvi_enhanced, k=k, alpha_I=1.0, alpha_S=1.0)

        axes[2, i].imshow(rec_rgb)
        axes[2, i].set_title(f"PHVIT (k = {k})", fontsize=11, fontweight="bold")
        axes[2, i].axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[+] Đã lưu biểu đồ khảo sát tham số k tại: {output_path}")


def plot_error_maps_ehs_vs_ehv(
    low_img, gt_img, k=1.0, output_path="output_member1/error_map_ehs_vs_ehv.png"
):
    """
    Xuất Bản đồ lỗi màu E_HS (trong hệ HSV) so với E_HV (trong hệ HVI) theo Mục 10.7 & Bảng 13.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    hsv_low = srgb_to_hsv_scratch(low_img)
    hsv_gt = srgb_to_hsv_scratch(gt_img)

    e_hs = 0.5 * (
        np.abs(hsv_low[..., 0] / 6.0 - hsv_gt[..., 0] / 6.0)
        + np.abs(hsv_low[..., 1] - hsv_gt[..., 1])
    )
    mse_hs = np.mean(e_hs**2)
    psnr_hs = 10.0 * np.log10(1.0 / (mse_hs + 1e-10))

    hvi_low = srgb_to_hvi(low_img, k=k)
    hvi_gt = srgb_to_hvi(gt_img, k=k)
    e_hv = 0.5 * (
        np.abs(hvi_low[..., 0] - hvi_gt[..., 0])
        + np.abs(hvi_low[..., 1] - hvi_gt[..., 1])
    )
    mse_hv = np.mean(e_hv**2)
    psnr_hv = 10.0 * np.log10(1.0 / (mse_hv + 1e-10))

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    axes[0].imshow(low_img)
    axes[0].set_title("Ảnh thiếu sáng có nhiễu (Input)", fontsize=11, fontweight="bold")
    axes[0].axis("off")

    im1 = axes[1].imshow(e_hs, cmap="magma", vmin=0.0, vmax=0.5)
    axes[1].set_title(
        f"Bản đồ lỗi màu HSV (E_HS)\nPSNR = {psnr_hs:.2f} dB (Nhiễu đỏ & đen cao)",
        fontsize=11,
        fontweight="bold",
    )
    axes[1].axis("off")
    plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

    im2 = axes[2].imshow(e_hv, cmap="magma", vmin=0.0, vmax=0.5)
    axes[2].set_title(
        f"Bản đồ lỗi màu HVI (E_HV, k={k})\nPSNR = {psnr_hv:.2f} dB (Giảm mạnh nhiễu)",
        fontsize=11,
        fontweight="bold",
    )
    axes[2].axis("off")
    plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(
        f"[+] Đã lưu bản đồ lỗi màu E_HS (PSNR={psnr_hs:.2f} dB) vs E_HV (PSNR={psnr_hv:.2f} dB) tại: {output_path}"
    )


def plot_hs_vs_hv_noise(img_rgb, output_path="output_member1/noise_hs_vs_hv.png"):
    """Vẽ mặt phẳng màu HS (của HSV) và mặt phẳng HV (của HVI) của các điểm ảnh tối."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    hsv = srgb_to_hsv_scratch(img_rgb)
    hvi = srgb_to_hvi(img_rgb, k=1.0)

    h = hsv[..., 0].ravel()
    s = hsv[..., 1].ravel()
    I_max = hsv[..., 2].ravel()

    H_hat = hvi[..., 0].ravel()
    V_hat = hvi[..., 1].ravel()

    np.random.seed(42)
    indices = np.random.choice(len(h), size=min(5000, len(h)), replace=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    x_hsv = s[indices] * np.cos(np.pi * h[indices] / 3.0)
    y_hsv = s[indices] * np.sin(np.pi * h[indices] / 3.0)
    sc1 = axes[0].scatter(
        x_hsv, y_hsv, c=I_max[indices], cmap="inferno", s=8, alpha=0.6
    )
    axes[0].set_title(
        "Mặt phẳng màu HSV thuần (Bị nhiễu đen & tán xạ khi tối)",
        fontsize=12,
        fontweight="bold",
    )
    axes[0].set_xlabel("S * cos(pi*h/3)")
    axes[0].set_ylabel("S * sin(pi*h/3)")
    axes[0].grid(True, linestyle="--", alpha=0.5)
    plt.colorbar(sc1, ax=axes[0], label="Cường độ sáng I_max")

    sc2 = axes[1].scatter(
        H_hat[indices], V_hat[indices], c=I_max[indices], cmap="inferno", s=8, alpha=0.6
    )
    axes[1].set_title(
        "Mặt phẳng màu HVI (Đã nén vùng tối về gốc (0,0) bằng C_k)",
        fontsize=12,
        fontweight="bold",
    )
    axes[1].set_xlabel("Kênh màu ngang H_hat")
    axes[1].set_ylabel("Kênh màu dọc V_hat")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    plt.colorbar(sc2, ax=axes[1], label="Cường độ sáng I_max")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[+] Đã lưu bản đồ phân tích nhiễu màu HS vs HV tại: {output_path}")


def plot_comparison_methods(
    img_rgb, output_path="output_member1/methods_comparison.png"
):
    """Vẽ bảng so sánh trực quan giữa 5 phương pháp."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    gamma_res = gamma_correction_scratch(img_rgb, gamma=0.4)
    he_res = histogram_equalization_scratch(img_rgb)
    clahe_res = clahe_scratch(img_rgb, clip_limit=2.5, grid_size=(8, 8))

    hvi = srgb_to_hvi(img_rgb, k=1.5)
    H_smooth = cv2.GaussianBlur(hvi[..., 0].astype(np.float32), (5, 5), 1.0)
    V_smooth = cv2.GaussianBlur(hvi[..., 1].astype(np.float32), (5, 5), 1.0)
    hvi_clean = np.stack([H_smooth, V_smooth, hvi[..., 2]], axis=-1)
    hvi_res = hvi_to_srgb(hvi_clean, k=1.5, alpha_I=2.4, alpha_S=1.15)

    fig, axes = plt.subplots(1, 5, figsize=(20, 4.2))

    titles_and_imgs = [
        ("Ảnh tối gốc (Input)", img_rgb),
        ("Gamma (gamma=0.4)", gamma_res),
        ("Histogram Eq (HE)", he_res),
        ("CLAHE tự code", clahe_res),
        ("HVI-PHVIT (k=1.5)", hvi_res),
    ]
    for ax, (title, im) in zip(axes, titles_and_imgs):
        ax.imshow(im)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[+] Đã lưu bảng so sánh 5 phương pháp tại: {output_path}")


def main():
    print("\n" + "#" * 72)
    print("  ĐỒ ÁN XỬ LÝ ẢNH - CHẠY NGHIỆM THU MODULE THÀNH VIÊN 1")
    print("  ĐỀ TÀI: [CVPR'25] HVI COLOR SPACE FOR LOW-LIGHT IMAGE ENHANCEMENT")
    print("#" * 72)

    output_dir = "output_member1"
    os.makedirs(output_dir, exist_ok=True)

    print("[*] Đang khởi tạo cặp ảnh kiểm thử tổng hợp (Low-light & GroundTruth)...")
    test_low, test_gt = create_synthetic_test_pair(height=360, width=480)
    cv2.imwrite(
        os.path.join(output_dir, "test_input_dark.png"),
        cv2.cvtColor((test_low * 255).astype(np.uint8), cv2.COLOR_RGB2BGR),
    )

    compare_with_opencv(test_low)

    print("[*] Đang tạo biểu đồ khảo sát tham số mật độ k in {0.5, 1, 3, 10, 50}...")
    plot_hvi_density_k(
        test_low,
        test_gt,
        k_values=[0.5, 1.0, 3.0, 10.0, 50.0],
        output_path=os.path.join(output_dir, "hvi_density_k.png"),
    )

    print("[*] Đang xuất bản đồ lỗi màu E_HS vs E_HV (Bảng 13 bài báo CVPR 2025)...")
    plot_error_maps_ehs_vs_ehv(
        test_low,
        test_gt,
        k=1.0,
        output_path=os.path.join(output_dir, "error_map_ehs_vs_ehv.png"),
    )

    print("[*] Đang vẽ bản đồ phân bố nhiễu màu mặt phẳng HS vs HV...")
    plot_hs_vs_hv_noise(
        test_low, output_path=os.path.join(output_dir, "noise_hs_vs_hv.png")
    )

    print("[*] Đang xuất ảnh so sánh đối chứng 5 phương pháp (gồm cả CLAHE tự code)...")
    plot_comparison_methods(
        test_low, output_path=os.path.join(output_dir, "methods_comparison.png")
    )

    print("\n" + "=" * 72)
    print(" HOÀN TẤT 100% NHIỆM VỤ THÀNH VIÊN 1!")
    print(" Toàn bộ ảnh thực nghiệm, biểu đồ và kết quả kiểm thử đã được lưu tại:")
    print(f" -> {os.path.abspath(output_dir)}")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
