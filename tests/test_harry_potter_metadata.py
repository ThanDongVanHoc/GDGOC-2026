import os
import sys

# Add parent directory to sys.path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase1.metadata_extractor import extract_metadata_from_brief

raw_brief = """
Chào team bản địa hóa dự án OmniLocal,

Tháng này chúng ta sẽ thầu bộ truyện "Harry Potter & The Sorcerer's Stone" phiên bản truyện tranh thiếu nhi.
Thông tin dự án như sau:
- Dịch từ tiếng Anh (EN) sang tiếng Việt (VI).
- Đối tượng độc giả: "Trẻ em và thanh thiếu niên". Nhớ dùng từ ngữ trong sáng, phong cách dịch phải phù hợp.
- Yêu cầu dịch: Phải bám sát nguyên tác (Strict), không được phóng tác hay chế cháo thêm kịch bản.

Về bản quyền thương hiệu (rất nghiêm ngặt):
1. Vui lòng giữ nguyên danh tính các nhân vật gốc, tuyệt đối không dịch sang tiếng Việt: "Harry Potter", "Hermione Granger", "Ron Weasley", "Lord Voldemort", "Hogwarts".
2. Khách hàng Warner Bros yêu cầu Không được phép chỉnh sửa hay vẽ lại hình ảnh có sẵn (no retouching).
3. Tuyệt đối không được đổi màu sắc đặc trưng của các nhân vật (ví dụ màu tóc của Ron hay vết sẹo của Harry). Khóa màu nhân vật giúp mình.
4. Nghiêm cấm team Edit vẽ đè chữ lên mặt nhân vật hay logo bản quyền của Harry Potter.

Ngoài ra, chú ý căn lề file in ấn là 2.5cm đều các góc nhé. Xin cảm ơn!
"""

def main() -> None:
    """Executes the test to extract Harry Potter project constraints."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY is not set.")
        return

    print("Sending raw brief to Gemini ...\n")
    metadata = extract_metadata_from_brief(raw_brief, api_key)
    
    print("\n[SUCCESS] Extracted GlobalMetadata Model:\n")
    # Encode as UTF-8 then decode to avoid Windows console CP1252 charmap errors
    dump = metadata.model_dump_json(indent=2)
    sys.stdout.buffer.write(dump.encode("utf-8") + b"\n")

if __name__ == "__main__":
    main()
