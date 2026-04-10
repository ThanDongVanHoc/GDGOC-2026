import sys
import os

# Fix encoding issues in Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Ensure the 'src' directory itself is in path so we can import phase4
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from web_app import create_app

app = create_app()

if __name__ == '__main__':
    print("Khởi động Agentic UI tại: http://localhost:5000 (Modular Architecture)")
    app.run(host='0.0.0.0', port=5000, debug=True)
