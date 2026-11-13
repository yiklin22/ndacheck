"""Web page: upload or paste an NDA, get the 17 answers with their clauses.

  uvicorn ndacheck.app:app --port 8850
"""
import io
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .check import check

app = FastAPI(title="ndacheck")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
MAX_BYTES = 10 * 1024 * 1024
SAY = {"Entailment": "Yes", "Contradiction": "No", "NotMentioned": "Not mentioned"}


def read_text(name: str, data: bytes) -> str:
    low = name.lower()
    if len(data) > MAX_BYTES:
        raise ValueError("file is larger than 10 MB")
    if low.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n\n".join(p.extract_text() or "" for p in pdf.pages)
        if not text.strip():
            raise ValueError("the PDF has no text layer (a scan?); OCR is not supported")
        return text
    if low.endswith(".docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
    if low.endswith(".txt"):
        return data.decode("utf-8", errors="replace")
    raise ValueError("only .pdf, .docx and .txt files are supported")


@app.get("/", response_class=HTMLResponse)
def page(request: Request):
    return templates.TemplateResponse(request, "index.html", {"text": ""})


@app.post("/", response_class=HTMLResponse)
async def run(request: Request, text: str = Form(""), file: UploadFile | None = File(None)):
    if file is not None and file.filename:
        try:
            text = read_text(file.filename, await file.read())
        except ValueError as e:
            return templates.TemplateResponse(request, "index.html", {"text": "", "error": str(e)})
    if not text.strip():
        return templates.TemplateResponse(request, "index.html", {"text": "", "error": "paste an NDA or upload a file"})
    answers = [dict(a.__dict__, say=SAY[a.label]) for a in check(text)]
    return templates.TemplateResponse(request, "index.html", {"text": text, "answers": answers})
