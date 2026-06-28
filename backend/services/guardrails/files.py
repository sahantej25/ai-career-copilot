"""File upload guardrails — type, size, and content safety."""
import io

from fastapi import HTTPException, UploadFile

from config import settings
from services.guardrails.constants import MAX_PDF_PAGES, MIN_UPLOAD_BYTES

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


def validate_upload_file(
    file: UploadFile,
    content: bytes,
    allowed_extensions: set[str],
) -> None:
    if len(content) < MIN_UPLOAD_BYTES:
        raise HTTPException(422, "Uploaded file is empty or too small.")

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            413,
            f"File exceeds {settings.max_file_size_mb}MB limit.",
        )

    filename = (file.filename or "").strip()
    if not filename or "." not in filename:
        raise HTTPException(415, "File must have a valid extension.")

    ext = filename.lower().rsplit(".", 1)[-1]
    if ext not in allowed_extensions:
        raise HTTPException(
            415,
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(allowed_extensions))}.",
        )

    if ext == "pdf":
        _validate_pdf(content)


def _validate_pdf(content: bytes) -> None:
    if PyPDF2 is None:
        return
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise HTTPException(422, "Password-protected PDFs are not supported.")
        page_count = len(reader.pages)
        if page_count > MAX_PDF_PAGES:
            raise HTTPException(
                422,
                f"PDF has {page_count} pages; maximum allowed is {MAX_PDF_PAGES}.",
            )
        if page_count == 0:
            raise HTTPException(422, "PDF contains no readable pages.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, f"Invalid or corrupted PDF: {exc}") from exc
