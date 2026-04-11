"""Configuration constants for the MinerU PDF conversion utility.

Centralizes all tuneable parameters so that callers can override defaults
without touching internal logic.  Values here are intentionally conservative
(CPU-safe, English-only) — override via MinerUConverter constructor args.
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Backend Selection
# ---------------------------------------------------------------------------
# "pipeline" — traditional layout-analysis models, works on CPU.
# "vlm"      — vision-language-model backend, requires NVIDIA GPU (CUDA).
SUPPORTED_BACKENDS: list[str] = ["pipeline", "vlm"]
DEFAULT_BACKEND: str = "pipeline"

# ---------------------------------------------------------------------------
# OCR / Language
# ---------------------------------------------------------------------------
DEFAULT_ENABLE_OCR: bool = True
DEFAULT_LANGUAGES: list[str] = ["en"]

# ---------------------------------------------------------------------------
# Output Control
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR: Path = Path("mineru_output")
DEFAULT_DROP_HEADERS: bool = True
DEFAULT_DROP_FOOTERS: bool = True

# ---------------------------------------------------------------------------
# MinerU CLI fallback
# ---------------------------------------------------------------------------
MINERU_CLI_COMMAND: str = "mineru"
CLI_TIMEOUT_SECONDS: int = 600  # 10 min per PDF — generous for large books
