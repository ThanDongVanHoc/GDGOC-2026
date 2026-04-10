from flask import Flask
import os
from .config import Config

def create_app(config_class=Config):
    # Load đường dẫn tuyệt đối tĩnh để tránh lỗi TemplateNotFound
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    # Khởi tạo App với mốc thư mục cực kỳ chính xác
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
                
    # Load configuration
    app.config.from_object(config_class)
    
    # Register blueprints
    from .routes import api_bp, pages_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
    
    return app
