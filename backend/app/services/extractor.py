"""
Krishi Setu — Multi-format Content Extractor
Handles: PDF (with OCR fallback), CSV, JSON, XLSX, DOCX, XML
Each extractor returns a dict compatible with the Scheme model or None.
"""

import csv
import hashlib
import io
import json
import xml.etree.ElementTree as ET
from typing import Optional

from app.models.models import Source


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ─── PDF ──────────────────────────────────────────────────────────────────────

def extract_from_pdf_bytes(
    content: bytes,
    url: str,
    source: Source,
) -> Optional[dict]:
    """
    Extract text from PDF using PyMuPDF (fitz).
    Falls back to Tesseract OCR for scanned PDFs.
    """
    text = ""

    try:
        import fitz  # PyMuPDF
        pdf = fitz.open(stream=content, filetype="pdf")
        for page in pdf:
            text += page.get_text()
        pdf.close()
    except Exception as e:
        print(f"  [pdf] PyMuPDF failed: {e}")

    # If no text extracted (scanned PDF), try OCR
    if not text.strip():
        text = _ocr_pdf(content)

    if not text.strip():
        return None

    # Heuristic scheme detection
    scheme_keywords = ["eligibility", "benefit", "scheme", "yojana", "subsidy", "farmer"]
    keyword_count = sum(1 for kw in scheme_keywords if kw.lower() in text.lower())
    if keyword_count < 2:
        return None

    # Use first non-empty line as title
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0][:500] if lines else "Untitled Scheme"

    return {
        "name": title,
        "description": text[:2000],
        "source_url": url,
        "url_hash": sha256_hash(url),
        "content_hash": sha256_hash(text[:5000]),
        "ministry_id": source.ministry_id,
        "search_synonyms": [],
        "eligibility_criteria": {},
        "benefits": {},
    }


def _ocr_pdf(content: bytes) -> str:
    """OCR fallback using Tesseract via pytesseract + PIL."""
    try:
        import fitz
        from PIL import Image
        import pytesseract

        text = ""
        pdf = fitz.open(stream=content, filetype="pdf")
        for page in pdf:
            # Render page as image
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img, lang="eng+hin")
        pdf.close()
        return text
    except Exception as e:
        print(f"  [ocr] Failed: {e}")
        return ""


# ─── CSV ──────────────────────────────────────────────────────────────────────

def extract_from_csv(
    content: bytes,
    url: str,
    source: Source,
) -> list[dict]:
    """
    Extract scheme records from CSV.
    Expects columns: name, description, eligibility, benefits (flexible).
    Returns a list of scheme dicts.
    """
    results = []
    try:
        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            name = (
                row.get("name") or row.get("scheme_name") or
                row.get("Name") or row.get("Scheme Name", "")
            ).strip()

            if not name:
                continue

            description = (
                row.get("description") or row.get("Description") or
                row.get("details") or ""
            ).strip()

            row_text = " ".join(str(v) for v in row.values())
            results.append({
                "name": name[:500],
                "description": description[:2000],
                "source_url": url,
                "url_hash": sha256_hash(f"{url}#{name}"),
                "content_hash": sha256_hash(row_text),
                "ministry_id": source.ministry_id,
                "search_synonyms": [],
                "eligibility_criteria": {},
                "benefits": {},
            })
    except Exception as e:
        print(f"  [csv] Extraction failed: {e}")

    return results


# ─── JSON ─────────────────────────────────────────────────────────────────────

def extract_from_json(
    content: bytes,
    url: str,
    source: Source,
) -> list[dict]:
    """
    Extract scheme records from JSON.
    Handles both a single scheme object and a list of schemes.
    """
    results = []
    try:
        data = json.loads(content.decode("utf-8", errors="replace"))

        # Normalize to list
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = data
        else:
            return results

        for item in items:
            if not isinstance(item, dict):
                continue

            name = (
                item.get("name") or item.get("scheme_name") or
                item.get("title") or ""
            ).strip()

            if not name:
                continue

            item_text = json.dumps(item)
            results.append({
                "name": name[:500],
                "description": str(item.get("description", ""))[:2000],
                "source_url": url,
                "url_hash": sha256_hash(f"{url}#{name}"),
                "content_hash": sha256_hash(item_text),
                "ministry_id": source.ministry_id,
                "eligibility_criteria": item.get("eligibility", item.get("eligibility_criteria", {})),
                "benefits": item.get("benefits", {}),
                "search_synonyms": item.get("synonyms", item.get("search_synonyms", [])),
            })
    except Exception as e:
        print(f"  [json] Extraction failed: {e}")

    return results


# ─── XLSX ─────────────────────────────────────────────────────────────────────

def extract_from_xlsx(
    content: bytes,
    url: str,
    source: Source,
) -> list[dict]:
    """Extract scheme records from Excel (XLSX) files."""
    results = []
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)

        for sheet in wb.worksheets:
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                continue

            # First row as headers
            headers = [str(h).strip().lower() if h else "" for h in rows[0]]

            for row in rows[1:]:
                row_dict = dict(zip(headers, row))
                name = str(row_dict.get("name") or row_dict.get("scheme name") or row_dict.get("scheme_name") or "").strip()
                if not name:
                    continue
                description = str(row_dict.get("description") or row_dict.get("details") or "").strip()
                row_text = " ".join(str(v) for v in row if v is not None)

                results.append({
                    "name": name[:500],
                    "description": description[:2000],
                    "source_url": url,
                    "url_hash": sha256_hash(f"{url}#{name}"),
                    "content_hash": sha256_hash(row_text),
                    "ministry_id": source.ministry_id,
                    "search_synonyms": [],
                    "eligibility_criteria": {},
                    "benefits": {},
                })
    except Exception as e:
        print(f"  [xlsx] Extraction failed: {e}")

    return results


# ─── DOCX ─────────────────────────────────────────────────────────────────────

def extract_from_docx(
    content: bytes,
    url: str,
    source: Source,
) -> Optional[dict]:
    """Extract scheme data from Word documents."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())

        if not text.strip():
            return None

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        title = lines[0][:500] if lines else "Untitled"

        return {
            "name": title,
            "description": text[:2000],
            "source_url": url,
            "url_hash": sha256_hash(url),
            "content_hash": sha256_hash(text[:5000]),
            "ministry_id": source.ministry_id,
            "search_synonyms": [],
            "eligibility_criteria": {},
            "benefits": {},
        }
    except Exception as e:
        print(f"  [docx] Extraction failed: {e}")
        return None


# ─── XML ──────────────────────────────────────────────────────────────────────

def extract_from_xml(
    content: bytes,
    url: str,
    source: Source,
) -> list[dict]:
    """Extract scheme records from XML files."""
    results = []
    try:
        root = ET.fromstring(content.decode("utf-8", errors="replace"))
        text = ET.tostring(root, encoding="unicode", method="text")

        # Try to find scheme elements
        scheme_tags = ["scheme", "Scheme", "yojana", "program", "Programme"]
        items = []
        for tag in scheme_tags:
            items = root.findall(f".//{tag}")
            if items:
                break

        if not items:
            # Treat whole document as one scheme
            name_el = root.find(".//name") or root.find(".//title")
            name = name_el.text.strip() if name_el is not None and name_el.text else root.tag

            results.append({
                "name": name[:500],
                "description": text[:2000],
                "source_url": url,
                "url_hash": sha256_hash(url),
                "content_hash": sha256_hash(text[:5000]),
                "ministry_id": source.ministry_id,
                "search_synonyms": [],
                "eligibility_criteria": {},
                "benefits": {},
            })
            return results

        for item in items:
            name_el = item.find("name") or item.find("title")
            name = name_el.text.strip() if name_el is not None and name_el.text else "Unnamed"
            item_text = ET.tostring(item, encoding="unicode", method="text")

            results.append({
                "name": name[:500],
                "description": item_text[:2000],
                "source_url": url,
                "url_hash": sha256_hash(f"{url}#{name}"),
                "content_hash": sha256_hash(item_text),
                "ministry_id": source.ministry_id,
                "search_synonyms": [],
                "eligibility_criteria": {},
                "benefits": {},
            })
    except Exception as e:
        print(f"  [xml] Extraction failed: {e}")

    return results
