# Contributing to OmniLocal

Welcome to **OmniLocal**! This guide will get you set up and coding in under 5 minutes.

## Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Node.js 20+** — [Download](https://nodejs.org/) (only if working on frontend)
- **Docker** — [Download](https://www.docker.com/products/docker-desktop/) (optional, for full pipeline testing)
- **Git** — [Download](https://git-scm.com/)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ThanDongVanHoc/GDGOC-2026.git
cd GDGOC-2026
```

### 2. Go to Your Phase Folder

Each partner works in their own `phase{N}/` folder:

```bash
cd phase1   # or phase2, phase3, phase4, phase5
```

### 3. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Your Service

```bash
uvicorn app.main:app --reload --port 8001
```

Your service is now running at `http://localhost:8001`. Test the health check:

```bash
curl http://localhost:8001/
# {"service": "Phase 1 — Ingestion", "status": "running"}
```

### 6. Start Coding

Open `app/worker.py` — this is where you write all your logic. See the [Phase 0 Example](#phase-0-example) below to understand the full pattern.

---

## Project Structure

```
GDGOC-2026/
├── docs/                      # Documentation (read-only for partners)
│   ├── Blueprint_LangGraph.md # Full architecture spec
│   ├── CODING_CONVENTION.md   # Code standards
│   └── phases/                # Detailed specs per Phase
│
├── orchestrator/              # Orchestrator service (team lead)
├── frontend/                  # React SPA (team lead)
│
├── phase0/                    # ⭐ EXAMPLE — study this first!
├── phase1/                    # Partner 1 workspace
├── phase2/                    # Partner 2 workspace
├── phase3/                    # Partner 3 workspace
├── phase4/                    # Partner 4 workspace
├── phase5/                    # Partner 5 workspace
│
├── docker-compose.yml         # Run everything
└── .env.example               # Environment variables
```

---

## Phase 0 Example

Before starting on your Phase, **study `phase0/`** — it is a complete working example that demonstrates:

1. How your FastAPI endpoint receives a job from the Orchestrator
2. How your `worker.py` processes the job (an OpenCV task)
3. How you fire a webhook back to the Orchestrator with results
4. How to test everything locally

### Run the Phase 0 Example

```bash
cd phase0
pip install -r requirements.txt

# Terminal 1: Start the Phase 0 service
uvicorn app.main:app --reload --port 8010

# Terminal 2: Run the test (simulates Orchestrator)
python test_flow.py
```

You will see the full flow: Orchestrator sends job → Worker processes → Worker fires webhook → Orchestrator receives result.

---

## How Your Code Fits In

```
Orchestrator                          Your Worker
────────────                          ───────────

POST /api/v1/phase{N}/run ──────────▶ app/main.py
                                        │
    Your payload:                       │ Immediately returns 202
    - thread_id                         │
    - input data                        ▼
    - webhook_url                    BackgroundTasks runs:
                                        │
                                        ▼
                                     app/worker.py
                                        │
                                        │ YOUR CODE HERE
                                        │ (CV, LLM, algorithms...)
                                        │
                                        ▼
                                     POST {webhook_url}
◀─────────────── webhook ───────────    │
    Result:                             │
    - thread_id                         Done ✅
    - result: { your output }
```

### What You Write

| File | What Goes Here |
|------|---------------|
| `app/worker.py` | **All your logic.** Algorithms, LLM calls, CV processing, etc. |
| `app/main.py` | Already done for you. Don't modify unless you need extra endpoints. |
| `requirements.txt` | Add any Python packages you need. |

### What You Don't Touch

- `orchestrator/` — Team lead manages this
- `frontend/` — Team lead manages this
- Other `phase{N}/` folders — Other partners manage those
- `docs/` — Read-only reference

---

## Khi bạn cần cài thêm Thư viện mới (Dependencies)

Trong quá trình code, nếu bạn cần một thư viện Python mới (VD: `beautifulsoup4`, `numpy`), hãy tuân thủ quy trình sau:

1. Đảm bảo Terminal đang bật môi trường sinh thái ảo `(venv)`.
2. Chạy `pip install <tên-thư-viện>`.
3. **BẮT BUỘC:** Cập nhật tên thư viện vào file `requirements.txt` nằm trong thư mục Phase của bạn.
4. Khi đồng đội nhận được code mới, họ chỉ cần chạy lại file `.\install_all.ps1` ở thư mục gốc để tải bù thư viện bạn vừa thêm.

---

## Git Workflow

### Commit Messages

Format: `#phase{N}: type(scope): description`

```bash
git commit -m "#phase1: feat(parser): implement PDF bbox extraction with PyMuPDF"
git commit -m "#phase2: fix(translator): handle empty text blocks"
git commit -m "#phase3: refactor(butterfly): optimize BFS traversal"
```

### Branching

```bash
git checkout -b phase1/feature-name
# ... code ...
git push origin phase1/feature-name
# Create a Pull Request
```

---

## Running the Full Pipeline (Without Docker)

Nếu bạn là **Partner**, bạn **KHÔNG CẦN CHẠY** các Phase khác hay Orchestrator. Xin hãy đọc kĩ mục [Môi trường Độc Lập của Partner](#môi-trường-độc-lập-của-partner) để test tự do.

Tuy nhiên, nếu bạn muốn test thử (hoặc Team Lead muốn chạy frontend để test luồng hoàn chỉnh), bạn có thể cài đặt toàn bộ hệ thống bằng 1 click:

**1. Mở PowerShell ở thư mục gốc và chạy Cài Đặt:**
```powershell
.\install_all.ps1
```
*(Script này sẽ tạo môi trường ảo dùng chung và tự động cài Node Modules, Python Packages cho TẤT CẢ các thư mục trong dự án, bạn có thể đi pha một ly cafe trong lúc chờ.)*

**2. Bật toàn bộ hệ thống:**
```powershell
.\start_all.ps1
```
*(Script sẽ tự động mở 7 cửa sổ riêng biệt để chạy Orchestrator, Frontend, và 5 Worker Node! Cực kỳ trực quan!)*

---

## 💡 Langchain & LangGraph nằm ở đâu? Tại sao Partner không thấy?

Nếu các Partner thắc mắc tại sao mình không thấy code LangChain hay LangGraph: **Đây là chủ ý thiết kế của kiến trúc OmniLocal.**

1. **Orchestrator** (do Team Lead code) là hệ thống DUY NHẤT cần import `langgraph` và `langchain`. Nhiệm vụ của nó là điều phối tiến trình.
2. **Partner Worker** (do bạn code) chỉ là một API Service độc lập (FastAPI). Nhiệm vụ của bạn là nhận dữ liệu → xử lý nặng bằng Python (có thể dùng LLM, OpenCV) → trả webhook.

### Lợi ích:
- Bạn **KHÔNG CẦN** học về kiến trúc Agentic phân tán, LangGraph nodes/edges phức tạp.
- Bạn chỉ cần tập trung vào chuyên môn Phase của mình.

---

## Môi trường Độc Lập của Partner

**Làm sao để test nếu tôi (Partner) không chạy Orchestrator?**

Mọi thư mục Phase đều chứa file `test_flow.py`. File này đóng vai trò là một "Orchestrator giả lập" siêu nhỏ.
Thay vì chạy 6 Terminal để test 1 Phase, bạn chỉ cần 2 Terminal:

```bash
# Terminal 1: Chạy Phase API của bạn
cd phase1
uvicorn app.main:app --reload --port 8001

# Terminal 2: Chạy file giả lập Orchestrator
python test_flow.py
```
`test_flow.py` sẽ gửi data chuẩn cho bạn, và mở sẵn Server hứng Hook để in kết quả của bạn ra màn hình. Bạn sẽ code liên tục theo cách này!

---

## Need Help?

1. Read `docs/Blueprint_LangGraph.md` — especially **Section 6: Critical Guide for Partners**
2. Read your Phase spec in `docs/phases/Phase{N}_*.md`
3. Study the `phase0/` example
4. Ask the team lead

---

_Happy coding! 🚀_
