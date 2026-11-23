"""Tests for the answer step with a fake LLM and a fake retriever (no Ollama, no model download)."""
from modules.rag.answer import FALLBACK_TEXT, NOT_FOUND_TOKEN, answer
from modules.rag.chunking import Chunk
from modules.rag.retriever import Hit


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits

    def search(self, question, **kwargs):
        return self.hits


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = 0

    def chat(self, system, user):
        self.calls += 1
        return self.reply


def make_hit(doc="01_discount_policy.md", section="1.2", score=0.8):
    chunk = Chunk(
        chunk_id=f"{doc}-en-{section}-0",
        doc=doc,
        section=section,
        title="Discount limits",
        language="en",
        text=f"{section} Discount limits: Up to 5 % without approval.",
    )
    return Hit(score=score, chunk=chunk)


def test_no_hits_skips_llm():
    llm = FakeLLM("should not be used")
    result = answer("anything", FakeRetriever([]), llm)
    assert result.found is False
    assert result.text == FALLBACK_TEXT
    assert llm.calls == 0


def test_not_found_token_returns_fallback():
    result = answer("q", FakeRetriever([make_hit()]), FakeLLM(NOT_FOUND_TOKEN))
    assert result.found is False
    assert result.text == FALLBACK_TEXT
    assert result.sources == []


def test_only_cited_sources_are_shown():
    hits = [make_hit(section="1.2"), make_hit(section="1.4")]
    reply = "5 %.\nSources used: [01_discount_policy.md 1.2]"
    result = answer("q", FakeRetriever(hits), FakeLLM(reply))
    assert result.found is True
    assert result.text == "5 %."
    assert result.sources == ["01_discount_policy.md 1.2"]


def test_invented_citation_is_dropped_and_top1_shown():
    hits = [make_hit(section="1.2"), make_hit(section="1.4")]
    reply = "5 %.\nSources used: [01_discount_policy.md 9.9]"
    result = answer("q", FakeRetriever(hits), FakeLLM(reply))
    assert result.sources == ["01_discount_policy.md 1.2"]


def test_missing_sources_line_shows_top1():
    hits = [make_hit(section="1.2"), make_hit(section="1.4")]
    result = answer("q", FakeRetriever(hits), FakeLLM("5 %."))
    assert result.text == "5 %."
    assert result.sources == ["01_discount_policy.md 1.2"]


def test_sources_are_deduplicated():
    hits = [make_hit(section="1.2", score=0.8), make_hit(section="1.2", score=0.7)]
    result = answer("q", FakeRetriever(hits), FakeLLM("answer\nSources used: [01_discount_policy.md 1.2]"))
    assert result.sources == ["01_discount_policy.md 1.2"]

def test_sources_line_inside_text_is_removed():
    hits = [make_hit(section="1.2"), make_hit(section="1.4")]
    reply = "5 %. Sources used: [01_discount_policy.md 1.2]"
    result = answer("q", FakeRetriever(hits), FakeLLM(reply))
    assert result.text == "5 %."
    assert result.sources == ["01_discount_policy.md 1.2"]