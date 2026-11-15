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
  5. Thuật toán cổ điển đối chứng: Biến đổi Gamma (Slide Chương 2) & Cân bằng lược đồ xám (HE)
  6. Kiểm thử đối chứng với OpenCV (MSE, Max Absolute Difference)
  7. Trực quan hóa các kênh màu theo mật độ k in {0.5, 1, 3, 10, 50} và mặt phẳng màu HS vs HV.
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
    
    Tham số:
      rgb_img: np.ndarray, kích thước (H, W, 3), kiểu float [0, 1] hoặc uint8 [0, 255]
    Trả về:
      hsv: np.ndarray, kích thước (H, W, 3), float64
           h in [0, 6), s in [0, 1], v in [0, 1]
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
    
    # TH1: cmax == R -> h = ((G - B) / delta) mod 6
    mask_r = nonzero_delta & (cmax == r)
    h[mask_r] = ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6.0
    
    # TH2: cmax == G -> h = 2 + (B - R) / delta
    mask_g = nonzero_delta & (cmax == g) & (~mask_r)
    h[mask_g] = ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2.0
    
    # TH3: cmax == B -> h = 4 + (R - G) / delta
    mask_b = nonzero_delta & (cmax == b) & (~mask_r) & (~mask_g)
    h[mask_b] = ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4.0
    
    # Đảm bảo h thuộc [0, 6)
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
    """
    Biến đổi thuận HVIT (HVI Transformation) từ HSV sang HVI.
    Giải quyết 2 nhược điểm cốt lõi của HSV trong ảnh thiếu sáng:
      1. Nhiễu đứt gãy màu đỏ: Phân cực hóa trục Hue thành h_polar = cos(pi*h/3), v_polar = sin(pi*h/3)
      2. Nhiễu mặt phẳng đen: Nén vùng tối thích nghi bằng hàm C_k(x) = [sin(pi*I_max/2) + eps]^(1/k)
    
    Công thức theo Eq. 4 & Eq. 5:
      H_hat = C_k * S * h_polar
      V_hat = C_k * S * v_polar
      I_max = V
    
    Tham số:
      hsv_img: np.ndarray, kích thước (H, W, 3), h in [0, 6), s in [0, 1], v in [0, 1]
      k: float > 0, tham số mật độ nén vùng tối (mặc định k = 1.0)
      eps: float, hằng số cực nhỏ tránh chia cho 0 và nổ gradient
    Trả về:
      hvi: np.ndarray, kích thước (H, W, 3) gồm (H_hat, V_hat, I_max)
    """
    h = hsv_img[..., 0]
    s = hsv_img[..., 1]
    v = hsv_img[..., 2]
    I_max = v
    
    # Bước 1: Phân cực hóa trục Hue (Polarization - Eq. 4)
    # Vì h in [0, 6], góc theta = h * (2*pi / 6) = pi * h / 3
    # Khi h = 0 và h = 6, tọa độ cực đều là (1, 0) -> Xóa bỏ đứt gãy màu đỏ!
    h_polar = np.cos(np.pi * h / 3.0)
    v_polar = np.sin(np.pi * h / 3.0)
    
    # Bước 2: Hàm nén vùng tối thích nghi C_k (Adaptive Intensity Collapse Function - Eq. 4)
    # Hàm F(I_max) = sin(pi * I_max / 2) trơn, đạo hàm ổn định, không nổ gradient khi I_max -> 0
    C_k = np.power(np.sin(np.pi * I_max / 2.0) + eps, 1.0 / k)
    
    # Bước 3: Tạo bản đồ màu ngang H_hat và dọc V_hat - Eq. 5
    H_hat = C_k * s * h_polar
    V_hat = C_k * s * v_polar
    
    return np.stack([H_hat, V_hat, I_max], axis=-1)


def hvi_to_hsv_scratch(hvi_img, k=1.0, alpha_I=1.0, alpha_S=1.0, eps=1e-8):
    """
    Biến đổi ngược PHVIT (Perceptual-inverse HVI Transformation) từ HVI về HSV.
    Công thức theo Eq. 6 (CVPR 2025):
      h_hat = H_hat / (C_k + eps)
      v_hat = V_hat / (C_k + eps)
      Hue angle H = arctan2(v_hat, h_hat) mod 1 (hoặc quy về [0, 6))
      Saturation S = alpha_S * sqrt(h_hat^2 + v_hat^2)
      Value V = alpha_I * I_max
    
    Tham số:
      hvi_img: np.ndarray, kích thước (H, W, 3) gồm (H_hat, V_hat, I_max)
      k: float, hệ số nén tương ứng
      alpha_I: float >= 0, hệ số khuếch đại độ sáng (thanh trượt UI)
      alpha_S: float >= 0, hệ số khuếch đại độ bão hòa màu (thanh trượt UI)
      eps: float, hằng số chống chia 0
    Trả về:
      hsv: np.ndarray, kích thước (H, W, 3)
    """
    H_hat = hvi_img[..., 0]
    V_hat = hvi_img[..., 1]
    I_max = hvi_img[..., 2]
    
    # Tính lại bán kính C_k
    C_k = np.power(np.sin(np.pi * I_max / 2.0) + eps, 1.0 / k)
    
    # Giải nén tọa độ màu trung gian
    h_hat = H_hat / (C_k + eps)
    v_hat = V_hat / (C_k + eps)
    
    # Khôi phục góc Hue từ arctan2 (trả về [-pi, pi])
    angle = np.arctan2(v_hat, h_hat)
    h = (angle * (3.0 / np.pi)) % 6.0
    
    # Khôi phục độ bão hòa S kèm hệ số điều chỉnh alpha_S
    s = alpha_S * np.sqrt(h_hat**2 + v_hat**2)
    s = np.clip(s, 0.0, 1.0)
    
    # Khôi phục độ sáng V kèm hệ số điều chỉnh alpha_I
    v = alpha_I * I_max
    v = np.clip(v, 0.0, 1.0)
    
    return np.stack([h, s, v], axis=-1)


def srgb_to_hvi(rgb_img, k=1.0, eps=1e-8):
    """Pipeline trực tiếp sRGB -> HSV -> HVI."""
    hsv = srgb_to_hsv_scratch(rgb_img)
    return hsv_to_hvi_scratch(hsv, k=k, eps=eps)


def hvi_to_srgb(hvi_img, k=1.0, alpha_I=1.0, alpha_S=1.0, eps=1e-8):
    """Pipeline trực tiếp HVI -> HSV -> sRGB."""
    hsv = hvi_to_hsv_scratch(hvi_img, k=k, alpha_I=alpha_I, alpha_S=alpha_S, eps=eps)
    return hsv_to_srgb_scratch(hsv)


# ======================================================================================
# PHẦN 3: THUẬT TOÁN CỔ ĐIỂN ĐỐI CHỨNG TỰ CODE TỪ ĐẦU (SLIDE CHƯƠNG 2, TRANG 52-65)
# ======================================================================================

def gamma_correction_scratch(img, gamma=0.5, c=1.0):
    """
    Tăng cường độ sáng bằng biến đổi hàm mũ / Gamma Correction từ đầu bằng NumPy.
    Công thức theo Slide Chương 2 (trang 52-54): s = c * (r ^ gamma)
    Trong ảnh thiếu sáng, gamma < 1.0 giúp dải xám thấp dãn rộng ra -> ảnh sáng rõ hơn.
    """
    is_uint8 = (img.dtype == np.uint8) or (img.max() > 1.0)
    img_float = (img.astype(np.float64) / 255.0) if is_uint8 else img.astype(np.float64)
    
    # Biến đổi lũy thừa
    enhanced = c * np.power(img_float, gamma)
    enhanced = np.clip(enhanced, 0.0, 1.0)
    
    if is_uint8:
        return np.round(enhanced * 255.0).astype(np.uint8)
    return enhanced


def histogram_equalization_scratch(img):
    """
    Cân bằng lược đồ xám (Histogram Equalization) từ đầu bằng NumPy.
    Công thức theo Slide Chương 2 (trang 60-65) & Slide Chương 3 (trang 44):
      - Nếu là ảnh xám: T(r_k) = round(255 * sum_{j=0}^k n_j / N)
      - Nếu là ảnh màu: Biến đổi sang HSV, chỉ cân bằng trên kênh cường độ sáng V
        để tránh biến dạng màu sắc (Color Artifacts) khi cân bằng riêng từng kênh RGB!
    """
    is_uint8 = (img.dtype == np.uint8) or (img.max() > 1.0)
    
    # Trường hợp 1: Ảnh xám 2D
    if img.ndim == 2:
        img_u8 = img.astype(np.uint8) if is_uint8 else np.round(img * 255.0).astype(np.uint8)
        hist = np.bincount(img_u8.ravel(), minlength=256)
        cdf = hist.cumsum()
        total_pixels = img_u8.size
        # Bảng tra cứu (Lookup Table)
        lut = np.round((cdf / total_pixels) * 255.0).astype(np.uint8)
        eq_gray = lut[img_u8]
        return eq_gray if is_uint8 else (eq_gray.astype(np.float64) / 255.0)
    
    # Trường hợp 2: Ảnh màu 3D (Áp dụng trên kênh V của HSV tự code)
    hsv = srgb_to_hsv_scratch(img)
    v_channel = hsv[..., 2]
    v_u8 = np.round(v_channel * 255.0).astype(np.uint8)
    
    hist = np.bincount(v_u8.ravel(), minlength=256)
    cdf = hist.cumsum()
    lut = np.round((cdf / v_u8.size) * 255.0).astype(np.uint8)
    v_eq_u8 = lut[v_u8]
    
    hsv[..., 2] = v_eq_u8.astype(np.float64) / 255.0
    eq_rgb = hsv_to_srgb_scratch(hsv)
    
    return np.round(eq_rgb * 255.0).astype(np.uint8) if is_uint8 else eq_rgb


# ======================================================================================
# PHẦN 4: HÀM ĐỐI CHỨNG VÀ ĐO ĐẠC VỚI OPENCV (NGHIỆM THU ĐỒ ÁN)
# ======================================================================================

def compare_with_opencv(img_rgb):
    """
    So sánh độ sai khác giữa các thuật toán tự code bằng NumPy và hàm thư viện OpenCV.
    Tính Mean Squared Error (MSE) và Sai số tuyệt đối cực đại (Max Absolute Difference).
    """
    img_u8 = img_rgb.astype(np.uint8) if img_rgb.max() > 1.0 else (img_rgb * 255.0).round().astype(np.uint8)
    img_gray = cv2.cvtColor(img_u8, cv2.COLOR_RGB2GRAY)
    
    print("\n" + "="*70)
    print(" KẾT QUẢ ĐỐI CHỨNG THUẬT TOÁN TỰ CODE NUMPY VS OPENCV")
    print("="*70)
    
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
    print(f"[2] Histogram Equalization (Grayscale):")
    print(f"    - Max Absolute Difference: {np.max(diff_he):.4f} mức xám (sai số làm tròn <= 1)")
    print(f"    - Mean Squared Error (MSE): {np.mean(diff_he**2):.6f}")
    
    # 3. Đối chứng tính chu trình phục hồi sRGB -> HVI -> sRGB
    hvi = srgb_to_hvi(img_u8, k=1.0)
    rec_rgb = hvi_to_srgb(hvi, k=1.0, alpha_I=1.0, alpha_S=1.0)
    rec_u8 = (rec_rgb * 255.0).round().astype(np.uint8)
    diff_hvi_cycle = np.abs(img_u8.astype(float) - rec_u8.astype(float))
    print(f"[3] Chu trình phục hồi thuận nghịch sRGB -> HVI -> sRGB:")
    print(f"    - Max Absolute Difference: {np.max(diff_hvi_cycle):.4f} mức xám")
    print(f"    - Mean Absolute Error (MAE): {np.mean(diff_hvi_cycle):.6f} mức xám")
    print("="*70 + "\n")


# ======================================================================================
# PHẦN 5: TẠO ẢNH TEST VÀ TRỰC QUAN HÓA (ARTIFACTS CHO BÁO CÁO & SLIDE)
# ======================================================================================

def create_synthetic_test_case(height=300, width=400):
    """
    Tạo ảnh tổng hợp kiểm thử chuyên dụng cho LLIE:
    Gồm dải chuyển màu tối dần, các khối màu cơ bản (đặc biệt là khối màu ĐỎ để kiểm tra
    nhiễu đứt gãy màu đỏ) và vùng tối sâu để kiểm tra nhiễu mặt phẳng đen.
    """
    img = np.zeros((height, width, 3), dtype=np.float64)
    
    # Nền chuyển sắc tối (cường độ sáng giảm từ 0.35 về 0.01)
    grad = np.linspace(0.35, 0.01, width).reshape(1, width, 1)
    img[:, :] = grad
    
    # Khối 1: Vật thể màu Đỏ thuần trong tối (R=0.5, G=0.02, B=0.02)
    img[40:120, 40:140] = [0.55, 0.02, 0.02]
    
    # Khối 2: Vật thể màu Xanh lá trong tối (R=0.02, G=0.45, B=0.02)
    img[40:120, 160:260] = [0.02, 0.45, 0.02]
    
    # Khối 3: Vật thể màu Xanh dương trong tối (R=0.02, G=0.02, B=0.60)
    img[40:120, 280:380] = [0.02, 0.02, 0.60]
    
    # Khối 4: Vật thể màu Vàng (pha trộn) trong tối
    img[160:240, 80:180] = [0.45, 0.45, 0.03]
    
    # Khối 5: Vùng tối cực đoan (Black plane) I_max ~ 0.005
    img[160:240, 220:320] = [0.008, 0.005, 0.006]
    
    # Thêm nhiễu Gaussian nhẹ mô phỏng nhiễu photon cảm biến ban đêm
    noise = np.random.normal(0, 0.015, img.shape)
    img = np.clip(img + noise, 0.0, 1.0)
    return img


def plot_hvi_density_k(img_rgb, k_values=[0.5, 1.0, 3.0, 10.0, 50.0], output_path="output_member1/hvi_density_k.png"):
    """
    Tạo biểu đồ trực quan hóa không gian HVI khi thay đổi tham số mật độ k in {0.5, 1, 3, 10, 50}.
    Tái hiện Hình 8 & Hình 9 trong Phụ lục bài báo CVPR 2025:
      - k < 1: nén quá mạnh vùng tối
      - k = 1 ~ 3: cân bằng tối ưu
      - k >= 10: xung đột chi tiết và khuếch đại nhiễu (Failure Case 2)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    n_k = len(k_values)
    fig, axes = plt.subplots(3, n_k, figsize=(3.2 * n_k, 8))
    
    for i, k in enumerate(k_values):
        hvi = srgb_to_hvi(img_rgb, k=k)
        H_hat = hvi[..., 0]
        V_hat = hvi[..., 1]
        I_max = hvi[..., 2]
        
        # Hàng 1: Kênh H_hat (chuẩn hóa về [0, 1] để hiển thị)
        h_vis = (H_hat - H_hat.min()) / (H_hat.max() - H_hat.min() + 1e-8)
        axes[0, i].imshow(h_vis, cmap='coolwarm')
        axes[0, i].set_title(f"H_hat (k = {k})", fontsize=11, fontweight='bold')
        axes[0, i].axis('off')
        
        # Hàng 2: Kênh V_hat
        v_vis = (V_hat - V_hat.min()) / (V_hat.max() - V_hat.min() + 1e-8)
        axes[1, i].imshow(v_vis, cmap='coolwarm')
        axes[1, i].set_title(f"V_hat (k = {k})", fontsize=11, fontweight='bold')
        axes[1, i].axis('off')
        
        # Hàng 3: Tái tạo ảnh sRGB khi tăng sáng nhẹ
        rec_rgb = hvi_to_srgb(hvi, k=k, alpha_I=1.8, alpha_S=1.2)
        axes[2, i].imshow(rec_rgb)
        axes[2, i].set_title(f"PHVIT (k = {k})", fontsize=11, fontweight='bold')
        axes[2, i].axis('off')
        
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[+] Đã lưu biểu đồ khảo sát tham số k tại: {output_path}")


def plot_hs_vs_hv_noise(img_rgb, output_path="output_member1/noise_hs_vs_hv.png"):
    """
    Vẽ mặt phẳng màu HS (của HSV) và mặt phẳng HV (của HVI) của các điểm ảnh tối.
    Minh chứng toán học trực quan:
      - Trong HSV: Các điểm màu đỏ bị xé làm 2 nửa ở h=0 và h=6; các điểm tối bị văng tán xạ khắp mặt phẳng (Black plane noise).
      - Trong HVI: Điểm tối tự động co cụm mượt mà về gốc (0, 0); hai đầu mút màu đỏ trùng khít tại (1, 0).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    hsv = srgb_to_hsv_scratch(img_rgb)
    hvi = srgb_to_hvi(img_rgb, k=1.0)
    
    h = hsv[..., 0].ravel()
    s = hsv[..., 1].ravel()
    I_max = hsv[..., 2].ravel()
    
    H_hat = hvi[..., 0].ravel()
    V_hat = hvi[..., 1].ravel()
    
    # Lấy mẫu ngẫu nhiên 5000 điểm ảnh để vẽ scatter
    indices = np.random.choice(len(h), size=min(5000, len(h)), replace=False)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 1. Mặt phẳng màu HSV (Hue - Saturation)
    # Tọa độ cực HSV: x = s * cos(pi * h / 3), y = s * sin(pi * h / 3) nhưng chưa nén C_k
    x_hsv = s[indices] * np.cos(np.pi * h[indices] / 3.0)
    y_hsv = s[indices] * np.sin(np.pi * h[indices] / 3.0)
    sc1 = axes[0].scatter(x_hsv, y_hsv, c=I_max[indices], cmap='inferno', s=8, alpha=0.6)
    axes[0].set_title("Mặt phẳng màu HSV thuần (Bị nhiễu đen & tán xạ khi tối)", fontsize=12, fontweight='bold')
    axes[0].set_xlabel("S * cos(pi*h/3)")
    axes[0].set_ylabel("S * sin(pi*h/3)")
    axes[0].grid(True, linestyle='--', alpha=0.5)
    plt.colorbar(sc1, ax=axes[0], label="Cường độ sáng I_max")
    
    # 2. Mặt phẳng màu HVI (H_hat - V_hat đã nén C_k)
    sc2 = axes[1].scatter(H_hat[indices], V_hat[indices], c=I_max[indices], cmap='inferno', s=8, alpha=0.6)
    axes[1].set_title("Mặt phẳng màu HVI (Đã nén vùng tối về gốc (0,0) bằng C_k)", fontsize=12, fontweight='bold')
    axes[1].set_xlabel("Kênh màu ngang H_hat")
    axes[1].set_ylabel("Kênh màu dọc V_hat")
    axes[1].grid(True, linestyle='--', alpha=0.5)
    plt.colorbar(sc2, ax=axes[1], label="Cường độ sáng I_max")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[+] Đã lưu bản đồ phân tích nhiễu màu HS vs HV tại: {output_path}")


def plot_comparison_methods(img_rgb, output_path="output_member1/methods_comparison.png"):
    """
    Vẽ bảng so sánh trực quan giữa:
    Ảnh tối gốc | Gamma tự code | Histogram Eq tự code | HVI-PHVIT tăng sáng
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    gamma_res = gamma_correction_scratch(img_rgb, gamma=0.4)
    he_res = histogram_equalization_scratch(img_rgb)
    
    # Tăng sáng trong không gian HVI (alpha_I = 2.2, alpha_S = 1.1)
    hvi = srgb_to_hvi(img_rgb, k=1.0)
    hvi_res = hvi_to_srgb(hvi, k=1.0, alpha_I=2.2, alpha_S=1.1)
    
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))
    
    axes[0].imshow(img_rgb)
    axes[0].set_title("Ảnh tối gốc (Low-light Input)", fontsize=11, fontweight='bold')
    axes[0].axis('off')
    
    axes[1].imshow(gamma_res)
    axes[1].set_title("Gamma Correction (gamma=0.4)", fontsize=11, fontweight='bold')
    axes[1].axis('off')
    
    axes[2].imshow(he_res)
    axes[2].set_title("Histogram Eq (trên kênh V)", fontsize=11, fontweight='bold')
    axes[2].axis('off')
    
    axes[3].imshow(hvi_res)
    axes[3].set_title("HVI-PHVIT (alpha_I=2.2, alpha_S=1.1)", fontsize=11, fontweight='bold')
    axes[3].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[+] Đã lưu bảng so sánh phương pháp tại: {output_path}")


# ======================================================================================
# HÀM CHÍNH: CHẠY KIỂM THỬ TOÀN DIỆN & XUẤT TOÀN BỘ SẢN PHẨM BÀN GIAO
# ======================================================================================

def main():
    print("\n" + "#"*70)
    print("  ĐỒ ÁN XỬ LÝ ẢNH - CHẠY NGHIỆM THU MODULE THÀNH VIÊN 1")
    print("  ĐỀ TÀI: [CVPR'25] HVI COLOR SPACE FOR LOW-LIGHT IMAGE ENHANCEMENT")
    print("#"*70)
    
    output_dir = "output_member1"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Tạo test case tổng hợp chuẩn
    print("[*] Đang khởi tạo test case ảnh tổng hợp chuẩn...")
    test_img = create_synthetic_test_case(height=360, width=480)
    cv2.imwrite(os.path.join(output_dir, "test_input_dark.png"), cv2.cvtColor((test_img * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    
    # 2. Đo đạc định lượng đối chứng với OpenCV
    compare_with_opencv(test_img)
    
    # 3. Khảo sát tham số mật độ nén k
    print("[*] Đang tạo biểu đồ khảo sát tham số mật độ k in {0.5, 1, 3, 10, 50}...")
    plot_hvi_density_k(test_img, k_values=[0.5, 1.0, 3.0, 10.0, 50.0], output_path=os.path.join(output_dir, "hvi_density_k.png"))
    
    # 4. Phân tích mặt phẳng màu HS vs HV
    print("[*] Đang vẽ bản đồ phân bố nhiễu màu mặt phẳng HS vs HV...")
    plot_hs_vs_hv_noise(test_img, output_path=os.path.join(output_dir, "noise_hs_vs_hv.png"))
    
    # 5. So sánh các phương pháp
    print("[*] Đang xuất ảnh so sánh đối chứng các phương pháp...")
    plot_comparison_methods(test_img, output_path=os.path.join(output_dir, "methods_comparison.png"))
    
    print("\n" + "="*70)
    print(f" HOÀN TẤT TOÀN BỘ NHIỆM VỤ THÀNH VIÊN 1!")
    print(f" Toàn bộ ảnh thực nghiệm, biểu đồ và kết quả kiểm thử đã được lưu tại:")
    print(f" -> {os.path.abspath(output_dir)}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
