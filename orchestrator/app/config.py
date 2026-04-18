"""
OmniLocal Orchestrator — Configuration.

Service URLs for each Phase Worker and pipeline constants.

Local dev:  All phases default to http://localhost:8010 (mock_workers).
Production: Set PHASE1_URL..PHASE5_URL environment variables to real Worker URLs.
"""

import os

# Phase Worker service URLs (override via environment variables)
PHASE_URLS: dict[int, str] = {
    0: os.getenv("PHASE0_URL", "http://localhost:8010"),
    1: os.getenv("PHASE1_URL", "https://seal-ada-fog-cedar.trycloudflare.com"),
    2: os.getenv("PHASE2_URL", "http://127.0.0.1:8002"),
    3: os.getenv("PHASE3_URL", "http://127.0.0.1:8003"),
    4: os.getenv("PHASE4_URL", "http://localhost:8010"),
    5: os.getenv("PHASE5_URL", "http://127.0.0.1:8005"),
}

# Webhook base URL (the Orchestrator's own address for Workers to call back)
WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "https://strips-proxy-medicines-perfect.trycloudflare.com")

# Pipeline safety limits
MAX_PIPELINE_ITERATIONS: int = 2
DISPATCH_TIMEOUT_SECONDS: int = 30
