# ĐỒ ÁN MÔN HỌC: XỬ LÝ ẢNH (INT13146)
**Học viện Công nghệ Bưu chính Viễn thông (PTIT) - Khoa CNTT 1**  
**Giảng viên hướng dẫn:** TS. Phạm Hoàng Việt  
**Đề tài:** `[CVPR'25] HVI: A New Color Space for Low-light Image Enhancement`  
**Nhóm sinh viên thực hiện:** 4 thành viên (đóng góp chuyên môn 25% mỗi người)

---

## 📌 BẢNG PHÂN CÔNG CHUYÊN MÔN & TÍCH HỢP 4 THÀNH VIÊN (25% / NGƯỜI)

Theo quy định đề cương môn học, tỷ lệ đóng góp chỉ tính trên nội dung chuyên môn (thuật toán, cài đặt mã nguồn, thực nghiệm và tích hợp):

| Thành viên | Tỷ lệ | Nội dung chuyên môn & Module phụ trách | Sản phẩm bàn giao tích hợp |
| :--- | :---: | :--- | :--- |
| **Thành viên 1** | 25% | **Toán học HVI & Code from scratch (NumPy thuần):**<br>• Biến đổi $sRGB \leftrightarrow HSV \leftrightarrow HVI$ (Eq. 1–6).<br>• Xóa nhiễu đứt gãy đỏ ($h_{polar}, v_{polar}$) và nhiễu đen ($C_k$).<br>• Tự code Gamma Correction, HE, CLAHE đối chứng OpenCV. | • File `color_space_scratch.py`<br>• Thư mục ảnh `output_member1/`<br>• Bản đồ lỗi $E_{HS}$ vs $E_{HV}$ (+6.11 dB) |
| **Thành viên 2** | 25% | **Mạng 2 nhánh CIDNet & Khối LCA:**<br>• Nghiên cứu kiến trúc Dual-branch UNet (1.88M params, 7.57 GFLOPs).<br>• 6 khối Lighten Cross-Attention (CAB, IEL theo Retinex, CDL).<br>• Trích xuất đặc trưng trung gian 2 nhánh (I-branch & HV-branch). | • File `inspect_cidnet_features.py`<br>• Module kiến trúc `net/` và `loss/`<br>• Trực quan hóa 8 kênh kích hoạt cao nhất |
| **Thành viên 3** | 25% | **Bộ dữ liệu test, Đánh giá định lượng & Phân tích lỗi:**<br>• Chuẩn bị tập test có cặp (LOL-v1, LOL-v2) & không cặp (DICM, LIME).<br>• Đo đạc PSNR, SSIM, LPIPS, NIQE giữa Tự code vs OpenCV vs CIDNet.<br>• Phân tích chuyên sâu 4 trường hợp thất bại (Failure Cases). | • File `eval.py`, `measure.py`, `failure_cases.py`<br>• Thư mục `failure_figures/`, `test_cases/`<br>• Toàn bộ 7 file số liệu `.csv` & `chay_tv3.ipynb` |
| **Thành viên 4** | 25% | **Pipeline tích hợp, Biến đổi ngược PHVIT & Web Demo:**<br>• Tiền xử lý đệm đối xứng Reflect Padding $8 \times 8$ & Clip Operation.<br>• Biến đổi ngược PHVIT điều chỉnh độ sáng $\alpha_I$, độ bão hòa $\alpha_S$.<br>• Xây dựng giao diện tương tác Web Demo đặt cạnh nhau 3 phương pháp. | • File giao diện `app_demo.py` (Gradio)<br>• Thư mục ảnh `output_member4/`<br>• Tự động nạp weights local hoặc Hugging Face |

---

## 📂 CẤU TRÚC THƯ MỤC DỰ ÁN TÍCH HỢP

```
XLA/
├── color_space_scratch.py       # [TV1] Biến đổi sRGB <-> HSV <-> HVI, Gamma, HE, CLAHE thuần NumPy
├── inspect_cidnet_features.py   # [TV2] Trích xuất feature maps trung gian mạng CIDNet
├── eval.py                      # [TV3] Pipeline đánh giá định lượng đa bộ dữ liệu
├── measure.py                   # [TV3] Hàm tính chỉ số PSNR, SSIM, LPIPS, NIQE
├── failure_cases.py             # [TV3] Tái hiện và đo đạc 4 trường hợp thất bại (Failure Cases)
├── prepare_test_cases.py        # [TV3] Tiền xử lý và gom nhóm các ca kiểm thử
├── app_demo.py                  # [TV4] Giao diện Web Demo trực quan (Gradio)
├── asciiout.py                  # [TV3] Utility in ấn log terminal
├── chay_tv3.ipynb               # [TV3] Jupyter Notebook chạy thực nghiệm định lượng
├── net/                         # [Kiến trúc mạng CIDNet]
│   ├── CIDNet.py                # Dual-branch UNet
│   ├── LCA.py                   # Lighten Cross-Attention (CAB + IEL + CDL)
│   ├── HVI_transform.py         # Module biến đổi HVI trong PyTorch
│   └── transformer_utils.py     # Lớp bổ trợ Transformer
├── loss/                        # [Hàm mất mát huấn luyện]
│   └── losses.py                # L1, SSIM, Edge Loss, Perceptual VGG Loss
├── output_member1/              # [TV1] Ảnh thực nghiệm HVI, khảo sát k, bản đồ lỗi E_HS vs E_HV
├── output_member4/              # [TV4] Ảnh thực nghiệm Web Demo, k-sweep, alpha-sweep
├── failure_figures/             # [TV3] Ảnh minh chứng 4 trường hợp thất bại
├── test_cases/                  # [TV3] Bộ ảnh kiểm thử phân loại (LOLv1, LOLv2, DICM, LIME, custom)
├── results/                     # [TV3] Kết quả ảnh đầu ra của các thuật toán
├── anh_goc/                     # Bộ ảnh gốc test
├── *.csv                        # Bảng số liệu định lượng (quantitative_results, failure_metrics...)
├── Ke_Hoach_Trien_Khai_...docx  # Kế hoạch phân công 4 thành viên (25%/người)
├── Khung_Bao_Cao_11_Muc_...docx # Khung báo cáo chi tiết 11 mục và kịch bản thuyết trình
└── README.md                    # Tài liệu hướng dẫn tích hợp toàn dự án
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY TỪNG MODULE

### 1. Cài đặt môi trường
Khuyến nghị Python 3.10+:
```bash
pip install numpy opencv-python scikit-image matplotlib pandas pillow torch torchvision einops gradio huggingface_hub safetensors
```

### 2. Chạy Module Thành viên 1 (Toán học HVI & Thuật toán cổ điển)
```bash
python color_space_scratch.py
```
* Kết quả đo sai số với OpenCV (MSE = 0.000000 trên HE, MAE = 0.000000 trên chu trình HVI) và 5 ảnh trực quan hóa lưu tại `output_member1/`.

### 3. Chạy Module Thành viên 2 (Trích xuất đặc trưng mạng CIDNet)
```bash
# Trích xuất đặc trưng trên một ảnh bất kỳ
python inspect_cidnet_features.py --img anh_goc/00767.png --save_dir output_tv2
```

### 4. Chạy Module Thành viên 3 (Đánh giá định lượng & Phân tích thất bại)
```bash
# Phân tích 4 trường hợp thất bại (Failure Cases)
python failure_cases.py

# Đánh giá chỉ số chất lượng ảnh
python eval.py evaluate
```

### 5. Chạy Module Thành viên 4 (Giao diện Web Demo trực quan)
```bash
python app_demo.py
```
* Mở trình duyệt tại địa chỉ: `http://127.0.0.1:7860` để tải ảnh thật, kéo thả tham số $\alpha_I, \alpha_S, k$, và xem kết quả đối chiếu trực tiếp giữa: **Tự code (TV1) ↔ OpenCV ↔ HVI-CIDNet (TV2 & TV4)**.
