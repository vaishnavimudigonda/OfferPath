import os
import re
from pathlib import Path


def extract_text_from_file(file_path: str) -> str:
    """
    Extract readable text from a resume file (PDF, DOCX, or TXT).
    
    Args:
        file_path: Full filesystem path to the file.
        
    Returns:
        Cleaned extracted string content.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If file is unsupported or cannot be extracted.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found at: {file_path}")

    extension = path.suffix.lower().lstrip(".")
    extracted = ""

    if extension == "pdf":
        extracted = _extract_from_pdf(path)
    elif extension == "docx":
        extracted = _extract_from_docx(path)
    elif extension in ("txt", "text", "md"):
        extracted = _extract_from_txt(path)
    else:
        raise ValueError(f"Unsupported file format: .{extension}. Please upload PDF, DOCX, or TXT.")

    cleaned = _clean_extracted_text(extracted)
    if not cleaned or len(cleaned.strip()) < 20:
        raise ValueError("The uploaded file does not contain enough extractable text. Please ensure it is not scanned/empty.")

    return cleaned


def _extract_from_pdf(path: Path) -> str:
    """Extract text from PDF using pypdf or PyPDF2 fallback."""
    text_chunks = []
    
    # Try pypdf first (modern standard)
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    except ImportError:
        # Fallback to PyPDF2
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(path))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF with PyPDF2: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")

    return "\n".join(text_chunks)


def _extract_from_docx(path: Path) -> str:
    """Extract text from DOCX document including paragraphs and tables."""
    try:
        import docx
        doc = docx.Document(str(path))
        text_chunks = []

        # Extract regular paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text_chunks.append(para.text)

        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_chunks.append(" | ".join(row_text))

        return "\n".join(text_chunks)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX file: {str(e)}")


def _extract_from_txt(path: Path) -> str:
    """Extract plain text with multiple encoding fallbacks."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file using standard encodings.")


def _clean_extracted_text(text: str) -> str:
    """Clean up redundant whitespace, form feeds, and null bytes."""
    if not text:
        return ""
    # Remove null characters
    text = text.replace("\x00", "")
    # Normalize line breaks
    text = re.sub(r"\r\n|\r", "\n", text)
    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple inline spaces
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
