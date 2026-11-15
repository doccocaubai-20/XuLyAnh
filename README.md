# Đồ Án Môn Học: Xử Lý Ảnh (INT13146)
**Học viện Công nghệ Bưu chính Viễn thông (PTIT) - Khoa CNTT 1**  
**Giảng viên hướng dẫn:** ThS/TS. Phạm Hoàng Việt  
**Đề tài:** `[CVPR'25] HVI: A New Color Space for Low-light Image Enhancement`  

---

## 📌 Phân công Chuyên môn: Thành viên 1 (25% đóng góp)
- **Nội dung:** Nghiên cứu bản chất toán học của không gian màu HVI, giải quyết 2 nhược điểm của HSV trong ảnh thiếu sáng (*Nhiễu đứt gãy màu đỏ* & *Nhiễu mặt phẳng đen*).
- **Quy định đồ án:** Cài đặt toàn bộ từ đầu (**code from scratch bằng NumPy**), không sử dụng các hàm biến đổi màu và xử lý có sẵn của OpenCV.

---

## 🚀 Các tính năng chính trong `color_space_scratch.py`

### 1. Biến đổi không gian màu thuần NumPy
* **`srgb_to_hsv_scratch(rgb)` & `hsv_to_srgb_scratch(hsv)`:** Tự cài đặt biến đổi hai chiều giữa sRGB và HSV theo công thức toán học (Slide Chương 3).
* **`hsv_to_hvi_scratch(hsv, k)` (Biến đổi thuận HVIT - Eq. 1-5 CVPR 2025):**
  - **Phân cực hóa trục Hue:** $h_{polar} = \cos(\pi h / 3)$, $v_{polar} = \sin(\pi h / 3)$ $\rightarrow$ giúp hai đầu mút màu đỏ tại $h=0$ và $h=6$ trùng khít tại $(1, 0)$, loại bỏ hoàn toàn đứt gãy màu đỏ.
  - **Hàm nén vùng tối thích nghi:** $C_k(x) = [\sin(\pi I_{max}(x) / 2) + \varepsilon]^{1/k}$ $\rightarrow$ gom cụm các điểm tối về gốc tọa độ $(0, 0)$, khử nhiễu mặt phẳng đen.
  - **Bản đồ HVI 3 kênh:** $\hat{H} = C_k \odot S \odot h_{polar}$, $\hat{V} = C_k \odot S \odot v_{polar}$, $I_{max} = \max(R, G, B)$.
* **`hvi_to_srgb_scratch(hvi, alpha_I, alpha_S)` (Biến đổi ngược PHVIT - Eq. 6 CVPR 2025):** Tái tạo lại ảnh sRGB, hỗ trợ hai tham số tùy chỉnh độ sáng ($\alpha_I$) và độ bão hòa màu ($\alpha_S$).

### 2. Thuật toán cổ điển đối chứng
* **`gamma_correction_scratch(img, gamma)`:** Tự cài đặt biến đổi hàm mũ $s = c \cdot r^\gamma$ (Slide Chương 2).
* **`histogram_equalization_scratch(img)`:** Tự tính Histogram và CDF trên kênh cường độ sáng $V$ trong HSV để tăng tương phản mà không làm lệch màu.

---

## 📊 Kết quả kiểm thử định lượng đối chứng với OpenCV

Chạy script kiểm thử nghiệm thu:
```bash
python color_space_scratch.py
```

| Thuật toán | Đối chứng OpenCV | Max Difference | Mean Squared Error (MSE) |
| :--- | :--- | :---: | :---: |
| **Gamma Correction ($\gamma = 0.5$)** | `cv2.LUT` | **1.0000** mức xám | **0.5476** |
| **Histogram Equalization** | `cv2.equalizeHist` | **2.0000** mức xám | **1.1706** |
| **Chu trình sRGB $\rightarrow$ HVI $\rightarrow$ sRGB** | Thuận nghịch PHVIT | **0.0000** mức xám | **0.000000** (MAE) |

---

## 🖼️ Ảnh thực nghiệm (Thư mục `output_member1/`)
* `hvi_density_k.png`: Khảo sát ảnh hưởng của tham số mật độ $k \in \{0.5, 1, 3, 10, 50\}$.
* `noise_hs_vs_hv.png`: Trực quan hóa mặt phẳng màu $HS$ vs $\hat{H}\hat{V}$ chứng minh xóa bỏ 2 loại nhiễu.
* `methods_comparison.png`: Bảng so sánh trực quan giữa ảnh tối gốc, Gamma, Histogram Eq và HVI-PHVIT.
