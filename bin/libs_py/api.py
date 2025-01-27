import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import date

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from model import AnalyzeDocs, ReadDocs
from security import Security

from dotenv import load_dotenv
load_dotenv()

from data_manager import SQLiteDBManager
manager = SQLiteDBManager()
key = os.getenv("SECRET_KEY")


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
    allow_origins=["http://fc.figliolo.it"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


analyze_docs = AnalyzeDocs()
read_docs = ReadDocs()

@app.post("/login")
async def login(user: LoginRequest):
    # print("Received payload:", user.model_dump()) 
    try:
        if not user.username or not user.password:
            raise HTTPException(
                status_code=422,
                detail="Username and password are required"
            )

        user_found = manager.fetch_user(user.username)
        if not user_found:
            raise HTTPException(
                status_code=404,
                detail="User not found. Please register."
            )
        stored_encrypted_password = user_found[3]
        if isinstance(stored_encrypted_password, str):
            stored_encrypted_password = stored_encrypted_password.encode('utf-8')

        if not Security.verify_password(user.password, stored_encrypted_password, key):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        return {"message": "Login successful"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/register")
async def register(user: User):
    try:
        if user.username is not None and user.email is not None and user.password is not None:
            user_found = manager.fetch_user(user.username)
            if user_found is not None:
                return {"message": "User already exists. Please login."}
            enc_pwd = Security.encrypt_password(user.password, key)
            manager.insert_user(user.username, user.email, enc_pwd)
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


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
