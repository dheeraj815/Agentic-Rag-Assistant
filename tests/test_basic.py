"""
tests/test_basic.py
Basic unit tests that do not require external API keys.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.text_splitter import split_text  # noqa: E402
from agents.report_generator_agent import _slugify  # noqa: E402


def test_split_text_basic():
    text = "word " * 500
    chunks = split_text(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 120  # allow slight overlap variance


def test_split_text_empty():
    chunks = split_text("", chunk_size=100, chunk_overlap=10)
    assert chunks == [] or chunks == [""]


def test_slugify():
    assert _slugify("What is the capital of France?") == "what_is_the_capital_of_france"
    assert _slugify("") == "report"
    assert "_" not in _slugify("single")


if __name__ == "__main__":
    test_split_text_basic()
    test_split_text_empty()
    test_slugify()
    print("All basic tests passed.")
