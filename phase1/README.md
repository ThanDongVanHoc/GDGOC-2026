# OmniLocal — Phase 1: Ingestion & Structural Parsing

## Quick Start

```bash
cd phase1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Your Endpoint

```
POST /api/v1/phase1/run
```

## What You Receive (from Orchestrator)

```json
{
    "thread_id": "run_abc123",
    "source_pdf_path": "/data/uploads/source_book.pdf",
    "brief_path": "/data/uploads/project_brief.docx",
    "webhook_url": "http://orchestrator:8000/webhook/phase1"
}
```

## What You Return (via Webhook)

```json
{
    "thread_id": "run_abc123",
    "result": {
        "global_metadata": { ... },
        "standardized_pack": [ ... ]
    }
}
```

## Your Job

1. Parse the project brief → extract `global_metadata` (constraints, protected names, style).
2. Parse the PDF with PyMuPDF → extract text blocks + image blocks with bbox coordinates.
3. Tag editability for each block (`editable`, `semi-editable`, `non-editable`).
4. Fire webhook with results.

**All internal decisions are yours** — subtask order, parallelism, algorithms.

## Detailed Spec

See [Phase 1 Documentation](../docs/phases/Phase1_Ingestion_StructuralParsing.md) and [Blueprint](../docs/Blueprint_LangGraph.md).
