from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import sys

# Khắc phục lỗi in tiếng Việt
sys.stdout.reconfigure(encoding='utf-8')

# Nạp hàm xử lý PDF lúc nãy chúng ta viết
from phase4.pdf_parser import annotate_pdf_blocks

app = Flask(__name__)

# Thiết lập các đường dẫn động dựa trên app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
INPUT_DIR = os.path.join(PROJECT_ROOT, "input_pdfs")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output_pdfs")

# Đảm bảo các thư mục tồn tại
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def index():
    # Render giao diện từ file templates/index.html
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'error': 'Không tìm thấy file'})
        
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Chưa chọn file'})
        
    if file and file.filename.lower().endswith('.pdf'):
        filename = file.filename
        input_path = os.path.join(INPUT_DIR, filename)
        
        # 1. Lưu file PDF người dùng nhét vào thư mục input_pdfs
        file.save(input_path)
        
        out_filename = f"annotated_{filename}"
        output_path = os.path.join(OUTPUT_DIR, out_filename)
        
        # 2. Chạy hàm parse lúc nãy
        try:
            parsed_data = annotate_pdf_blocks(input_path, output_path)
            
            # Trả về kết quả đường dẫn PDF nội bộ và chuỗi JSON nguyên gốc để UI bắt
            return jsonify({
                'success': True,
                'pdf_url': f'/result/{out_filename}',
                'json_data': parsed_data
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Định dạng file không hợp lệ, phải là PDF.'})

@app.route('/page_image/<filename>/<int:page_id>')
def get_page_image(filename, page_id):
    import fitz
    from flask import Response
    
    # Mở pdf gốc từ input_pdfs
    pdf_path = os.path.join(INPUT_DIR, filename)
    if not os.path.exists(pdf_path):
        return "Not found", 404
        
    doc = fitz.open(pdf_path)
    if page_id < 1 or page_id > len(doc):
        return "Page not found", 404
        
    page = doc[page_id - 1]
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    doc.close()
    
    return Response(img_bytes, mimetype="image/png")

@app.route('/result/<filename>')
def get_pdf(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    print(f"Khởi động Agentic UI tại: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
