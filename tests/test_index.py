import json

from modules.rag.index import MODEL_NAME, build_index, load_index


def test_index_is_built_and_loadable(tmp_path):
    index, chunks = build_index(index_dir=tmp_path)
    assert index.ntotal == len(chunks) == 40

    loaded_index, loaded_chunks, meta = load_index(index_dir=tmp_path)
    assert loaded_index.ntotal == 40
    assert len(loaded_chunks) == 40
    assert meta["model"] == MODEL_NAME
    assert meta["dimension"] == loaded_index.d
    assert meta["chunks"] == 40
