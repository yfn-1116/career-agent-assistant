# Sample Data Boundary

`data/samples/` contains only sanitized demo data that can be committed and
used for tests, local demos, and presentations.

Runtime data must not be committed:

- Uploaded resumes, PDFs, DOCX files, or raw personal documents
- Generated knowledge-base indexes such as `data/knowledge_base/chunks.jsonl`
- Application records created during local demos
- Generated resumes, diagnostics, reports, logs, and temporary files

Use `runtime/` for local runtime state and `outputs/` for generated demo output.
Both locations are ignored by default. If a demo needs committed data, add a
small sanitized fixture under `data/samples/` instead of committing real user
data.
