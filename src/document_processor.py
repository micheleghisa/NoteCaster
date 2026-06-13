import os
import re
from pathlib import Path

import fitz  # PyMuPDF

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import fitz as fitz2
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def _sanitize(text: str) -> str:
    """Remove characters PostgreSQL text columns cannot store (null bytes etc.)."""
    return text.replace('\x00', '')


def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        doc = fitz.open(file_path)
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        doc.close()
        text = "\n".join(pages_text)

        if len(text.strip()) < 100:
            if OCR_AVAILABLE:
                doc = fitz2.open(file_path)
                ocr_parts = []
                for page in doc:
                    mat = fitz2.Matrix(2, 2)
                    pix = page.get_pixmap(matrix=mat)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_parts.append(pytesseract.image_to_string(img))
                doc.close()
                text = "\n".join(ocr_parts)
            else:
                raise ValueError(
                    "PDF scansionato: non è possibile estrarre testo. "
                    "Installa tesseract per OCR: brew install tesseract tesseract-lang"
                )

        return _sanitize(text.strip())

    elif ext in (".docx", ".doc"):
        if not DOCX_AVAILABLE:
            raise ValueError(
                f"Impossibile leggere file {ext}: python-docx non è installato. "
                "Installa con: pip install python-docx"
            )
        document = docx.Document(file_path)
        text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
        return _sanitize(text.strip())

    elif ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return _sanitize(f.read().strip())

    else:
        raise ValueError(f"Formato non supportato: {ext}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) >= 30:
            chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks


def get_file_stats(file_path: str) -> dict:
    return dict(
        name=Path(file_path).name,
        size_kb=round(os.path.getsize(file_path) / 1024, 1),
        ext=Path(file_path).suffix.lower(),
    )
