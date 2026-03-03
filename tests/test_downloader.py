"""Tests for data downloader (mocked HTTP)."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from ramayana_kg.data.downloader import download_text


@patch("ramayana_kg.data.downloader.httpx.get")
def test_download_text(mock_get):
    mock_response = MagicMock()
    mock_response.text = "BOOK I\nCANTO I\nTest verse content here."
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        result = download_text(url="http://example.com/test.txt", output_dir=tmpdir)
        assert result.exists()
        assert result.name == "ramayana_griffith.txt"
        content = result.read_text()
        assert "BOOK I" in content


@patch("ramayana_kg.data.downloader.httpx.get")
def test_download_text_cached(mock_get):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Pre-create the file
        cached_path = Path(tmpdir) / "ramayana_griffith.txt"
        cached_path.write_text("cached content")

        result = download_text(url="http://example.com/test.txt", output_dir=tmpdir)
        assert result == cached_path
        mock_get.assert_not_called()  # Should not download if cached
