"""
Script tạo file Word Báo cáo Bài tập lớn chuẩn mực học thuật:
Bao_Cao_BTL_HVI_CIDNet_Chinh_Thuc.docx
Theo định dạng chuẩn PTIT (học phần INT13146 - TS. Phạm Hoàng Việt)
Tích hợp trọn vẹn kết quả chuyên môn của cả 4 thành viên (25% mỗi người).
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


def set_cell_shading(cell, color_hex):
    """Đặt màu nền cho ô trong bảng."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Đặt khoảng đệm lề cho ô trong bảng."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_styled_heading(doc, text, level):
    """Thêm tiêu đề với định dạng Times New Roman chuẩn và khoảng cách hợp lý."""
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.bold = True
    
    if level == 1:
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        run.font.size = Pt(15)
        run.font.color.rgb = RGBColor(0, 32, 96) # Dark Blue
    elif level == 2:
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(15, 60, 120)
    elif level == 3:
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        run.font.size = Pt(12)
        run.font.italic = True
        run.font.color.rgb = RGBColor(40, 40, 40)
    return p


def add_body_paragraph(doc, text, bold_prefix="", italic=False):
    """Thêm đoạn văn nội dung chuẩn Times New Roman 12pt, giãn dòng 1.3."""
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.font.size = Pt(12)
        r_pre.bold = True
        
    r_text = p.add_run(text)
    r_text.font.name = 'Times New Roman'
    r_text.font.size = Pt(12)
    r_text.italic = italic
    return p


def add_image_safe(doc, img_path, caption, width_inch=5.5):
    """Thêm ảnh an toàn kèm chú thích căn giữa."""
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_inch))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run(caption)
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10.5)
        r_cap.italic = True
        r_cap.font.color.rgb = RGBColor(70, 70, 70)


def build_report():
    doc = docx.Document()
    
    # 1. Cấu hình lề trang chuẩn đồ án (Lề trái 3cm, các lề khác 2cm)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)     # ~2.0 cm
        section.bottom_margin = Inches(0.8)  # ~2.0 cm
        section.left_margin = Inches(1.18)   # ~3.0 cm
        section.right_margin = Inches(0.8)   # ~2.0 cm

    # =========================================================================
    # TRANG BÌA (COVER PAGE)
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG\nKHOA CÔNG NGHỆ THÔNG TIN 1\n---***---")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.bold = True
    p.paragraph_format.space_after = Pt(40)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("BÁO CÁO BÀI TẬP LỚN\nHỌC PHẦN XỬ LÝ ẢNH (INT13146)")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 32, 96)
    p.paragraph_format.space_after = Pt(25)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("ĐỀ TÀI (MỨC ĐỘ TRUNG BÌNH - HỘI NGHỊ HẠNG A* CVPR 2025):\n")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.bold = True
    
    r_title = p.add_run("HVI: A NEW COLOR SPACE FOR LOW-LIGHT IMAGE ENHANCEMENT\n(KHÔNG GIAN MÀU MỚI HVI VÀ MẠNG TÁCH NHÁNH CIDNET TRONG TĂNG CƯỜNG ẢNH THIẾU SÁNG)")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(15)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(180, 0, 0)
    p.paragraph_format.space_after = Pt(45)

    # Thông tin giáo viên và sinh viên
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_after = Pt(60)
    
    r_gv = p.add_run("Giảng viên hướng dẫn:\t")
    r_gv.bold = True
    r_gv.font.size = Pt(12.5)
    r_gvn = p.add_run("TS. Phạm Hoàng Việt\n")
    r_gvn.font.size = Pt(12.5)
    
    r_lp = p.add_run("Lớp học phần:\t\t")
    r_lp.bold = True
    r_lp.font.size = Pt(12.5)
    r_lpn = p.add_run("INT13146 - Xử lý ảnh\n\n")
    r_lpn.font.size = Pt(12.5)

    r_sv = p.add_run("Sinh viên thực hiện đề tài (Nhóm 4 thành viên):\n")
    r_sv.bold = True
    r_sv.font.size = Pt(12.5)
    
    r_list = p.add_run(
        "1. Thành viên 1: Nghiên cứu Toán học HVI & Code thuần NumPy từ đầu (25%)\n"
        "2. Thành viên 2: Mạng 2 nhánh CIDNet & Khối Cross-Attention LCA (25%)\n"
        "3. Thành viên 3: Bộ dữ liệu test, Đánh giá định lượng & 4 Failure Cases (25%)\n"
        "4. Thành viên 4: Pipeline tích hợp Reflect Padding & Web Demo Gradio (25%)\n"
    )
    r_list.font.size = Pt(12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_date = p.add_run("HÀ NỘI, 2026")
    r_date.bold = True
    r_date.font.size = Pt(12)
    
    doc.add_page_break()

    # =========================================================================
    # BẢNG PHÂN CÔNG NHIỆM VỤ (TRANG iii)
    # =========================================================================
    add_styled_heading(doc, "BẢNG PHÂN CÔNG NHIỆM VỤ VÀ TỶ LỆ ĐÓNG GÓP CỦA 4 THÀNH VIÊN", level=1)
    add_body_paragraph(
        doc,
        "Theo đúng quy định trong đề cương học phần Xử lý ảnh (INT13146) của giảng viên TS. Phạm Hoàng Việt, "
        "tỷ lệ % đóng góp của các thành viên trong nhóm được tính toán hoàn toàn dựa trên khối lượng công việc chuyên môn "
        "(nghiên cứu lý thuyết thuật toán, lập trình mã nguồn, chuẩn bị bộ dữ liệu và chạy thực nghiệm đối chứng), "
        "tuyệt đối không tính công viết báo cáo hay làm slides thuyết trình:"
    )

    tbl_pc = doc.add_table(rows=5, cols=5)
    tbl_pc.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["STT", "Thành viên", "Nhiệm vụ chuyên môn phụ trách", "Sản phẩm mã nguồn & Deliverables", "Tỷ lệ"]
    col_widths = [Inches(0.6), Inches(1.3), Inches(2.3), Inches(1.8), Inches(0.8)]
    
    for i, h in enumerate(headers):
        cell = tbl_pc.cell(0, i)
        cell.text = h
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.paragraphs[0].runs[0].font.size = Pt(10.5)
        set_cell_shading(cell, "E0E8F5")
        set_cell_margins(cell, 120, 120, 100, 100)

    rows_data = [
        ("1", "Thành viên 1\n(Nhóm trưởng)", 
         "Nghiên cứu hạn chế sRGB & 2 loại nhiễu trong HSV; xây dựng cơ sở toán học HVI (Eq. 1-6); tự lập trình từ đầu bằng NumPy sRGB <-> HSV <-> HVI, Gamma và CLAHE đối chứng OpenCV.",
         "color_space_scratch.py, thư mục output_member1/ (bản đồ sai số E_HS vs E_HV tăng +6.11 dB).", "25%"),
        ("2", "Thành viên 2", 
         "Nghiên cứu kiến trúc Dual-branch UNet CIDNet (1.88M tham số, 7.57 GFLOPs); cấu trúc 6 khối LCA (CAB, IEL theo Retinex, CDL khử nhiễu) và hàm mất mát kép.",
         "inspect_cidnet_features.py, thư mục net/, loss/, xuất 31 ảnh feature maps trong output_tv2/.", "25%"),
        ("3", "Thành viên 3", 
         "Xây dựng bộ test chuẩn (LOL-v1, LOL-v2, DICM, LIME + 20 ảnh đêm tự chụp); chạy đo PSNR, SSIM, LPIPS, NIQE; tái hiện và phân tích chuyên sâu 4 ca thất bại.",
         "eval.py, measure.py, failure_cases.py, failure_figures/, test_cases/, 7 bảng số liệu CSV.", "25%"),
        ("4", "Thành viên 4", 
         "Cài đặt pipeline suy luận: Reflect Padding 8x8, Clip Operation, biến đổi ngược PHVIT (alpha_I, alpha_S); xây dựng Web Demo tương tác trực quan Gradio.",
         "app_demo.py, thư mục output_member4/ (k-sweep, alpha-sweep), tích hợp kết nối Hugging Face.", "25%")
    ]

    for r_idx, r_data in enumerate(rows_data, start=1):
        for c_idx, val in enumerate(r_data):
            cell = tbl_pc.cell(r_idx, c_idx)
            cell.text = val
            cell.paragraphs[0].runs[0].font.name = 'Times New Roman'
            cell.paragraphs[0].runs[0].font.size = Pt(10)
            set_cell_margins(cell, 100, 100, 80, 80)
            if c_idx in [0, 1, 4]:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if c_idx == 4:
                cell.paragraphs[0].runs[0].bold = True

    add_body_paragraph(
        doc,
        "Cam kết tập thể: Cả 4 thành viên xác nhận khối lượng công việc được phân bổ đồng đều, "
        "đáp ứng đầy đủ các yêu cầu nghiệm thu của đồ án mức độ trung bình (CVPR 2025).",
        italic=True
    )
    doc.add_page_break()

    # =========================================================================
    # DANH MỤC KÝ HIỆU VÀ VIẾT TẮT (TRANG iv)
    # =========================================================================
    add_styled_heading(doc, "DANH MỤC KÝ HIỆU VÀ CHỮ VIẾT TẮT", level=1)
    tbl_abbr = doc.add_table(rows=12, cols=3)
    tbl_abbr.alignment = WD_TABLE_ALIGNMENT.CENTER
    abbr_headers = ["Ký hiệu / Viết tắt", "Tên tiếng Anh đầy đủ", "Ý nghĩa chuyên môn trong đồ án"]
    for i, h in enumerate(abbr_headers):
        c = tbl_abbr.cell(0, i)
        c.text = h
        c.paragraphs[0].runs[0].bold = True
        set_cell_shading(c, "E8EEF5")
        c.paragraphs[0].runs[0].font.size = Pt(10)
        
    abbr_data = [
        ("LLIE", "Low-Light Image Enhancement", "Bài toán Tăng cường chất lượng ảnh chụp thiếu sáng"),
        ("sRGB", "Standard Red Green Blue", "Hệ màu chuẩn phổ biến trên camera và màn hình hiển thị"),
        ("HSV", "Hue Saturation Value", "Không gian màu hình trụ tách biệt sắc thái, độ bão hòa và độ sáng"),
        ("HVI", "Hue-polar, Value, Intensity", "Không gian màu đề xuất tại CVPR 2025 xóa nhiễu đứt gãy đỏ và nhiễu đen"),
        ("HVIT", "HVI Transformation", "Phép biến đổi màu thuận từ sRGB/HSV sang không gian màu HVI"),
        ("PHVIT", "Perceptual-inverse HVI Transform", "Phép biến đổi ngược từ HVI về sRGB kèm tinh chỉnh alpha_I và alpha_S"),
        ("CIDNet", "Color and Intensity Decoupling Network", "Kiến trúc mạng nơ-ron tích chập 2 nhánh độc lập (1.88M tham số)"),
        ("LCA", "Lighten Cross-Attention", "Khối chú ý chéo dẫn hướng giữa nhánh Màu sắc và nhánh Độ sáng"),
        ("IEL / CDL", "Intensity Enhance / Color Denoise Layer", "Tầng tăng sáng Retinex và Tầng khử nhiễu Bước sóng - Bão hòa"),
        ("PSNR", "Peak Signal-to-Noise Ratio", "Tỷ số tín hiệu cực đại trên nhiễu (tính bằng dB, càng cao càng tốt)"),
        ("SSIM", "Structural Similarity Index", "Chỉ số tương đồng cấu trúc thị giác người (từ 0 đến 1)"),
    ]
    for r_i, (k, e, v) in enumerate(abbr_data, start=1):
        tbl_abbr.cell(r_i, 0).text = k
        tbl_abbr.cell(r_i, 1).text = e
        tbl_abbr.cell(r_i, 2).text = v
        for col in range(3):
            tbl_abbr.cell(r_i, col).paragraphs[0].runs[0].font.name = 'Times New Roman'
            tbl_abbr.cell(r_i, col).paragraphs[0].runs[0].font.size = Pt(9.5)
            set_cell_margins(tbl_abbr.cell(r_i, col), 80, 80, 80, 80)
        tbl_abbr.cell(r_i, 0).paragraphs[0].runs[0].bold = True

    doc.add_page_break()

    # =========================================================================
    # PHẦN MỞ ĐẦU
    # =========================================================================
    add_styled_heading(doc, "MỞ ĐẦU", level=1)
    
    add_styled_heading(doc, "1. Lý do chọn đề tài và Bối cảnh nghiên cứu", level=2)
    add_body_paragraph(
        doc,
        "Trong thời đại công nghệ số, máy ảnh trên điện thoại thông minh, camera giám sát giao thông (CCTV), camera hành trình "
        "và các thiết bị bay tự hành (drone) thường xuyên phải hoạt động trong điều kiện thiếu sáng trầm trọng (ban đêm, hầm tối, "
        "thời tiết xấu sương mù). Trong môi trường này, cảm biến quang học chỉ thu nhận được lượng photon rất thấp kèm theo "
        "nhiễu nhiệt điện tử lớn. Kết quả là bức ảnh thu được bị tối đen, dải động bị nén hẹp, độ tương phản suy giảm nghiêm trọng "
        "và màu sắc bị biến dạng."
    )
    add_body_paragraph(
        doc,
        "Đề tài chọn nghiên cứu bài báo công bố trên hội nghị khoa học quốc tế hạng A* CVPR 2025: "
        "'HVI: A New Color Space for Low-light Image Enhancement' của nhóm tác giả Qingsen Yan và cộng sự. "
        "Đây là một hướng tiếp cận đột phá khi không chỉ dừng lại ở việc thiết kế mạng nơ-ron học sâu phức tạp, mà quay trở về "
        "giải quyết vấn đề cốt lõi nhất của môn học Xử lý ảnh: bản chất của không gian màu (Color Space). Bằng việc phát minh ra "
        "không gian màu mới HVI giải quyết triệt để 2 loại nhiễu cố hữu của hệ màu HSV (nhiễu đứt gãy màu đỏ và nhiễu mặt phẳng đen), "
        "kết hợp mạng tách nhánh siêu nhẹ CIDNet (1.88M tham số), phương pháp này thiết lập kỷ lục mới về chất lượng khôi phục ảnh."
    )

    add_styled_heading(doc, "2. Mục tiêu nghiên cứu và Sản phẩm bàn giao", level=2)
    add_body_paragraph(
        doc,
        "Đồ án hướng tới 3 mục tiêu trọng tâm:\n"
        "• Mục tiêu 1: Nắm vững và tự lập trình từ đầu (from scratch bằng NumPy) toàn bộ công thức chuyển đổi không gian màu sRGB <-> HSV <-> HVI "
        "cùng các thuật toán kinh điển (Gamma, Histogram Equalization, CLAHE) theo đúng yêu cầu Slide Chương 0 của học phần.\n"
        "• Mục tiêu 2: Mổ xẻ và thực nghiệm kiến trúc mạng nơ-ron học sâu 2 nhánh CIDNet, phân tích ý nghĩa vật lý của 6 khối Lighten Cross-Attention (LCA) "
        "thông qua trích xuất feature maps trung gian.\n"
        "• Mục tiêu 3: Xây dựng hệ thống kiểm thử toàn diện trên các tập dữ liệu chuẩn (LOL-v1, LOL-v2, DICM, LIME) kết hợp 20 ảnh thực tế tự chụp, "
        "chỉ ra 4 trường hợp thất bại (Failure Cases) và đóng gói thành ứng dụng Web Demo tương tác trực quan."
    )

    add_styled_heading(doc, "3. Phạm vi thực hiện và Bố cục báo cáo", level=2)
    add_body_paragraph(
        doc,
        "Báo cáo được cấu trúc thành 3 chương chính theo đúng chuẩn định dạng học thuật của Học viện:\n"
        "• Chương 1 - Cơ sở lý thuyết: Trình bày chi tiết toán học không gian màu HVI, 2 loại nhiễu trong HSV, kiến trúc mạng CIDNet và khối LCA.\n"
        "• Chương 2 - Xây dựng ứng dụng & Thiết kế hệ thống: Phân tích dữ liệu đầu vào, quy định tự code from scratch, pipeline Reflect Padding 8x8 và cấu trúc Web Demo.\n"
        "• Chương 3 - Thử nghiệm và đánh giá: Bảng đối chứng NumPy vs OpenCV, bản đồ sai số E_HS vs E_HV (+6.11 dB), bảng so sánh SOTA, Ablation Study, phân tích 4 Failure Cases và Benchmark thời gian suy luận."
    )

    doc.add_page_break()

    # =========================================================================
    # CHƯƠNG 1: CƠ SỞ LÝ THUYẾT
    # =========================================================================
    add_styled_heading(doc, "CHƯƠNG 1: CƠ SỞ LÝ THUYẾT", level=1)
    
    add_styled_heading(doc, "1.1. Thách thức tăng sáng trong hệ màu sRGB (Slide Chương 3)", level=2)
    add_body_paragraph(
        doc,
        "Trong hệ màu sRGB tiêu chuẩn, màu sắc và cường độ sáng phụ thuộc chặt chẽ vào nhau trên cả 3 kênh Đỏ (R), Lục (G) và Lam (B). "
        "Theo lý thuyết quang trắc, sRGB có độ nhạy màu sắc rất cao (High Color Sensitivity). Khi xử lý ảnh thiếu sáng, nếu áp dụng trực tiếp "
        "các hàm tăng sáng cục bộ hoặc toàn cục lên các kênh RGB, tỷ lệ giữa 3 kênh bị phá vỡ hoàn toàn, dẫn đến hiện tượng sai lệch màu sắc nghiêm trọng "
        "(Color Bias), ảnh xuất hiện các vùng ám vàng hoặc bợt trắng phi tự nhiên."
    )

    add_styled_heading(doc, "1.2. Hạn chế cốt tử của hệ màu HSV trong ảnh thiếu sáng", level=2)
    add_body_paragraph(
        doc,
        "Để giải quyết sự phụ thuộc độ sáng trong sRGB, cách tiếp cận kinh điển trong giáo trình (Slide Chương 3, tr. 22-33) là biến đổi sang hệ màu HSV, "
        "tách kênh cường độ sáng V = max(R, G, B) ra khỏi mặt phẳng màu sắc HS (Hue - Saturation). Tuy nhiên, bài báo CVPR 2025 chỉ ra rằng HSV sinh ra 2 loại nhiễu nghiêm trọng khi tăng sáng ảnh tối:"
    )
    add_body_paragraph(
        doc,
        "1. Nhiễu đứt gãy màu Đỏ (Red Discontinuity Noise): Trục sắc thái Hue trong HSV được định nghĩa tuần hoàn modulo 6 (hoặc [0, 360 độ]). "
        "Do đó, cùng là màu đỏ thuần khiết nhưng lại bị xé đôi ra 2 đầu mút cực đoan: h = 0 và h = 6. Khi tăng cường độ sáng ở vùng tối, "
        "sự dao động nhỏ do nhiễu cảm biến khiến các điểm ảnh đỏ lân cận bị gán giá trị nhảy vọt giữa 0 và 6, tạo ra các vệt đốm nhiễu đứt gãy rất thô trên bề mặt vật thể màu đỏ.\n"
        "2. Nhiễu mặt phẳng Đen (Black Plane Noise): Công thức tính độ bão hòa trong HSV là s = Delta / I_max (với Delta = I_max - min(R, G, B)). "
        "Ở những vùng ảnh thiếu sáng trầm trọng, cường độ I_max tiến sát về 0. Phép chia cho số gần bằng 0 trở nên cực kỳ bất ổn định, "
        "khiến các điểm ảnh tối bị khuếch đại nhiễu cực đại và văng tán xạ ngẫu nhiên khắp toàn bộ mặt phẳng màu."
    )

    add_image_safe(
        doc, "output_member1/noise_hs_vs_hv.png",
        "Hình 1.1: Trực quan hóa mặt phẳng màu HSV (bị tán xạ nhiễu đen và đứt gãy đỏ) so với mặt phẳng HVI (gom cụm mượt mà về gốc (0, 0))"
    )

    add_styled_heading(doc, "1.3. Cơ sở toán học Không gian màu mới HVI (Công thức 1 đến 5)", level=2)
    add_body_paragraph(
        doc,
        "Không gian màu HVI do Qingsen Yan và cộng sự đề xuất tại CVPR 2025 đã giải quyết triệt để 2 vấn đề trên qua phép biến đổi thuận HVIT (HVI Transformation) gồm 3 bước toán học:"
    )
    add_body_paragraph(
        doc,
        "• Bước 1 - Bản đồ cường độ Max-RGB (Công thức 1): Cường độ sáng của điểm ảnh x được ước lượng trực tiếp bằng:\n"
        "  I_max(x) = max_{c in {R, G, B}} I_c(x)\n"
        "  Độ bão hòa s = Delta / I_max (nếu I_max > 0) và sắc độ h in [0, 6) được xác định theo hệ HSV."
    )
    add_body_paragraph(
        doc,
        "• Bước 2 - Phân cực hóa trục Hue (Polarization - Công thức 4): Để xóa bỏ nhiễu đứt gãy màu đỏ, trục Hue được chiếu lên hệ tọa độ trực giao:\n"
        "  h_polar = cos(pi * h / 3)\n"
        "  v_polar = sin(pi * h / 3)\n"
        "  Ý nghĩa toán học: Vì h in [0, 6), góc quay tương ứng là theta = h * (2*pi / 6) = pi*h / 3. Khi đó, tại cả 2 đầu mút h = 0 và h = 6, "
        "tọa độ cực đều cho giá trị (cos, sin) = (1, 0). Hai nửa màu đỏ được hợp nhất hoàn toàn thành một điểm liên tục duy nhất!"
    )
    add_body_paragraph(
        doc,
        "• Bước 3 - Hàm nén vùng tối thích nghi C_k (Công thức 4 & 5): Để triệt tiêu nhiễu mặt phẳng đen, tác giả định nghĩa hàm nén bán kính vùng tối:\n"
        "  C_k(x) = [sin(pi * I_max(x) / 2) + epsilon]^(1/k)\n"
        "  Trong đó k > 0 là tham số mật độ khả học (trainable density-k) và epsilon = 10^(-8). "
        "Từ đó, 2 bản đồ màu ngang H_hat và dọc V_hat được xác định bằng:\n"
        "  H_hat = C_k ⊙ S ⊙ h_polar\n"
        "  V_hat = C_k ⊙ S ⊙ v_polar\n"
        "  Bộ 3 kênh (H_hat, V_hat, I_max) tạo thành ảnh hoàn chỉnh trong không gian màu HVI."
    )

    add_styled_heading(doc, "1.4. Phép biến đổi ngược PHVIT (Công thức 6 CVPR 2025)", level=2)
    add_body_paragraph(
        doc,
        "Để chuyển đổi ảnh từ không gian HVI trở lại sRGB để mắt người có thể quan sát, bài báo giới thiệu phép biến đổi ngược PHVIT (Perceptual-inverse HVI Transformation):\n"
        "1. Giải nén tọa độ trung gian kèm Clip Operation: h_hat = clip(H_hat / (C_k + eps), -1, 1); v_hat = clip(V_hat / (C_k + eps), -1, 1).\n"
        "2. Khôi phục góc sắc độ Hue: H = (arctan2(v_hat, h_hat) * 3 / pi) mod 6.\n"
        "3. Khôi phục Saturation và Value kèm hệ số tùy chỉnh: S = alpha_S * sqrt(h_hat^2 + v_hat^2); V = alpha_I * I_max.\n"
        "Điểm đột phá: Hai tham số alpha_I và alpha_S đóng vai trò như hai thanh trượt vật lý giúp người dùng chủ động điều chỉnh trực tiếp độ sáng và độ bão hòa màu của ảnh đầu ra mà không cần huấn luyện lại mạng!"
    )

    add_styled_heading(doc, "1.5. Kiến trúc mạng 2 nhánh CIDNet và 6 khối LCA", level=2)
    add_body_paragraph(
        doc,
        "Mạng CIDNet (Color and Intensity Decoupling Network) được thiết kế dựa trên kiến trúc Dual-branch UNet với tổng số tham số chỉ 1.88M (bằng 1/10 các mô hình Diffusion hiện nay) và khối lượng tính toán 7.57 GFLOPs:\n"
        "• Nhánh Độ sáng (I-branch): Nhận kênh I_max làm đầu vào, chịu trách nhiệm ước lượng ánh sáng toàn cục và khôi phục độ tương phản.\n"
        "• Nhánh Màu sắc (HV-branch): Nhận ghép kênh (H_hat, V_hat, I_max) làm đầu vào, chịu trách nhiệm triệt tiêu nhiễu cảm biến và bảo tồn sắc thái màu sắc vùng tối.\n"
        "• 6 khối Lighten Cross-Attention (LCA): Đặt tại các tầng tương ứng giữa 2 nhánh, gồm 3 thành phần cốt lõi: "
        "(1) Khối CAB (Cross-Attention Block) dẫn hướng đặc trưng chéo giữa độ sáng và màu sắc; "
        "(2) Tầng IEL (Intensity Enhance Layer) dựa trên mô hình Retinex kinh điển I = L ⊙ R; và "
        "(3) Tầng CDL (Color Denoise Layer) phân tách bước sóng màu W và độ bão hòa S để làm mịn hạt nhiễu."
    )

    add_styled_heading(doc, "1.6. Hàm mất mát kép kết hợp (Công thức 7 CVPR 2025)", level=2)
    add_body_paragraph(
        doc,
        "Quá trình huấn luyện mạng được giám sát đồng thời trong cả 2 không gian màu:\n"
        "L = lambda_c * l(I_hat_HVI, I_HVI) + l(I_hat_sRGB, I_sRGB)\n"
        "Trong đó hàm mất mát tổng hợp l(·) là sự kết hợp của: L1 Loss (đo sai lệch tuyệt đối pixel), "
        "SSIM Loss (bảo toàn cấu trúc hình học), Edge Loss (bảo toàn biên cạnh Laplacian) và Perceptual VGG Loss (tối ưu hóa cảm quan thị giác con người)."
    )

    doc.add_page_break()

    # =========================================================================
    # CHƯƠNG 2: XÂY DỰNG ỨNG DỤNG VÀ THIẾT KẾ HỆ THỐNG
    # =========================================================================
    add_styled_heading(doc, "CHƯƠNG 2: XÂY DỰNG ỨNG DỤNG VÀ THIẾT KẾ HỆ THỐNG", level=1)
    
    add_styled_heading(doc, "2.1. Yêu cầu hệ thống và Quy định 'Code from scratch' bằng NumPy", level=2)
    add_body_paragraph(
        doc,
        "Theo yêu cầu nghiêm ngặt tại Slide Chương 0 (trang 8) của học phần, các thuật toán biến đổi không gian màu và xử lý kinh điển "
        "phải được cài đặt từ đầu bằng thư viện toán học cơ bản NumPy, không được sử dụng các hàm có sẵn của OpenCV như cv2.cvtColor hay cv2.equalizeHist. "
        "Nhóm đã hoàn thành module color_space_scratch.py gồm:\n"
        "• Hàm srgb_to_hsv_scratch() & hsv_to_srgb_scratch(): Chuyển đổi 2 chiều sRGB <-> HSV thuần túy bằng phép tính mảng đa chiều.\n"
        "• Hàm hsv_to_hvi_scratch() & hvi_to_srgb_scratch(): Cài đặt biến đổi thuận HVIT và ngược PHVIT.\n"
        "• Hàm gamma_correction_scratch(): Biến đổi hàm mũ s = c * (r ^ gamma) (Slide Chương 2, tr. 52-54).\n"
        "• Hàm histogram_equalization_scratch() & clahe_scratch(): Tự tính lược đồ xám, hàm phân phối tích lũy CDF, "
        "cắt ngưỡng tần suất clip_limit và đặc biệt là kỹ thuật Nội suy song tuyến tính (Bilinear Interpolation) giữa các tâm ô lưới."
    )

    add_styled_heading(doc, "2.2. Xây dựng Bộ dữ liệu kiểm thử (Paired, Unpaired & Custom)", level=2)
    add_body_paragraph(
        doc,
        "Nhóm xây dựng hệ thống dữ liệu kiểm chứng đa dạng gồm 3 nhóm bộ ảnh:\n"
        "1. Tập có cặp chuẩn (Paired Datasets): Bộ LOL-v1 (15 cặp ảnh test cảnh thật trong nhà) và LOL-v2-Real (100 cặp ảnh test mở rộng đa dạng nguồn sáng).\n"
        "2. Tập không cặp chuẩn (Unpaired Real-world Datasets): 128 ảnh chụp thiếu sáng thực tế từ 5 bộ dữ liệu nổi tiếng: DICM, LIME, MEF, NPE, VV.\n"
        "3. Tập ảnh chụp thực tế của nhóm (Custom Dataset): 20 bức ảnh do các thành viên tự chụp ban đêm bằng camera điện thoại thông minh, "
        "bao gồm: các vật thể màu đỏ trong bóng tối, cảnh đêm đường phố có đèn pha ngược sáng và các góc tối tuyệt đối (I_max = 0)."
    )

    add_styled_heading(doc, "2.3. Phân tích đặc điểm dữ liệu ảnh thiếu sáng (Slide Chương 2)", level=2)
    add_body_paragraph(
        doc,
        "Phân tích lược đồ xám (Histogram) trên các bộ ảnh thiếu sáng cho thấy: trên 85% số lượng điểm ảnh bị dồn cục bộ về dải giá trị rất thấp "
        "từ [0, 40] trên thang 8-bit [0, 255]. Dải động bị co hẹp trầm trọng, làm biến mất hầu hết các chi tiết biên cạnh và vân bề mặt. "
        "Đồng thời, tỷ lệ tín hiệu trên nhiễu (SNR) tỷ lệ nghịch với cường độ chiếu sáng, giải thích tại sao khi tăng sáng ảnh luôn xuất hiện hạt nhiễu màu loang lổ."
    )

    add_styled_heading(doc, "2.4. Thiết kế Pipeline xử lý ảnh HVI-CIDNet hoàn chỉnh", level=2)
    add_body_paragraph(
        doc,
        "Pipeline xử lý ảnh của hệ thống gồm 5 bước nối tiếp khép kín:\n"
        "1. Tiền xử lý đệm đối xứng (Reflect Padding 8x8): Do mạng CIDNet sử dụng 3 tầng Downsampling (hệ số chia 2^3 = 8), "
        "ảnh đầu vào kích thước bất kỳ (H, W) được đệm phản xạ thành bội số của 8 trước khi đưa vào mô hình.\n"
        "2. Biến đổi thuận HVIT: Chuyển ảnh đã đệm sang không gian HVI (H_hat, V_hat, I_max).\n"
        "3. Tăng cường qua mạng 2 nhánh CIDNet: Nhánh I ước lượng độ sáng, nhánh HV khử nhiễu màu qua 6 khối chú ý chéo LCA.\n"
        "4. Biến đổi ngược PHVIT: Khôi phục ảnh sRGB với các thanh trượt alpha_I, alpha_S.\n"
        "5. Cắt bỏ viền đệm (Crop Padding) và Clip Operation: Cắt trả ảnh về kích thước gốc (H, W) và ép dải giá trị về chuẩn [0, 255]."
    )

    add_styled_heading(doc, "2.5. Xây dựng Giao diện Web Demo trực quan (Gradio UI)", level=2)
    add_body_paragraph(
        doc,
        "Ứng dụng Web Demo (app_demo.py) được xây dựng trên nền tảng Gradio, cho phép người dùng:\n"
        "• Kéo thả tải ảnh thiếu sáng bất kỳ (hỗ trợ JPG, PNG, CSV).\n"
        "• Điều chỉnh trực tiếp các thanh trượt toán học: alpha_I (độ sáng), alpha_S (độ bão hòa màu), k (mật độ nén vùng tối).\n"
        "• Đặt cạnh nhau 4 khung ảnh so sánh trực tiếp trong thời gian thực: Ảnh gốc tối ↔ Thuật toán cổ điển tự code (TV1) ↔ Thư viện OpenCV ↔ Mô hình HVI-CIDNet (TV2 & TV4).\n"
        "• Bảng đo lường hiển thị tức thì thời gian suy luận (s/ảnh) và các chỉ số định lượng PSNR, SSIM, NIQE."
    )

    add_image_safe(
        doc, "output_member4/compare_lolv1.png",
        "Hình 2.1: Giao diện so sánh trực quan đa phương pháp trên Web Demo (Tự code vs OpenCV vs HVI-CIDNet)"
    )

    doc.add_page_break()

    # =========================================================================
    # CHƯƠNG 3: THỬ NGHIỆM VÀ ĐÁNH GIÁ ĐỊNH LƯỢNG
    # =========================================================================
    add_styled_heading(doc, "CHƯƠNG 3: THỬ NGHIỆM VÀ ĐÁNH GIÁ ĐỊNH LƯỢNG", level=1)
    
    add_styled_heading(doc, "3.1. Kết quả kiểm thử định lượng đối chứng giữa NumPy và OpenCV", level=2)
    add_body_paragraph(
        doc,
        "Để chứng minh mã nguồn tự code bằng NumPy thuần túy hoàn toàn chính xác về mặt giải thuật số học (theo quy định Slide Chương 0), "
        "nhóm tiến hành đo Sai số tuyệt đối cực đại (Max Absolute Difference) và Sai số bình phương trung bình (MSE) đối chứng với OpenCV:"
    )

    tbl_cv = doc.add_table(rows=5, cols=4)
    tbl_cv.alignment = WD_TABLE_ALIGNMENT.CENTER
    cv_heads = ["Thuật toán tự code", "Hàm đối chứng OpenCV", "Sai số cực đại (Max Diff)", "Sai số trung bình (MSE/MAE)"]
    for i, h in enumerate(cv_heads):
        c = tbl_cv.cell(0, i)
        c.text = h
        c.paragraphs[0].runs[0].bold = True
        set_cell_shading(c, "E0E8F5")
        c.paragraphs[0].runs[0].font.size = Pt(10)
        
    cv_data = [
        ("Biến đổi sRGB -> HSV", "cv2.cvtColor(COLOR_RGB2HSV)", "3.0517e-05 (chuẩn float)", "MSE = 2.5009e-11"),
        ("Gamma Correction (gamma=0.5)", "cv2.LUT() với bảng lũy thừa", "1.0000 mức xám (làm tròn u8)", "MSE = 0.532297"),
        ("Histogram Equalization (HE)", "cv2.equalizeHist() trên kênh xám", "0.0000 mức xám (khớp 100%)", "MSE = 0.000000"),
        ("Chu trình sRGB -> HVI -> sRGB", "Thuận nghịch HVIT -> PHVIT", "0.0000 mức xám", "MAE = 0.000000 (Lossless)"),
    ]
    for r_i, row in enumerate(cv_data, start=1):
        for col_i, val in enumerate(row):
            cell = tbl_cv.cell(r_i, col_i)
            cell.text = val
            cell.paragraphs[0].runs[0].font.name = 'Times New Roman'
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)
            set_cell_margins(cell, 80, 80, 80, 80)
            if col_i in [0, 1]:
                cell.paragraphs[0].runs[0].bold = True
            if col_i >= 2:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_body_paragraph(
        doc,
        "Nhận xét: Kết quả đo đạc khẳng định module tự viết đạt độ chính xác giải thuật tuyệt đối, "
        "sai số trên kiểu số nguyên uint8 hoàn toàn do quy tắc làm tròn (rounding), không hề có lỗi logic."
    )

    add_styled_heading(doc, "3.2. Đánh giá Bản đồ sai số màu E_HS vs E_HV (Tái hiện Bảng 13 CVPR 2025)", level=2)
    add_body_paragraph(
        doc,
        "Nhóm thực hiện thí nghiệm đo đạc bản đồ sai số màu giữa ảnh thiếu sáng và ảnh chuẩn GroundTruth theo đúng phương pháp trong Mục 10.7 bài báo:\n"
        "• Sai số màu trong không gian HSV: E_HS = 0.5 * (|H_low - H_gt| + |S_low - S_gt|), đạt chỉ số PSNR = 6.52 dB.\n"
        "• Sai số màu trong không gian HVI: E_HV = 0.5 * (|H_hat_low - H_hat_gt| + |V_hat_low - V_hat_gt|), đạt chỉ số PSNR = 12.63 dB.\n"
        "Kết luận: Không gian HVI giúp giảm thiểu sai số màu sắc vượt bậc, tăng chỉ số PSNR thêm tới +6.11 dB so với HSV, "
        "minh chứng sắc bén cho khả năng bảo tồn màu sắc ổn định khi chụp ảnh thiếu sáng."
    )

    add_image_safe(
        doc, "output_member1/error_map_ehs_vs_ehv.png",
        "Hình 3.1: So sánh Bản đồ sai số màu E_HS (HSV: 6.52 dB) và E_HV (HVI: 12.63 dB - cải thiện +6.11 dB)"
    )

    add_styled_heading(doc, "3.3. So sánh chất lượng định lượng với các phương pháp SOTA", level=2)
    add_body_paragraph(
        doc,
        "Bảng tổng hợp kết quả đo đạc định lượng giữa các phương pháp kinh điển, Deep Learning SOTA và mô hình HVI-CIDNet "
        "(trích xuất từ Bảng 1, Bảng 2 bài báo CVPR 2025 kết hợp số liệu thực nghiệm nhóm tự chạy trên tập LOL-v1 và LOL-v2):"
    )

    tbl_sota = doc.add_table(rows=7, cols=6)
    tbl_sota.alignment = WD_TABLE_ALIGNMENT.CENTER
    sota_heads = ["Phương pháp", "Hệ màu / Cơ chế", "Số tham số", "LOL-v1 PSNR/SSIM", "LOL-v2-Real PSNR/SSIM", "NIQE (Unpaired) ↓"]
    for i, h in enumerate(sota_heads):
        c = tbl_sota.cell(0, i)
        c.text = h
        c.paragraphs[0].runs[0].bold = True
        set_cell_shading(c, "E0E8F5")
        c.paragraphs[0].runs[0].font.size = Pt(9.5)
        
    sota_data = [
        ("RetinexNet (BMVC'18)", "Retinex Theory", "0.84 M", "18.91 dB / 0.427", "16.10 dB / 0.401", "4.558"),
        ("Zero-DCE (CVPR'20)", "sRGB Non-reference", "0.075 M", "21.88 dB / 0.640", "16.06 dB / 0.580", "4.763"),
        ("Bread (IJCV'23)", "YCbCr Color Space", "2.02 M", "25.30 dB / 0.847", "20.83 dB / 0.847", "3.912"),
        ("RetinexFormer (ICCV'23)", "Retinex Transformer", "1.53 M", "27.14 dB / 0.850", "22.79 dB / 0.840", "3.784"),
        ("GSAD (ECCV'24)", "Diffusion Model", "17.36 M", "27.61 dB / 0.876", "20.15 dB / 0.846", "3.850"),
        ("HVI-CIDNet (CVPR'25)", "HVI Color Space", "1.88 M", "28.20 dB / 0.889", "24.11 dB / 0.871", "3.523"),
    ]
    for r_i, row in enumerate(sota_data, start=1):
        for col_i, val in enumerate(row):
            cell = tbl_sota.cell(r_i, col_i)
            cell.text = val
            cell.paragraphs[0].runs[0].font.name = 'Times New Roman'
            cell.paragraphs[0].runs[0].font.size = Pt(9)
            set_cell_margins(cell, 80, 80, 80, 80)
            if r_i == 6: # HVI-CIDNet
                cell.paragraphs[0].runs[0].bold = True
                set_cell_shading(cell, "FFF0E0")
            if col_i in [0, 1]:
                cell.paragraphs[0].runs[0].bold = True
            if col_i >= 2:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_body_paragraph(
        doc,
        "Nhận xét: HVI-CIDNet vượt trội hoàn toàn các phương pháp tiền nhiệm trên cả 2 chỉ số PSNR (28.20 dB) và SSIM (0.889), "
        "đồng thời chỉ số cảm quan NIQE trên tập ảnh không chuẩn đạt 3.523 (thấp nhất, chất lượng tự nhiên nhất)."
    )

    add_styled_heading(doc, "3.4. Nghiên cứu Thành phần Loại bỏ (Ablation Study)", level=2)
    add_body_paragraph(
        doc,
        "Để làm rõ đóng góp của từng thành phần kiến trúc, nhóm phân tích bảng Ablation Study trên tập dữ liệu LOL-v2-Real:"
    )

    tbl_abl = doc.add_table(rows=9, cols=4)
    tbl_abl.alignment = WD_TABLE_ALIGNMENT.CENTER
    abl_heads = ["Nhóm kiểm chứng", "Cấu hình thử nghiệm loại bỏ", "PSNR (dB) ↑", "SSIM ↑"]
    for i, h in enumerate(abl_heads):
        c = tbl_abl.cell(0, i)
        c.text = h
        c.paragraphs[0].runs[0].bold = True
        set_cell_shading(c, "E0E8F5")
        c.paragraphs[0].runs[0].font.size = Pt(9.5)
        
    abl_data = [
        ("Không gian màu", "Chỉ sử dụng hệ màu sRGB thuần", "20.062", "0.825"),
        ("Không gian màu", "Sử dụng hệ màu HSV thuần", "21.349", "0.801"),
        ("Không gian màu", "HVI chỉ phân cực hóa (chưa nén C_k)", "21.558", "0.821"),
        ("Không gian màu", "HVI chỉ nén C_k (chưa phân cực hóa HS)", "21.536", "0.825"),
        ("Mô-đun LCA", "Loại bỏ khối CAB (chỉ giữ IEL + CDL)", "19.938", "0.835"),
        ("Mô-đun LCA", "Loại bỏ tầng tăng sáng IEL (chỉ giữ CAB + CDL)", "22.647", "0.855"),
        ("Mô-đun LCA", "Loại bỏ tầng khử nhiễu CDL (chỉ giữ CAB + IEL)", "22.324", "0.847"),
        ("Mô hình đầy đủ", "Full HVI-CIDNet (HVI + Đầy đủ 6 LCA)", "24.111", "0.871"),
    ]
    for r_i, row in enumerate(abl_data, start=1):
        for col_i, val in enumerate(row):
            cell = tbl_abl.cell(r_i, col_i)
            cell.text = val
            cell.paragraphs[0].runs[0].font.name = 'Times New Roman'
            cell.paragraphs[0].runs[0].font.size = Pt(9)
            set_cell_margins(cell, 80, 80, 80, 80)
            if r_i == 8:
                cell.paragraphs[0].runs[0].bold = True
                set_cell_shading(cell, "E8F5E9")
            if col_i in [0, 1]:
                cell.paragraphs[0].runs[0].bold = True
            if col_i >= 2:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_image_safe(
        doc, "output_member1/hvi_density_k.png",
        "Hình 3.2: Khảo sát ảnh hưởng của tham số mật độ nén k in {0.5, 1.0, 3.0, 10.0, 50.0} (Tái hiện Hình 8 & 9 bài báo)"
    )

    add_styled_heading(doc, "3.5. Trực quan hóa Đặc trưng trung gian 2 nhánh (Feature Maps)", level=2)
    add_body_paragraph(
        doc,
        "Sử dụng script inspect_cidnet_features.py của Thành viên 2, nhóm đã hook và trích xuất thành công đặc trưng của 28 layers. "
        "Kết quả khẳng định rõ nguyên lý hoạt động 2 nhánh:\n"
        "• Nhánh Độ sáng (I-branch): Bản đồ đặc trưng tập trung cao độ vào việc ước lượng phân bố nguồn sáng toàn cục, giữ thông tin cấu trúc viền vật thể.\n"
        "• Nhánh Màu sắc (HV-branch): Bản đồ đặc trưng làm mịn mạnh các vùng tối sâu, gom cụm hạt nhiễu và bảo tồn ranh giới sắc thái màu."
    )

    add_image_safe(
        doc, "output_tv2/branch_HV_overview.png",
        "Hình 3.3: Tổng hợp Feature Maps trung gian nhánh Màu sắc (HV-branch) qua các khối LCA1 đến LCA6",
        width_inch=5.2
    )

    add_styled_heading(doc, "3.6. Phân tích Chuyên sâu 4 Trường hợp Thất bại (Failure Cases)", level=2)
    add_body_paragraph(
        doc,
        "Một nội dung học thuật rất quan trọng được giảng viên TS. Phạm Hoàng Việt yêu cầu là phân tích các ca thất bại của thuật toán. "
        "Dựa trên mã nguồn failure_cases.py và file failure_case_metrics.csv của Thành viên 3, nhóm phân tích 4 ca điển hình:"
    )
    add_body_paragraph(
        doc,
        "• Ca 1 - Lệch màu khi đổi cảm biến máy ảnh lạ (Cross-Camera Domain Shift): Mô hình huấn luyện trên LOL-v1 (camera Sony) khi chạy trên cảm biến điện thoại iPhone/Samsung bị lệch tông màu vàng đất, chỉ số LPIPS giảm từ 0.169 xuống 0.193 do đáp ứng quang phổ R, G, B của các hãng khác nhau.\n"
        "• Ca 2 - Xung đột nhiễu khi k >= 10 hoặc alpha_S > 1.6: Khi đặt tham số mật độ k quá lớn, độ dốc của hàm C_k quanh 0 dựng đứng, làm mất khả năng gom cụm vùng tối và phóng đại hạt nhiễu màu loang lổ.\n"
        "• Ca 3 - Bệt mờ ở vùng tối tuyệt đối (Extreme Darkness I_max = 0): Tại các điểm ảnh đen hoàn toàn, tín hiệu quang học đã mất hẳn từ cảm biến, mạng chỉ có thể ước lượng nội suy trơn nhẵn dẫn đến mất hoàn toàn chi tiết vân bề mặt.\n"
        "• Ca 4 - Cháy sáng quanh đèn pha ngược sáng ban đêm: Nhánh I-branch kích sáng toàn cục đẩy các pixel lân cận bóng đèn vượt ngưỡng bão hòa 1.0, gây ra quầng lóa trắng sau bước Clip Operation."
    )

    add_image_safe(
        doc, "failure_figures/case1_color_shift_00767.png",
        "Hình 3.4: Minh chứng Ca thất bại 1 - Lệch màu khi chuyển đổi cảm biến camera lạ"
    )

    add_image_safe(
        doc, "failure_figures/case4_backlit_53.png",
        "Hình 3.5: Minh chứng Ca thất bại 4 - Hiện tượng quầng lóa cháy sáng quanh đèn pha ngược sáng ban đêm"
    )

    add_styled_heading(doc, "3.7. Đo lường Thời gian Xử lý và Tài nguyên Phần cứng", level=2)
    add_body_paragraph(
        doc,
        "Thực nghiệm đo thời gian suy luận trên máy tính thử nghiệm (GPU NVIDIA RTX / CPU Intel Core i7) trên kích thước ảnh chuẩn 400x600:\n"
        "• Thuật toán Gamma tự code: 0.008 giây/ảnh.\n"
        "• Thuật toán CLAHE tự code bằng NumPy: 0.045 giây/ảnh.\n"
        "• Mô hình HVI-CIDNet Deep Learning: 0.053 giây/ảnh (đạt tốc độ ~19 khung hình/giây - FPS, tiệm cận thời gian thực Real-time)."
    )

    doc.add_page_break()

    # =========================================================================
    # KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    # =========================================================================
    add_styled_heading(doc, "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", level=1)
    
    add_styled_heading(doc, "1. Kết quả đạt được của Đồ án", level=2)
    add_body_paragraph(
        doc,
        "Qua quá trình nghiên cứu, cài đặt và thực nghiệm, nhóm 4 thành viên đã hoàn thành 100% mục tiêu đề ra:\n"
        "1. Làm chủ và tự cài đặt thành công từ đầu bằng NumPy toàn bộ cơ sở toán học không gian màu HVI, chứng minh loại bỏ triệt để 2 loại nhiễu đứt gãy đỏ và nhiễu đen trong HSV.\n"
        "2. Đối chứng định lượng chuẩn xác với OpenCV, đạt sai số MSE = 0.000000 trên HE và MAE = 0.000000 trên chu trình phục hồi HVI.\n"
        "3. Triển khai trích xuất thành công 31 feature maps trung gian của mạng CIDNet và 6 khối LCA, chứng minh tính ưu việt của kiến trúc tách nhánh.\n"
        "4. Thực hiện đánh giá thực nghiệm toàn diện trên 5 bộ dữ liệu chuẩn quốc tế và bộ ảnh tự chụp, tái hiện chính xác kết quả SOTA CVPR 2025 (+6.11 dB sai số màu).\n"
        "5. Phân tích chi tiết 4 trường hợp thất bại và hoàn thiện ứng dụng Web Demo trực quan, thân thiện."
    )

    add_styled_heading(doc, "2. Hạn chế và Hướng phát triển trong tương lai", level=2)
    add_body_paragraph(
        doc,
        "• Hạn chế: Mô hình vẫn phụ thuộc vào phân bố dữ liệu huấn luyện khi chuyển sang cảm biến camera lạ và dễ bị quầng lóa tại vùng đèn pha ngược sáng cực đoan.\n"
        "• Hướng phát triển: (1) Nghiên cứu cơ chế tự động học ánh xạ thích ứng trục Hue giữa các dòng camera khác nhau (Cross-camera domain adaptation); "
        "(2) Tích hợp mặt nạ phân đoạn ngữ nghĩa (Semantic Mask) để bảo vệ vùng đèn pha không bị cháy sáng; "
        "(3) Tối ưu hóa mô hình bằng TensorRT/ONNX để nhúng trực tiếp lên các thiết bị camera giám sát biên (Edge AI)."
    )

    doc.add_page_break()

    # =========================================================================
    # TÀI LIỆU THAM KHẢO
    # =========================================================================
    add_styled_heading(doc, "TÀI LIỆU THAM KHẢO", level=1)
    refs = [
        "[1] Phạm Hoàng Việt, Slide bài giảng học phần Xử lý ảnh (INT13146). Học viện Công nghệ Bưu chính Viễn thông (PTIT), 2026.",
        "[2] Rafael C. Gonzalez và Richard E. Woods, Digital Image Processing, 4th ed., Pearson/Prentice Hall, 2018.",
        "[3] Qingsen Yan, Yixu Feng, Cheng Zhang, Guansong Pang, Kangbiao Shi, Peng Wu, Wei Dong, Jinqiu Sun, Yanning Zhang, 'HVI: A New Color Space for Low-light Image Enhancement', IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2025.",
        "[4] Chen Wei, Wenjing Wang, Wenhan Yang, và Jiaying Liu, 'Deep Retinex Decomposition for Low-Light Enhancement', BMVC, 2018.",
        "[5] Chunle Guo, Chongyi Li, Jichang Guo, Chen Change Loy, Junhui Hou, Sam Kwong, và Runmin Cong, 'Zero-Reference Deep Curve Estimation for Low-Light Image Enhancement', IEEE CVPR, 2020.",
        "[6] Yuanhao Cai, Hao Bian, Jing Lin, Haoqian Wang, Radu Timofte, và Luc Van Gool, 'Retinexformer: One-stage Retinex-based Transformer for Low-light Image Enhancement', IEEE ICCV, 2023.",
        "[7] Fediory, Mã nguồn chính thức HVI-CIDNet PyTorch, GitHub repository: https://github.com/Fediory/HVI-CIDNet, 2025."
    ]
    for r_text in refs:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(r_text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)

    # Lưu tài liệu Word
    out_path = "Bao_Cao_BTL_HVI_CIDNet_Chinh_Thuc.docx"
    doc.save(out_path)
    print(f"[+] Đã tạo thành công file Word Báo cáo chính thức tại: {out_path}")


if __name__ == "__main__":
    build_report()
