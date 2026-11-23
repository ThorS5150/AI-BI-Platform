"""Chunking der Richtlinien.

Ein Chunk entspricht einem Abschnitt (### x.y) je Sprache (## English / ## Français).
Abschnitte über MAX_WORDS werden mit Überlappung in Fenster geteilt.
Jeder Chunk bekommt Metadaten für Quellenangaben: Dokument, Abschnitt, Sprache.
"""
import re
from dataclasses import dataclass
from pathlib import Path

# Define and initialize variables
MAX_WORDS = 350   # max. size  per Chunk, around 500 Tokens
OVERLAP_WORDS = 50
LANG_HEADINGS = {"## English": "en", "## Français": "fr"}
SECTION_RE = re.compile(r"^### (\d+\.\d+) (.+)$")

try:
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
except NameError:  # Jupyter-Notebook: __file__ is not defined
    _PROJECT_ROOT = Path.cwd()  # Notebook muss im Projektordner laufen, sonst DOCS_DIR übergeben

DOCS_DIR = _PROJECT_ROOT / "data" / "raw" / "documents" # Path to documents

# Definition of a chunk class used in the following functions chunk_document and chunck_all
@dataclass
class Chunk:
    chunk_id: str
    doc: str
    section: str
    title: str
    language: str
    text: str

# called by chunk_document to split the words accordingly 
def _split_words(text: str) -> list[str]:
    words = text.split()
    if len(words) <= MAX_WORDS:
        return [text]
    windows, start = [], 0
    while start < len(words):
        windows.append(" ".join(words[start:start + MAX_WORDS]))
        if start + MAX_WORDS >= len(words):
            break
        start += MAX_WORDS - OVERLAP_WORDS
    return windows

# called by chunk_all to create the chunk for a document 
def chunk_document(path: Path) -> list[Chunk]:
    sections, lang, current = [], None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            lang = LANG_HEADINGS.get(stripped)  # None für den Dokumenttitel
            current = None
            continue
        match = SECTION_RE.match(stripped)
        if match and lang:
            current = {"section": match.group(1), "title": match.group(2), "lang": lang, "body": []}
            sections.append(current)
        elif current is not None and stripped:
            current["body"].append(stripped)

    chunks = []
    for sec in sections:
        body = " ".join(sec["body"])
        header = f"{sec['section']} {sec['title']}:"
        for i, window in enumerate(_split_words(body)):
            chunks.append(Chunk(
                chunk_id=f"{path.stem}-{sec['lang']}-{sec['section']}-{i}",
                doc=path.name,
                section=sec["section"],
                title=sec["title"],
                language=sec["lang"],
                text=f"{header} {window}",
            ))
    return chunks

# All related documents will be integrated into the chunks-list
def chunk_all(docs_dir: Path = DOCS_DIR) -> list[Chunk]:
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        chunks.extend(chunk_document(path)) # calls the chunk_document within this file
    return chunks


if __name__ == "__main__":
    all_chunks = chunk_all() # initial call 
    print("Chunks gesamt:", len(all_chunks))
    print("Nach Sprache:", {lang: sum(c.language == lang for c in all_chunks) for lang in ("en", "fr")})
    longest = max(all_chunks, key=lambda c: len(c.text.split()))
    print("Längster Chunk:", longest.chunk_id, len(longest.text.split()), "Wörter")
    print("Beispiel:", all_chunks[0])
