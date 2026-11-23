# 08 RAG Concept

## Sources
Five fictional policies of Demo Auto Québec Inc. in `data/raw/documents/`:
- 01 Discounts
- 02 Returns
- 03 Delivery
- 04 Financing
- 05 Warranty

Each document has an English and a French section (`## English`, `## Français`). The section headings `### 1.1` to `### 5.4` are the natural chunk boundaries.

The source format is Markdown, not PDF. Reasons: clean headings as chunk boundaries, no extraction errors (headers, footers, columns). The evaluation measures chunking and embedding only. A PDF test is planned as an extra experiment: render the Markdown to PDF, read it with a PDF loader, and compare the Top 1 result.

## Language
English and French. The embedding model must be multilingual, so a French question can find an English passage and vice versa. The evaluation checks both languages separately.

## Chunking
One chunk per section (`###`) and language. Sections above 350 words are split into windows with 50 words of overlap. Each chunk keeps metadata: document, section number, title, language. The chunk text starts with the section header, so the embedding sees the topic.

## Embedding model
Decision: `BAAI/bge-m3` (multilingual). It was selected after comparing it with the baseline `paraphrase-multilingual-MiniLM-L12-v2`.

| Test | MiniLM | bge-m3 |
|---|---|---|
| 28-question set, Top 1 | 22/24 | 24/24 |
| Independent 15-question set, sources correct | 10/12 | 12/12 |

Caveat: both test sets were used to choose the model and the threshold (see docs/09). The model is set via `EMBED_MODEL` in `modules/rag/index.py`.

## Vector store
FAISS (`IndexFlatIP`, local). Vectors are normalized, so the inner product equals the cosine similarity. Chunk metadata is stored in `chunks.json`, the model and dimension in `meta.json`. The index is rebuilt after every change to the documents or the model.

## Retrieval
Top 3 hits, only hits with a score of at least 0.55 (`MIN_SCORE`). The threshold is provisional, see docs/09.

## Answer step
- Local LLM via Ollama: `qwen2.5:7b-instruct`, temperature 0, at most 300 output tokens.
- Adapter interface `chat(system, user)`. The provider is selected by `LLM_PROVIDER` in `.env` (`local` or `huggingface`).
- The answer uses only the retrieved passages. If no passage addresses the question, the model replies `NOT_FOUND`, and the system returns "nothing found" in both languages.
- Prohibitions and exclusions count as answers ("No, ...").
- The model names the sections it used in a "Sources used:" line. The code shows only those sections, checked against the retrieved set. Without a valid citation, the top-1 section is shown.

## Hugging Face Inference API (implemented, not in use)
The adapter `modules/llm/hf_api.py` works up to authentication. The calls then returned `402 Payment Required`, because the account has no Inference Providers credits. The adapter stays in the code base. It can be used after buying credits or subscribing to PRO.

## Known limits
- The 7B model makes reasoning errors on conditions and limits (vehicle age, "not above 3 %"). See docs/09, errors 4 and 5.
- The threshold 0.55 is tuned on the 28-question set. A larger test set is needed.
- Both test sets are small (28 and 15 questions).