"""
OmniLocal Orchestrator — Configuration.

Service URLs for each Phase Worker and pipeline constants.
"""

import os

# Phase Worker service URLs (override via environment variables)
PHASE_URLS: dict[int, str] = {
    0: os.getenv("PHASE0_URL", "http://localhost:8010"),
    1: os.getenv("PHASE1_URL", "http://phase1:8000"),
    2: os.getenv("PHASE2_URL", "http://phase2:8000"),
    3: os.getenv("PHASE3_URL", "http://phase3:8000"),
    4: os.getenv("PHASE4_URL", "http://phase4:8000"),
    5: os.getenv("PHASE5_URL", "http://phase5:8000"),
}

# Webhook base URL (the Orchestrator's own address for Workers to call back)
WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "http://orchestrator:8000")

# Pipeline safety limits
MAX_PIPELINE_ITERATIONS: int = 2
DISPATCH_TIMEOUT_SECONDS: int = 30
