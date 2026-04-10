from flask import Blueprint, request, jsonify, Response, current_app
import os
import fitz

# Import core business logic from phase4
from phase4.pdf_parser import annotate_pdf_blocks

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
        
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
        
    if file and file.filename.lower().endswith('.pdf'):
        filename = file.filename
        
        # Access config variables attached to app
        input_dir = current_app.config['INPUT_PDF_DIR']
        output_dir = current_app.config['OUTPUT_PDF_DIR']
        
        input_path = os.path.join(input_dir, filename)
        
        # Save uploaded file
        file.save(input_path)
        
        out_filename = f"annotated_{filename}"
        output_path = os.path.join(output_dir, out_filename)
        
        # Run Parser Logic
        try:
            parsed_data = annotate_pdf_blocks(input_path, output_path)
            return jsonify({
                'success': True,
                'json_data': parsed_data
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Định dạng file không hợp lệ, phải là PDF.'})

@api_bp.route('/page_image/<filename>/<int:page_id>')
def get_page_image(filename, page_id):
    input_dir = current_app.config['INPUT_PDF_DIR']
    pdf_path = os.path.join(input_dir, filename)
    
    if not os.path.exists(pdf_path):
        return "File not found", 404
        
    try:
        doc = fitz.open(pdf_path)
        if page_id < 1 or page_id > len(doc):
            return "Page out of range", 404
            
        page = doc[page_id - 1]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        doc.close()
        
        return Response(img_bytes, mimetype="image/png")
    except Exception as e:
        return str(e), 500
