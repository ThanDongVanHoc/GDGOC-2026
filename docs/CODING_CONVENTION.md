# OmniLocal Project Coding Convention

This document defines the professional coding standards and architecture guidelines for the **OmniLocal (GDGOC 2026 - 24A01)** project. All partners and contributors MUST strictly adhere to these conventions to ensure code maintainability, security, and consistent collaboration across all project phases.

---

## 1. General Principles`
- **English-Only Policy**: All code, including comments, variable names, function names, and commit messages, MUST be written in **English**. 
- **Self-Documenting Code**: Code should be expressive and readable. Favor meaningful, descriptive variable names over obscure abbreviations.
- **Separation of Concerns**: Each phase (Ingestion, Translation, Localization, Compositing, QA) must remain decoupled, acting as independent microservices passing standardized JSON.

## 2. Code Comments & Documentation
- **Function/Method Parameters**: Every function MUST include a clear Docstring (preferably Google style) clearly explaining what it does, its parameters (Args), return type (Returns), and any potential errors (Raises).
- **Inline Comments**: Use inline comments only to explain *why* a particular workaround or complex logic was implemented, not *what* the code is doing.

**Example (Python):**
```python
def extract_scene_entities(page_id: str, text_blocks: list) -> dict:
    """
    Extracts cultural entities from standardized text blocks to evaluate the Butterfly Effect.

    Args:
        page_id (str): The unique identifier of the physical PDF page.
        text_blocks (list): A list of dictionaries containing text content and bounding boxes [x0, y0, x1, y1].

    Returns:
        dict: A dictionary of identified entities and their corresponding global relationships.
    """
    pass
```

## 3. Architecture & Security
- **No Direct Database Access from Frontend**: Frontend applications, visual components, or external clients MUST NEVER access the database directly. All operations must strictly go through RESTful APIs provided by the backend (FastAPI).
- **API Versioning**: All API endpoints must be versioned (e.g., `GET /api/v1/task-graph/{page_id}`).
- **Global Metadata Protection**: The constraints defined in `global_metadata.json` (such as copyright bounding boxes, locked character names) are globally immutable and MUST be verified at every API boundary.

## 4. Python Specific Conventions (Backend & LLM Agents)
- **PEP 8 Compliance**: Follow the standard Python style guide (PEP 8). Maximum line length is typically 88 or 100 characters.
- **Type Hinting**: All functions and methods must use Python's built-in type hints (`str`, `int`, `list`, `dict`, etc.) to facilitate static typing and IDE support.
- **Data Validation**: Always use **Pydantic** to validate incoming JSON schema and `global_metadata` constraints before passing it to LLM Agents.

## 5. Naming Conventions
- **Variables & Functions**: Use `snake_case` (e.g., `semantic_chunk`, `call_gemini_api()`).
- **Classes**: Use `PascalCase` (e.g., `TranslatorAgent`, `ButterflyEffectValidator`).
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES = 3`, `SAFE_MARGIN_MM = 5`).
- **Files & Modules**: Use `lower_snake_case` (e.g., `entity_mapping.py`).

## 6. Git Workflow & Commit Guidelines
- **Conventional Commits**: Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard format combined with the **Task ID** from the project breakdown to easily track progress.
  - Format: `#[task_id]: type(scope): description`
  - Types: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `refactor` (code restructuring), `test` (adding missing tests), `chore` (configuration or dependency changes).
  - Example: `#p1.2: feat(phase1): extract spatial coordinates using PyMuPDF`
  - Example: `#p2.4: fix(translator): resolve infinite feedback loop issue`
- DO NOT commit credentials or `.env` files into the repository. 

## 7. Docker & Operational Constraints
- **Containerization**: Every phase or API service MUST be fully containerized. 
- **Lightweight Images**: Use slim base images (e.g., `python:3.10-slim`) to optimize container limits for grading/demo purposes.
- **Requirements Handling**: Keep a strict `requirements.txt` file per container, using exact versioning when possible to avoid dependency conflicts across different partners' machines.
