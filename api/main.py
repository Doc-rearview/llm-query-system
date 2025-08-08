from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from app.retrieval import get_answer, process_documents
from app.config import DATA_DIR
import os
from typing import List

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "LLM Query-Retrieval System is running!"}

@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    # Save uploaded files to DATA_DIR
    for file in files:
        if not file.filename.endswith(".pdf"):
            continue
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
    
    # Process the newly uploaded documents
    try:
        process_documents()
        return JSONResponse(content={"status": "success", "message": "Files uploaded and processed successfully"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.post("/query/")
async def query_llm(question: str):
    try:
        answer = get_answer(question)
        return JSONResponse(content={
            "status": "success",
            "question": question,
            "answer": answer,
            "source": "gemini" if answer.startswith("Answering:gem") else "retrieval"
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)