"""Suche in den Richtlinien-Chunks.

Eine Frage wird mit demselben Modell vektorisiert wie der Index. Die TOP_K
ähnlichsten Chunks werden zurückgegeben, aber nur, wenn ihr Score über
MIN_SCORE liegt. Ist kein Treffer darüber, ist die Liste leer. Das setzt die
Antwortregel aus docs/08 um: keine Quelle, keine Antwort.
"""
from dataclasses import dataclass
from pathlib import Path

from sentence_transformers import SentenceTransformer

from modules.rag.chunking import Chunk
from modules.rag.index import INDEX_DIR, embed, load_index

TOP_K = 3
MIN_SCORE = 0.55  # Startwert, wird im Evaluationslauf kalibriert


@dataclass
class Hit:
    score: float
    chunk: Chunk

# An instance will be instanziated by the Agent (user interaction)
class Retriever:
    def __init__(self, index_dir: Path = INDEX_DIR):
        self.index, self.chunks, self.meta = load_index(index_dir) # calls load_index function of the index.py module
        self.model = SentenceTransformer(self.meta["model"]) # gets model from the meta.json file in data/index folder
    
    def search(self, question: str, k: int = TOP_K, min_score: float = MIN_SCORE) -> list[Hit]:
        query = embed(self.model, [question])
        scores, ids = self.index.search(query, k)
        hits = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1 or score < min_score:
                continue
            hits.append(Hit(score=float(score), chunk=self.chunks[idx]))
        return hits