# Bài tập lớn môn Xử lý ảnh (INT13146)

Học viện Công nghệ Bưu chính Viễn thông  
Khoa Công nghệ Thông tin 1  
Giảng viên hướng dẫn: TS. Phạm Hoàng Việt  
Đề tài: HVI: A New Color Space for Low-light Image Enhancement (CVPR 2025)

---

## 1. Phân công nhiệm vụ nhóm

| STT | Họ và tên | Mã sinh viên | Nhiệm vụ phụ trách | Sản phẩm mã nguồn / Kết quả | Tỷ lệ đóng góp |
| :---: | :--- | :---: | :--- | :--- | :---: |
| 1 | Lê Quang Huy | B23DCCN388 | Nghiên cứu lý thuyết không gian màu HVI; lập trình thuần NumPy các phép biến đổi sRGB <-> HSV <-> HVI, Gamma Correction, Histogram Equalization, CLAHE và đối chứng với OpenCV. | color_space_scratch.py<br>output_member1/ | 25% |
| 2 | Nguyễn Khả Luận | B23DCCN514 | Nghiên cứu cấu trúc mạng CIDNet (Dual-branch UNet) và 6 khối Lighten Cross-Attention (LCA); trích xuất và trực quan hóa bản đồ đặc trưng (feature maps) trung gian. | inspect_cidnet_features.py<br>net/, loss/<br>output_tv2/ | 25% |
| 3 | Nguyễn Quang Huy | B23DCCN402 | Chuẩn bị dữ liệu kiểm thử (LOL-v1, LOL-v2, DICM, LIME, ảnh tự chụp); đo đạc định lượng (PSNR, SSIM, LPIPS, NIQE); phân tích 4 trường hợp thất bại (Failure Cases). | eval.py, measure.py<br>failure_cases.py<br>failure_figures/<br>Các file .csv | 25% |
| 4 | Nguyễn Đại Nghĩa | B23DCCN598 | Xây dựng pipeline tích hợp (Reflect Padding, Clip Operation); biến đổi ngược PHVIT với hệ số alpha_I, alpha_S; xây dựng giao diện Web Demo so sánh kết quả. | app_demo.py<br>output_member4/ | 25% |

---

## 2. Cấu trúc thư mục

```
XLA/
├── color_space_scratch.py      # [TV1] Biến đổi hệ màu và thuật toán kinh điển bằng NumPy
├── inspect_cidnet_features.py  # [TV2] Trích xuất feature maps trung gian của mạng CIDNet
├── eval.py                     # [TV3] Đánh giá định lượng trên các tập dữ liệu
├── measure.py                  # [TV3] Hàm đo các chỉ số PSNR, SSIM, LPIPS, NIQE
├── failure_cases.py            # [TV3] Tái hiện và đo đạc 4 ca thất bại
├── prepare_test_cases.py       # [TV3] Tiền xử lý dữ liệu kiểm thử
├── asciiout.py                 # [TV3] Tiện ích in ấn terminal không dấu
├── chay_tv3.ipynb              # [TV3] Notebook chạy thử nghiệm định lượng
├── app_demo.py                 # [TV4] Giao diện ứng dụng Web tương tác (Gradio)
├── net/                        # Kiến trúc mô hình mạng nơ-ron CIDNet
│   ├── CIDNet.py               # Mạng 2 nhánh Dual-branch UNet
│   ├── LCA.py                  # Khối Lighten Cross-Attention
│   ├── HVI_transform.py        # Module biến đổi HVI dạng tensor PyTorch
│   └── transformer_utils.py    # Lớp bổ trợ Transformer
├── loss/                       # Các hàm mất mát huấn luyện (L1, SSIM, Edge, VGG)
├── output_member1/             # Kết quả thực nghiệm của TV1 (đối chứng OpenCV, bản đồ sai số E_HV)
├── output_tv2/                 # Bản đồ đặc trưng trích xuất của TV2
├── failure_figures/            # Hình ảnh minh chứng 4 trường hợp thất bại của TV3
├── output_member4/             # Kết quả chạy thực nghiệm Web Demo của TV4
├── anh_goc/                    # Bộ ảnh tối thực tế do nhóm tự chụp
├── *.csv                       # Bảng dữ liệu định lượng trích xuất từ thực nghiệm
└── README.md                   # Hướng dẫn dự án
```

---

## 3. Hướng dẫn cài đặt và chạy chương trình

### 3.1. Cài đặt môi trường

Yêu cầu môi trường Python 3.10 trở lên. Cài đặt các thư viện phụ thuộc:

```bash
pip install numpy opencv-python scikit-image matplotlib pandas pillow torch torchvision einops gradio huggingface_hub safetensors
```

### 3.2. Chạy module tự lập trình bằng NumPy (Thành viên 1)

Chạy kiểm thử các hàm biến đổi hệ màu sRGB - HSV - HVI và các thuật toán Gamma, HE, CLAHE đối chứng với OpenCV:

```bash
python color_space_scratch.py
```

Kết quả in ra terminal đo sai số (MSE/MAE) và các ảnh trực quan hóa được lưu vào thư mục `output_member1/`.

### 3.3. Chạy trích xuất đặc trưng mạng CIDNet (Thành viên 2)

Trích xuất bản đồ đặc trưng tại các tầng trung gian của mô hình:

```bash
python inspect_cidnet_features.py --img anh_goc/night_01.jpg --save_dir output_tv2
```

Ảnh phân tích đặc trưng của 2 nhánh Intensity và Hue-Saturation được lưu tại thư mục `output_tv2/`.

### 3.4. Chạy đánh giá định lượng và phân tích ca thất bại (Thành viên 3)

Phân tích 4 trường hợp thất bại của mô hình:

```bash
python failure_cases.py
```

Đo lường các chỉ số PSNR, SSIM, NIQE trên tập dữ liệu:

```bash
python eval.py evaluate
```

### 3.5. Chạy giao diện Web Demo (Thành viên 4)

Khởi động giao diện web so sánh trực quan các phương pháp:

```bash
python app_demo.py
```

Mở trình duyệt truy cập: `http://127.0.0.1:7860`.  
Giao diện cho phép tải ảnh, điều chỉnh thanh trượt alpha_I, alpha_S, k và đối chiếu đồng thời: Ảnh gốc, Thuật toán cổ điển tự code (TV1), OpenCV và Mô hình HVI-CIDNet (TV2 & TV4).
