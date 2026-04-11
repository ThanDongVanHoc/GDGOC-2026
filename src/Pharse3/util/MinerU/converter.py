"""MinerU PDF → Markdown / Standardized Pack converter.

Provides :class:`MinerUConverter`, the primary entry-point for converting
a PDF file into either:

* Raw Markdown (:meth:`parse_pdf_to_markdown`)
* #p1.2 Standardized Pack JSON (:meth:`parse_pdf_to_standardized_pack`)

The converter tries the **MinerU Python SDK** first and falls back to
invoking the ``mineru`` CLI as a subprocess if the SDK is unavailable or
fails at runtime.

Usage::

    from src.Pharse3.util.MinerU import MinerUConverter

    converter = MinerUConverter(backend="pipeline")
    pack = converter.parse_pdf_to_standardized_pack("book.pdf")
    print(pack.model_dump_json(indent=2))
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .config import (
    CLI_TIMEOUT_SECONDS,
    DEFAULT_BACKEND,
    DEFAULT_DROP_FOOTERS,
    DEFAULT_DROP_HEADERS,
    DEFAULT_ENABLE_OCR,
    DEFAULT_LANGUAGES,
    DEFAULT_OUTPUT_DIR,
    MINERU_CLI_COMMAND,
    SUPPORTED_BACKENDS,
)
from .models import DocumentPack, PageLayout
from .post_processor import build_document_pack, build_page_layouts

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# SDK availability check (deferred import)
# ------------------------------------------------------------------

def _sdk_available() -> bool:
    """Return True if the ``mineru`` Python package can be imported."""
    try:
        import mineru  # noqa: F401
        return True
    except ImportError:
        return False


class MinerUConverter:
    """High-level wrapper around the MinerU document-parsing engine.

    Args:
        backend: Parsing backend — ``"pipeline"`` (CPU) or ``"vlm"`` (GPU).
        enable_ocr: Whether to enable OCR for scanned / garbled PDFs.
        languages: List of ISO-639-1 language codes for OCR.
        output_dir: Directory where MinerU writes intermediate files.
            A temporary directory is used if ``None``.
        drop_headers: Strip repeated page headers from output.
        drop_footers: Strip repeated page footers from output.

    Raises:
        ValueError: If *backend* is not one of the supported backends.
    """

    def __init__(
        self,
        backend: str = DEFAULT_BACKEND,
        enable_ocr: bool = DEFAULT_ENABLE_OCR,
        languages: list[str] | None = None,
        output_dir: str | Path | None = None,
        drop_headers: bool = DEFAULT_DROP_HEADERS,
        drop_footers: bool = DEFAULT_DROP_FOOTERS,
    ) -> None:
        if backend not in SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unsupported backend '{backend}'. "
                f"Choose from {SUPPORTED_BACKENDS}."
            )

        self.backend = backend
        self.enable_ocr = enable_ocr
        self.languages = languages or list(DEFAULT_LANGUAGES)
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.drop_headers = drop_headers
        self.drop_footers = drop_footers

        self._sdk_ok: bool | None = None  # lazy-checked on first call

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_pdf(self, pdf_path: str | Path) -> dict[str, Any]:
        """Parse a PDF and return the raw MinerU result dictionary.

        The returned dict always contains at minimum:
        - ``"markdown"``       — full Markdown string
        - ``"output_dir"``     — path to the output directory
        - ``"content_list"``   — list of content entries (may be empty)

        Args:
            pdf_path: Path to the input PDF file.

        Returns:
            Dictionary with raw parsing artefacts.

        Raises:
            FileNotFoundError: If *pdf_path* does not exist.
            RuntimeError: If both SDK and CLI parsing fail.
        """
        pdf_path = Path(pdf_path).resolve()
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Try SDK first, then CLI
        if self._try_sdk():
            try:
                return self._parse_via_sdk(pdf_path)
            except Exception as exc:
                logger.warning(
                    "SDK parsing failed (%s), falling back to CLI.", exc
                )

        return self._parse_via_cli(pdf_path)

    def parse_pdf_to_markdown(self, pdf_path: str | Path) -> str:
        """Parse a PDF and return only the Markdown text.

        Args:
            pdf_path: Path to the input PDF file.

        Returns:
            Markdown string produced by MinerU.
        """
        result = self.parse_pdf(pdf_path)
        return result.get("markdown", "")

    def parse_pdf_to_standardized_pack(
        self,
        pdf_path: str | Path,
        page_dimensions: dict[int, tuple[float, float]] | None = None,
    ) -> DocumentPack:
        """Parse a PDF and return a fully structured ``DocumentPack``.

        This is the main integration point — the returned object matches
        the #p1.2 Standardized Pack schema and can be serialised with
        ``pack.model_dump_json()``.

        Args:
            pdf_path: Path to the input PDF file.
            page_dimensions: Optional mapping ``page_id → (width, height)``
                to override default A4 dimensions.

        Returns:
            A :class:`DocumentPack` containing per-page layout data.
        """
        pdf_path = Path(pdf_path).resolve()
        result = self.parse_pdf(pdf_path)

        content_list = result.get("content_list", [])
        markdown = result.get("markdown", "")
        out_dir = Path(result.get("output_dir", self.output_dir))

        # If we got an empty content_list from the SDK, try loading from disk
        if not content_list:
            cl_path = self._find_content_list(out_dir)
            if cl_path:
                with open(cl_path, encoding="utf-8") as fh:
                    loaded = json.load(fh)
                if isinstance(loaded, list):
                    content_list = loaded
                elif isinstance(loaded, dict) and "content_list" in loaded:
                    content_list = loaded["content_list"]

        # If markdown is empty, try reading from disk
        if not markdown:
            md_path = self._find_markdown_file(out_dir)
            if md_path:
                markdown = md_path.read_text(encoding="utf-8")

        pages = build_page_layouts(content_list, page_dimensions)

        return DocumentPack(
            source_file=pdf_path.name,
            total_pages=len(pages),
            pages=pages,
            markdown_content=markdown or None,
        )

    # ------------------------------------------------------------------
    # SDK path
    # ------------------------------------------------------------------

    def _try_sdk(self) -> bool:
        """Check (once) whether the MinerU SDK is usable."""
        if self._sdk_ok is None:
            self._sdk_ok = _sdk_available()
            if self._sdk_ok:
                logger.info("MinerU SDK detected — using Python API.")
            else:
                logger.info("MinerU SDK not found — will use CLI fallback.")
        return self._sdk_ok

    def _parse_via_sdk(self, pdf_path: Path) -> dict[str, Any]:
        """Run parsing through the MinerU Python SDK.

        Args:
            pdf_path: Resolved path to the PDF file.

        Returns:
            Dictionary with ``markdown``, ``output_dir``, ``content_list``.

        Raises:
            ImportError: If the SDK cannot be imported.
            RuntimeError: If SDK parsing fails for any other reason.
        """
        from mineru import MinerU  # type: ignore[import-untyped]

        out_dir = self.output_dir / pdf_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)

        parser = MinerU(
            enable_ocr=self.enable_ocr,
            languages=self.languages,
            drop_headers=self.drop_headers,
            drop_footers=self.drop_footers,
        )

        logger.info("Parsing '%s' via SDK (backend=%s)…", pdf_path.name, self.backend)
        result = parser.parse(str(pdf_path))

        # Extract what we need from the SDK result
        markdown = ""
        content_list: list[dict[str, Any]] = []

        if isinstance(result, str):
            markdown = result
        elif isinstance(result, dict):
            markdown = result.get("markdown", result.get("md", ""))
            content_list = result.get("content_list", [])
        elif hasattr(result, "markdown"):
            markdown = getattr(result, "markdown", "")
            content_list = getattr(result, "content_list", [])

        return {
            "markdown": markdown,
            "output_dir": str(out_dir),
            "content_list": content_list,
        }

    # ------------------------------------------------------------------
    # CLI fallback path
    # ------------------------------------------------------------------

    def _parse_via_cli(self, pdf_path: Path) -> dict[str, Any]:
        """Run parsing through the ``mineru`` CLI subprocess.

        Args:
            pdf_path: Resolved path to the PDF file.

        Returns:
            Dictionary with ``markdown``, ``output_dir``, ``content_list``.

        Raises:
            RuntimeError: If the CLI returns a non-zero exit code.
        """
        out_dir = self.output_dir / pdf_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            MINERU_CLI_COMMAND,
            "-p", str(pdf_path),
            "-o", str(out_dir),
            "-b", self.backend,
        ]
        logger.info("Parsing '%s' via CLI: %s", pdf_path.name, " ".join(cmd))

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=CLI_TIMEOUT_SECONDS,
                check=False,
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"'{MINERU_CLI_COMMAND}' not found on PATH. "
                "Install MinerU: pip install -U 'mineru[core]'"
            )

        if proc.returncode != 0:
            raise RuntimeError(
                f"MinerU CLI failed (exit {proc.returncode}):\n"
                f"stdout: {proc.stdout[:500]}\n"
                f"stderr: {proc.stderr[:500]}"
            )

        # Read artefacts written to disk
        markdown = ""
        content_list: list[dict[str, Any]] = []

        md_file = self._find_markdown_file(out_dir)
        if md_file:
            markdown = md_file.read_text(encoding="utf-8")

        cl_file = self._find_content_list(out_dir)
        if cl_file:
            with open(cl_file, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                content_list = data
            elif isinstance(data, dict) and "content_list" in data:
                content_list = data["content_list"]

        return {
            "markdown": markdown,
            "output_dir": str(out_dir),
            "content_list": content_list,
        }

    # ------------------------------------------------------------------
    # File discovery helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_markdown_file(directory: Path) -> Path | None:
        """Locate the first ``.md`` file in *directory* (recursive).

        Args:
            directory: Root directory to search.

        Returns:
            Path to the Markdown file, or ``None``.
        """
        for md in sorted(directory.rglob("*.md")):
            return md
        return None

    @staticmethod
    def _find_content_list(directory: Path) -> Path | None:
        """Locate the ``content_list.json`` artefact written by MinerU.

        Args:
            directory: Root directory to search.

        Returns:
            Path to the JSON file, or ``None``.
        """
        for candidate_name in ("content_list.json", "content-list.json"):
            for match in directory.rglob(candidate_name):
                return match
        # Fallback: any JSON file
        for jf in sorted(directory.rglob("*.json")):
            return jf
        return None


# ------------------------------------------------------------------
# Module-level convenience function
# ------------------------------------------------------------------

def convert_pdf_to_standardized_pack(
    pdf_path: str | Path,
    backend: str = DEFAULT_BACKEND,
    enable_ocr: bool = DEFAULT_ENABLE_OCR,
    languages: list[str] | None = None,
    output_dir: str | Path | None = None,
) -> DocumentPack:
    """One-shot convenience function for PDF → Standardized Pack.

    Creates a temporary :class:`MinerUConverter`, parses the PDF, and
    returns the structured result.  Use this when you don't need to
    re-use a converter instance across multiple files.

    Args:
        pdf_path: Path to the input PDF.
        backend: Parsing backend (``"pipeline"`` or ``"vlm"``).
        enable_ocr: Enable OCR for scanned documents.
        languages: OCR language codes.
        output_dir: Where to write intermediate files.

    Returns:
        A :class:`DocumentPack` matching the #p1.2 schema.
    """
    converter = MinerUConverter(
        backend=backend,
        enable_ocr=enable_ocr,
        languages=languages,
        output_dir=output_dir,
    )
    return converter.parse_pdf_to_standardized_pack(pdf_path)
