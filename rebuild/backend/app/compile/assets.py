"""Missing image helpers for tectonic compile (e.g. profile.jpg)."""

from __future__ import annotations

import base64
import re
from pathlib import Path

# Minimal valid 1×1 JPEG / PNG (stdlib only — no Pillow)
_MIN_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8U"
    "HRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgN"
    "DRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
    "MjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAU"
    "EAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAA"
    "AAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAGcP//EABQQAQAAAAAAAAAAAAAAAAAAAAD/"
    "2gAIAQEAAQUCf//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Bf//EABQRAQAA"
    "AAAAAAAAAAAAAAAAAAD/2gAIAQIBAT8Bf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAI"
    "AQEABj8Cf//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAT8hf//Z"
)

_MIN_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAE"
    "hgGAviQBpwAAAABJRU5ErkJggg=="
)

# \includegraphics[width=2cm]{profile.jpg} or {./assets/photo.png}
_INCLUDE_RE = re.compile(
    r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}",
    re.IGNORECASE,
)


def referenced_image_names(source: str) -> list[str]:
    names: list[str] = []
    for m in _INCLUDE_RE.finditer(source or ""):
        raw = (m.group(1) or "").strip().strip('"').strip("'")
        if not raw:
            continue
        # drop path; only basename for temp dir
        name = Path(raw.replace("\\", "/")).name
        if name and name not in names:
            names.append(name)
    return names


def ensure_placeholder_images(source: str, work_dir: Path) -> list[str]:
    """
    Write tiny placeholder files for includegraphics targets missing on disk.
    Returns basenames that were created as placeholders.
    """
    created: list[str] = []
    work_dir = Path(work_dir)
    for name in referenced_image_names(source):
        dest = work_dir / name
        if dest.is_file():
            continue
        # also skip if path-like already exists relative to work_dir
        lower = name.lower()
        if lower.endswith((".png", ".pdf")):
            data = _MIN_PNG if lower.endswith(".png") else _MIN_JPEG
            # PDF placeholder: write minimal JPEG with .pdf name is wrong;
            # for .pdf use a tiny real PDF
            if lower.endswith(".pdf"):
                data = _minimal_pdf_bytes()
            else:
                data = _MIN_PNG
        elif lower.endswith((".jpg", ".jpeg", ".jpe")):
            data = _MIN_JPEG
        else:
            # default photo-like
            data = _MIN_JPEG
            if not Path(name).suffix:
                dest = work_dir / f"{name}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        created.append(dest.name)
    return created


def _minimal_pdf_bytes() -> bytes:
    # tiny valid single-page PDF
    return b"""%PDF-1.1
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 3 3] /Contents 4 0 R >>endobj
4 0 obj<< /Length 0 >>stream
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer<< /Size 5 /Root 1 0 R >>
startxref
284
%%EOF
"""
