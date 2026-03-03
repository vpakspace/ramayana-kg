"""Tests for pipeline orchestrator (mocked)."""

from unittest.mock import MagicMock, patch
from pathlib import Path

from ramayana_kg.pipeline import step_download, step_parse


@patch("ramayana_kg.pipeline.download_text")
def test_step_download(mock_download):
    mock_download.return_value = Path("/tmp/test.txt")
    result = step_download("/tmp")
    assert result == Path("/tmp/test.txt")


@patch("ramayana_kg.pipeline.parse_file")
def test_step_parse(mock_parse):
    from ramayana_kg.models import Verse
    mock_parse.return_value = [
        Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="test"),
    ]
    verses = step_parse(Path("/tmp/test.txt"))
    assert len(verses) == 1
