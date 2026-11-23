from modules.rag.index import build_index
from modules.rag.retriever import Retriever


def test_known_question_finds_correct_section(tmp_path):
    build_index(index_dir=tmp_path)
    retriever = Retriever(index_dir=tmp_path)

    hits = retriever.search("What is the maximum discount a dealer can grant without approval?")

    assert hits, "Keine Treffer über dem Schwellenwert"
    top = hits[0].chunk
    assert top.doc == "01_discount_policy.md"
    assert top.section == "1.2"
    assert top.language == "en"


def test_french_question_finds_french_chunk(tmp_path):
    build_index(index_dir=tmp_path)
    retriever = Retriever(index_dir=tmp_path)

    hits = retriever.search("Quelle remise maximale un concessionnaire peut-il accorder sans approbation ?")

    assert hits
    assert hits[0].chunk.doc == "01_discount_policy.md"
    assert hits[0].chunk.language == "fr"