"""Download Griffith's Ramayana from Project Gutenberg."""

from __future__ import annotations

import os
from pathlib import Path

import httpx

from ramayana_kg.config import settings


def download_text(url: str | None = None, output_dir: str | None = None) -> Path:
    """Download Ramayana text and save to local file.

    Returns path to the downloaded file.
    """
    url = url or settings.gutenberg_url
    output_dir = output_dir or settings.data_dir
    os.makedirs(output_dir, exist_ok=True)
    output_path = Path(output_dir) / "ramayana_griffith.txt"

    if output_path.exists():
        return output_path

    response = httpx.get(url, follow_redirects=True, timeout=60.0)
    response.raise_for_status()
    output_path.write_text(response.text, encoding="utf-8")
    return output_path
