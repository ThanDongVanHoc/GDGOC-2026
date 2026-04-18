import logging
import os
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

def download_if_needed(img_path: str, img_url: str = None) -> bytes:
    """Read local img bytes if present, otherwise download from URL."""
    if os.path.exists(img_path):
        return Path(img_path).read_bytes()

    if img_url:
        logger.info("[Download File] File missing locally; fetching from %s", img_url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = httpx.get(img_url, headers=headers, follow_redirects=True, timeout=120)
        r.raise_for_status()
        
        # Ensure the directory exists and save the file
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        with open(img_path, "wb") as f:
            f.write(r.content)
            
        return r.content

    raise FileNotFoundError(f"Image not found locally and no download URL provided: {img_path}")