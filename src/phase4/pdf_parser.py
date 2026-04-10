import fitz  # PyMuPDF
import os
import json
import sys

# Khắc phục lỗi in tiếng Việt ra Windows Console
sys.stdout.reconfigure(encoding='utf-8')

def annotate_pdf_blocks(input_pdf_path, output_pdf_path):
    """
    Đọc PDF, trích xuất cấu trúc block và vẽ bounding box:
    - Trả về object chứa thông tin page_id, width, height, text_blocks, image_blocks
    - Đồng thời xuất ra một PDF mới đã được vẽ highlight khung xanh/đỏ.
    """
    pdf_data = []
    
    try:
        # Mở file PDF
        doc = fitz.open(input_pdf_path)
        print(f"Đang xử lý: {input_pdf_path}")
    except Exception as e:
        print(f"Lỗi khi mở file {input_pdf_path}: {e}")
        return None

    # Lặp qua từng trang trong PDF
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Tạo object chứa dữ liệu layout của trang
        page_dict = {
            "page_id": page_num + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "text_blocks": [],
            "image_blocks": []
        }
        
        # Lấy toàn bộ thông tin block của trang dưới dạng dict
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            bbox = block["bbox"] # Dạng tuple (x0, y0, x1, y1)
            fitz_bbox = fitz.Rect(bbox)
            block_type = block.get("type", 0)
            
            if block_type == 0:  # Type 0: Text Block
                text_content = ""
                # Ghép các text span lại với nhau
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_content += span["text"] + " "
                            
                page_dict["text_blocks"].append({
                    "content": text_content.strip(),
                    "bbox": list(bbox)
                })
                # Vẽ màu Xanh lá cho Text (RGB: 0, 1, 0)
                page.draw_rect(fitz_bbox, color=(0, 1, 0), width=1.5)
                
            elif block_type == 1:  # Type 1: Image Block
                page_dict["image_blocks"].append({
                    "bbox": list(bbox)
                })
                # Vẽ màu Đỏ cho Image (RGB: 1, 0, 0)
                page.draw_rect(fitz_bbox, color=(1, 0, 0), width=1.5)
                
        pdf_data.append(page_dict)
                
    # Lưu file PDF layout kết quả
    doc.save(output_pdf_path)
    doc.close()
    print(f"Đã lưu file PDF có khung layout tại: {output_pdf_path}")
    
    return pdf_data