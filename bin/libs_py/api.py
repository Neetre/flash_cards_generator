import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import date

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from model import AnalyzeDocs, ReadDocs
from dotenv import load_dotenv
load_dotenv()

if os.path.exists("../log") is False:
    os.mkdir("../log")

if os.path.exists("../log/flash_cards.log") is False:
    with open("../log/flash_cards.log", "w") as f:
        f.write("")

import logging
logging.basicConfig(
    filename="../log/flash_cards.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Path("../log").mkdir(exist_ok=True)
Path("../log/flash_cards.log").touch(exist_ok=True)

app = FastAPI(
    title="Flash Cards API",
    description="API for processing flash cards.",
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)
class Config:
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

@app.middleware("http")
async def file_size_middleware(request: Request, call_next):
    if request.method == "POST" and "multipart/form-data" in request.headers.get("content-type", ""):
        content_length = int(request.headers.get("content-length", 0))
        if content_length > Config.MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": f"File too large. Maximum size is {Config.MAX_FILE_SIZE // (1024 * 1024)} MB"}
            )
    return await call_next(request)


class User(BaseModel):
    username: str
    password: str


analyze_docs = AnalyzeDocs()
read_docs = ReadDocs()

@app.post("/login")
async def login(user: User):
    try:
        if user.username == "admin" and user.password == "password":
            return {"message": "Login successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/register")
async def register(user: User):
    try:
        if user.username == "admin" and user.password == "password":
            return {"message": "Login successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

@app.post("/upload/")
async def upload_file(document: UploadFile = File(...), language: str = Form(...), num_flashcards: int = Form(...)) -> Dict[str, Any]:
    try:
        logger.info(f"Received file: {document.filename}, Language: {language}, Num Flashcards: {num_flashcards}")

        if document.content_type not in ["application/pdf", "text/plain"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and text files are allowed.")

        file_content = await document.read()
        with open(f"input/{document.filename}", "wb") as f:
            f.write(file_content)

        logger.info(f"File saved: {document.filename}")

        file_type = "pdf" if document.content_type == "application/pdf" else "text"
        text = read_docs.read_document(file_type, document.filename)
        logging.info(f"Text extracted from {document.filename}:\n{text}")
        generated_flashcards = analyze_docs.generate_flashcards(text, num_flashcards, language)
        json_flashcards = analyze_docs.flashcards_to_json(generated_flashcards)
        logger.info(f"Generated flashcards: {json_flashcards}")
        os.remove(f"input/{document.filename}")

        return {"flashcards": json_flashcards}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/download")
async def download_file(file_name: str):
    try:
        file_path = Path(f"../output/{file_name}")
        if file_path.exists():
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)