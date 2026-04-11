# OmniLocal - Developer Quick Start Guide

Welcome to the OmniLocal project! This guide provides a concise, step-by-step workflow for project partners to onboard quickly, run the system locally, and begin developing their assigned modules. 

The OmniLocal system consists of a Frontend interface (React) and multiple Microservices (FastAPI) orchestrated via LangGraph. To simplify collaboration, local development utilizes automated PowerShell scripts.

---

## 🚀 1. Local System Initialization

The system leverages a script-based automation approach to install dependencies and run services without the overhead of Docker during the prototype phase.

### A. Environment Setup (First-time or upon dependency changes)
Open a terminal at the root of `GDGOC-2026` and run:
```powershell
.\install_all.ps1
```
*This script will automatically install `node_modules` for the Frontend and create isolated Python virtual environments (`venv`) for all Backend microservices.*

### B. Launching the Project
To start all services concurrently, run:
```powershell
.\start_all.ps1
```
*This will spawn separate PowerShell windows for the Frontend (Port 3000), Orchestrator (Port 8000), and all Phase Workers (Ports 8001-8010).*

**Access the Frontend UI:** Open your browser and navigate to `http://localhost:3000`.

---

## 💻 2. Development Workflow

The OmniLocal architecture is heavily encapsulated. As a partner assigned to a specific Phase (e.g., Phase 2: Translation), **you only need to interact with your assigned phase directory.**

### Understanding the Lifecycle (Phase 0 as Reference)
Phase 0 serves as a complete example of the system's Orchestrator-Worker communication pattern. Here is the lifecycle you must understand:

1. **Receiving the Job (`phase0/app/main.py`):**
   The Orchestrator sends a POST request to your phase's endpoint. The boilerplate code accepts the incoming payload (e.g., `image_path` and `webhook_url`), immediately returns a `202 Accepted` response, and moves the task to a Python `BackgroundTasks` queue.
   > **Action Required:** None. Do not modify `main.py`.

2. **Processing the Job (`phase0/app/worker.py`):**
   The background queue triggers the `run_phase_worker()` function. This is where the core logic resides. In Phase 0, this is where OpenCV processes the image data.
   > **Action Required:** This is your development space. Replace the sample code inside `run_phase_worker()` with your LLM, OCR, or YOLO workflows.

3. **Returning the Results (`phase0/app/worker.py`):**
   Once your processing algorithm completes, the results must be aggregated and returned to the Orchestrator.
   > **Action Required:** Append your evaluated data to the `webhook_payload` dictionary and invoke the `await _send_webhook(...)` trigger at the bottom of the function. **Do not remove or alter the webhook method signature.**

---

## 📦 3. Dependency Management Protocol

If your algorithm requires new third-party libraries (e.g., `beautifulsoup4`, `transformers`, `pytesseract`), you must strictly follow this protocol. **Do not use `pip install` directly in your terminal.**

1. **Register the Dependency:** Open the `requirements.txt` file located inside your specific Phase directory and append the package name.
   ```text
   # phaseX/requirements.txt
   pytesseract>=0.3.10
   ```
2. **Synchronize the Project:** Close all currently running server windows. Return to your root terminal and run the installation script again:
   ```powershell
   .\install_all.ps1
   ```
*This guarantees that all project dependencies remain tracked in source control and are seamlessly installed for all other developers pulling the repository.*
