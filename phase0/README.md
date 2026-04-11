# Phase 0 — Example Worker (Edge Detection)

> **This is a working example.** Study this before starting your Phase.  
> It demonstrates the full Orchestrator ↔ Worker flow with a simple OpenCV task.

## What This Does

1. Receives an image path from the Orchestrator
2. Runs OpenCV edge detection (Canny) + contour analysis
3. Saves the processed image
4. Fires a webhook back to the Orchestrator with results

## Run It

```bash
cd phase0
pip install -r requirements.txt

# Terminal 1: Start the service
uvicorn app.main:app --reload --port 8010

# Terminal 2: Run the test (simulates the Orchestrator calling you)
python test_flow.py
```

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI entry — receives job, runs worker in background, fires webhook |
| `app/worker.py` | **Your logic goes here** — OpenCV edge detection in this example |
| `test_flow.py` | Simulates the Orchestrator: sends job + listens for webhook |

## The Pattern

```
test_flow.py (fake Orchestrator)        app/main.py + app/worker.py
────────────────────────────────        ──────────────────────────────

1. POST /api/v1/phase0/run ──────────▶  Receives job
   { image_path, webhook_url }            Returns 202 immediately
                                          │
                                          ▼
                                       worker.run(payload)
                                          - Load image (OpenCV)
                                          - Canny edge detection
                                          - Find contours
                                          - Save processed image
                                          │
                                          ▼
2. ◀──────── POST /webhook ──────────  Fires webhook with result
   { thread_id, result: {               { edges, contour_count,
     contour_count, output_path } }       output_path }
```
