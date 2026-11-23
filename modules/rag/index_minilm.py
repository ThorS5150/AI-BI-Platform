"""Embedding der Richtlinien-Chunks und Aufbau des FAISS-Index.

Ablauf: chunk_all() liefert die Chunks, das Sentence-Transformers-Modell macht
normalisierte Vektoren, FAISS speichert sie (Inner Product = Kosinus-Ähnlichkeit).
Gespeichert werden Index, Chunk-Metadaten und das verwendete Modell, damit der
Retriever später exakt dasselbe Modell für Fragen benutzt.
"""
import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from modules.rag.chunking import Chunk, _PROJECT_ROOT, chunk_all

# Define and initialize global variables
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INDEX_DIR = _PROJECT_ROOT / "data" / "index"
INDEX_FILE = "rules.faiss"
CHUNKS_FILE = "chunks.json"
META_FILE = "meta.json"

# embed function called by the retriver (Agent call) the build_index_function to create the vectors 
def embed(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return np.asarray(vectors, dtype="float32")

# function to build the index and chunks over chunk_all function in chunking.py, called by user
def build_index(docs_dir: Path | None = None, index_dir: Path = INDEX_DIR,
                model_name: str = MODEL_NAME) -> tuple[faiss.Index, list[Chunk]]:
    chunks = chunk_all(docs_dir) if docs_dir else chunk_all()
    model = SentenceTransformer(model_name)
    vectors = embed(model, [c.text for c in chunks])

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    index_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_dir / INDEX_FILE))
    (index_dir / CHUNKS_FILE).write_text(
        json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=2), encoding="utf-8")
    (index_dir / META_FILE).write_text(json.dumps({
        "model": model_name,
        "dimension": int(vectors.shape[1]),
        "chunks": len(chunks),
    }, indent=2), encoding="utf-8")
    return index, chunks

# function to load the index, called by Retriever class (Agent call)
def load_index(index_dir: Path = INDEX_DIR) -> tuple[faiss.Index, list[Chunk], dict]:
    index = faiss.read_index(str(index_dir / INDEX_FILE))
    raw = json.loads((index_dir / CHUNKS_FILE).read_text(encoding="utf-8"))
    meta = json.loads((index_dir / META_FILE).read_text(encoding="utf-8"))
    return index, [Chunk(**r) for r in raw], meta  # return to the retriever class
