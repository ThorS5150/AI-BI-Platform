from modules.rag.chunking import MAX_WORDS, chunk_all


def test_every_section_in_both_languages():
    chunks = chunk_all()
    # 5 Dokumente x 4 Abschnitte x 2 Sprachen = 40 Chunks (alle Abschnitte sind kurz)
    assert len(chunks) == 40


def test_metadata_is_complete():
    for c in chunk_all():
        assert c.doc.endswith(".md")
        assert c.language in ("en", "fr")
        assert c.section.count(".") == 1
        assert c.text.startswith(c.section)


def test_no_chunk_exceeds_limit():
    assert all(len(c.text.split()) <= MAX_WORDS + 10 for c in chunk_all())


def test_chunk_ids_unique():
    ids = [c.chunk_id for c in chunk_all()]
    assert len(ids) == len(set(ids))