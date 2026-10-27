from __future__ import annotations

import base64
import binascii
import hmac
import os
import secrets
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import pymupdf
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from booklet_engine import arrange_booklet


APP_DIR = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
SESSION_TTL_SECONDS = 60 * 60
MAX_PAGES = 1000

_session_dir: tempfile.TemporaryDirectory[str] | None = None
_sessions: dict[str, tuple[Path, int, float]] = {}
_sessions_lock = threading.Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _session_dir
    if os.getenv("APP_AUTH_ENABLED", "").lower() == "true":
        if not os.getenv("APP_USERNAME") or not os.getenv("APP_PASSWORD"):
            raise RuntimeError(
                "APP_USERNAME and APP_PASSWORD must be set when authentication is enabled."
            )

    _session_dir = tempfile.TemporaryDirectory(prefix="starz-booklet-")
    try:
        yield
    finally:
        with _sessions_lock:
            _sessions.clear()
        _session_dir.cleanup()
        _session_dir = None


app = FastAPI(title="STARz Booklet Maker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")


@app.middleware("http")
async def require_basic_auth(request, call_next):
    if os.getenv("APP_AUTH_ENABLED", "").lower() != "true":
        return await call_next(request)

    username = os.environ["APP_USERNAME"]
    password = os.environ["APP_PASSWORD"]
    authorization = request.headers.get("authorization", "")
    scheme, separator, encoded_credentials = authorization.partition(" ")

    if scheme.lower() == "basic" and separator:
        try:
            credentials = base64.b64decode(
                encoded_credentials, validate=True
            ).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            credentials = ""

        supplied_username, delimiter, supplied_password = credentials.partition(":")
        if (
            delimiter
            and hmac.compare_digest(supplied_username, username)
            and hmac.compare_digest(supplied_password, password)
        ):
            return await call_next(request)

    return Response(
        content="Authentication required.",
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="STARz Booklet Maker"'},
    )


class GenerateRequest(BaseModel):
    session_id: str
    page_numbers: list[int]


def _get_session(session_id: str) -> tuple[Path, int]:
    with _sessions_lock:
        session = _sessions.get(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail="This upload has expired. Please upload the PDF again.",
            )

        path, page_count, last_used = session
        if time.monotonic() - last_used > SESSION_TTL_SECONDS:
            _sessions.pop(session_id, None)
            path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=404,
                detail="This upload has expired. Please upload the PDF again.",
            )

        _sessions[session_id] = (path, page_count, time.monotonic())
        return path, page_count


@app.get("/")
def home() -> FileResponse:
    return FileResponse(APP_DIR / "static" / "index.html")


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)) -> dict[str, object]:
    if _session_dir is None:
        raise HTTPException(status_code=503, detail="The server is starting.")

    data = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDFs must be 50 MB or smaller.",
        )

    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            page_count = len(document)
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Could not read this file as a PDF.",
        ) from error

    if page_count == 0:
        raise HTTPException(status_code=400, detail="This PDF contains no pages.")
    if page_count > MAX_PAGES:
        raise HTTPException(
            status_code=413,
            detail=f"PDFs must contain {MAX_PAGES} pages or fewer.",
        )

    session_id = secrets.token_urlsafe(24)
    path = Path(_session_dir.name) / f"{session_id}.pdf"
    path.write_bytes(data)

    now = time.monotonic()
    with _sessions_lock:
        expired = [
            old_path
            for old_path, _, last_used in _sessions.values()
            if now - last_used > SESSION_TTL_SECONDS
        ]
        for expired_path in expired:
            expired_path.unlink(missing_ok=True)
        _sessions.update(
            {
                key: value
                for key, value in _sessions.items()
                if now - value[2] <= SESSION_TTL_SECONDS
            }
        )
        _sessions[session_id] = (path, page_count, now)

    filename = Path(file.filename or "document.pdf").name
    return {
        "session_id": session_id,
        "filename": filename,
        "page_count": page_count,
    }


@app.get("/api/session/{session_id}/thumbnail/{page_number}")
def page_thumbnail(
    session_id: str,
    page_number: int,
    scale: int = Query(default=30, ge=10, le=100),
) -> Response:
    path, page_count = _get_session(session_id)
    if not 1 <= page_number <= page_count:
        raise HTTPException(status_code=404, detail="Page not found.")

    try:
        with pymupdf.open(path) as document:
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(scale / 100, scale / 100),
                alpha=False,
            )
            image = pixmap.tobytes("png")
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Could not render this PDF page.",
        ) from error

    return Response(
        content=image,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@app.post("/api/generate")
def generate_booklet(request: GenerateRequest) -> Response:
    path, page_count = _get_session(request.session_id)
    page_numbers = sorted(set(request.page_numbers))

    if not page_numbers:
        raise HTTPException(
            status_code=400,
            detail="Select at least one page to include.",
        )
    if any(number < 1 or number > page_count for number in page_numbers):
        raise HTTPException(
            status_code=400,
            detail=f"Page numbers must be between 1 and {page_count}.",
        )

    sheets = arrange_booklet([number - 1 for number in page_numbers])
    output = pymupdf.open()
    try:
        with pymupdf.open(path) as source:
            a4_width = 841.8898
            a4_height = 595.2756
            half_width = a4_width / 2

            for front_left, front_right, back_left, back_right in sheets:
                for left_page, right_page in (
                    (front_left, front_right),
                    (back_left, back_right),
                ):
                    sheet = output.new_page(width=a4_width, height=a4_height)
                    left_rect = pymupdf.Rect(0, 0, half_width, a4_height)
                    right_rect = pymupdf.Rect(
                        half_width, 0, a4_width, a4_height
                    )

                    if left_page is not None:
                        sheet.show_pdf_page(
                            left_rect, source, left_page, keep_proportion=True
                        )
                    if right_page is not None:
                        sheet.show_pdf_page(
                            right_rect, source, right_page, keep_proportion=True
                        )

        pdf_bytes = output.tobytes(garbage=4, deflate=True)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Could not generate the booklet PDF.",
        ) from error
    finally:
        output.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="booklet.pdf"'},
    )
