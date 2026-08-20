# Local Document Assistant (Local RAG Agent)

**English** | [Türkçe](README_TR.md)

A privacy-focused, fully local Retrieval-Augmented Generation (RAG) assistant running on personal PDFs using [Ollama](https://ollama.com/) and ChromaDB. The CLI is the primary interface; a PySide6 desktop GUI and SQLCipher-encrypted audit logging are provided as optional modules.

![Local Document Assistant UI with synthetic documents](assets/local-belge-asistani.png)

The desktop interface includes a searchable document drawer, document metadata details, source reference buttons opening the relevant PDF page, clipboard copy actions, new chat sessions, and persistent light/dark theme toggles. The settings view displays system status and export options when audit logging is active. Both the interface and model responses support English and Turkish with runtime switching.

## Requirements

- Python 3.12 (supports `>=3.12,<3.14`)
- A running local [Ollama](https://ollama.com/) instance
- Default embedding model: `bge-m3`
- Default chat model: `qwen2.5:1.5b-instruct`

```bash
ollama pull bge-m3
ollama pull qwen2.5:1.5b-instruct
```

## CLI Quickstart

macOS / Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp .env.example .env
python -m src.cli.main
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
python -m src.cli.main
```

Place your PDF documents in the `docs/` folder. The application indexes new documents, updates modified files by re-chunking, and removes deleted files from the vector index automatically.

Available CLI commands:
- `:status` - View index metrics and runtime status
- `:export` - Export encrypted audit logs (if audit is enabled)
- `:language en` / `:language tr` - Switch UI and generation language at runtime
- `:quit` - Exit the CLI

## Desktop GUI

Install the GUI optional dependency in your active virtual environment:

```bash
python -m pip install -e '.[gui]'
python -m src.ui.main_window
```

For Windows PowerShell: `python -m pip install -e ".[gui]"`

The source button attempts to open the referenced PDF directly at the relevant page number in the default PDF viewer (page fragment support depends on your local viewer). The document drawer allows filtering by filename and double-clicking to open documents.

The language can be toggled at runtime via the `Türkçe / English` selector in the Settings menu. Existing conversation text remains intact while card headers, sources, and UI strings update immediately. Responses follow the chosen language regardless of the original document or prompt language. Changing languages does not affect embeddings or require re-indexing.

## Configuration

Copy `.env.example` to `.env` to customize settings:

| Variable | Default | Description |
|---|---:|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `CHAT_MODEL` | `qwen2.5:1.5b-instruct` | Response generation LLM |
| `EMBED_MODEL` | `bge-m3` | Vector embedding model |
| `DOCS_DIR` / `DB_DIR` / `AUDIT_DIR` | `docs` / `db` / `audit` | Data directory paths |
| `RETRIEVAL_K` | `3` | Number of chunks to retrieve |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `500` / `50` | Text chunking parameters |
| `CONFIDENCE_THRESHOLD` | `0.45` | Minimum cosine similarity threshold |
| `CONFIDENCE_HIGH_THRESHOLD` | `0.80` | High-confidence badge threshold for GUI |
| `AUDIT_ENABLED` | `false` | Enables encrypted query/response audit logging |
| `AUDIT_DB_KEY` | *(empty)* | Encryption key (minimum 16 chars when enabled) |

> [!NOTE]
> If you switch embedding models, delete the existing `db/` directory and re-index the documents. The system validates index dimensions and avoids running on mismatched models.

## Encrypted Audit Logging

```bash
python -m pip install -e '.[audit]'
```

Set `AUDIT_ENABLED=true` and configure a strong `AUDIT_DB_KEY` in `.env`. Exported logs contain prompts, answers, and source filenames, and should be handled securely. CSV and XLSX exports sanitize cells to prevent spreadsheet formula injection attacks. SQLCipher is not required when audit logging is disabled.

## Dependency Management

Dependencies are defined in `pyproject.toml`, including optional extras (`gui`, `audit`, `test`). A lightweight `requirements.txt` is maintained for backward compatibility with standard `pip install -r` workflows.

## Docker CLI

With Ollama running on the host machine:

```bash
docker compose run --rm rag-cli
```

`compose.yaml` mounts `docs/`, `db/`, and `audit/` as persistent volumes.

## Testing

Run the test suite:

```bash
python -m pip install -e '.[test,gui]'
python -m pytest
```

Unit tests do not require an active Ollama instance or external model downloads. Real service integration tests run opt-in:

```bash
RUN_OLLAMA_INTEGRATION=1 python -m pytest tests/integration
```

## Security Boundaries

- Running local models and vector stores reduces reliance on third-party APIs, but does not inherently guarantee regulatory compliance or absolute isolation.
- `NetworkGuard` provides process-level defensive filtering at the Python socket layer; it does not replace OS firewalls or container network isolation.
- The retrieval confidence gate filters out low-similarity chunks to reduce unsupported answers; it does not guarantee hallucination-free generation. Always verify sources.
- Structured `<context>` boundaries mitigate prompt injection risks within retrieved content.
- Do not commit sensitive documents, `.env` secrets, audit databases, or model weights to version control.

See [SECURITY.md](SECURITY.md) for full security guidelines and vulnerability reporting procedures.

## Architecture

![Local RAG architecture and security boundaries](assets/local-rag-agent-arch.png)

- `src/loaders`: PDF text and metadata extraction
- `src/indexing`: Document tracking, chunking, and vector index lifecycle
- `src/retrieval`: Vector retrieval, confidence gating, and prompt assembly
- `src/audit`: Optional SQLCipher-backed audit logging and sanitization
- `src/cli` & `src/ui`: Terminal and PySide6 desktop interfaces

## Troubleshooting

- **"Local language model failed to generate response"**: Ensure `ollama serve` is running and verify `OLLAMA_BASE_URL` and model names.
- **"Embedding model mismatch"**: Clear the `db/` folder and restart to regenerate embeddings.
- **SQLCipher not found**: Install the audit extra via `python -m pip install -e '.[audit]'` or keep audit disabled.
- **PDF not indexing**: Verify that the PDF contains selectable text (not scanned images).
## License

[MIT](LICENSE)
