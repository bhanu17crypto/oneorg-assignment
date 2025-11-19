from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import uuid
import time
import traceback
import uvicorn

from document_processor import DocumentProcessor
from rag_pipeline import RAGPipeline

app = FastAPI(title="Context-Aware RAG Pipeline")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
try:
    document_processor = DocumentProcessor()
    rag_pipeline = RAGPipeline()
except Exception:
    print("\nERROR INITIALIZING PIPELINE COMPONENTS:")
    print(traceback.format_exc())
    raise

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query: str

class IngestionResponse(BaseModel):
    message: str
    processed_files: List[str]
    total_chunks: int

@app.post("/ingest", response_model=IngestionResponse)
async def ingest_documents(files: List[UploadFile] = File(...)):
    try:
        processed_files = []
        total_chunks = 0
        for file in files:
            file_path = f"temp_{uuid.uuid4()}_{file.filename}"
            content = await file.read()
            await file.close()
            with open(file_path, "wb") as f:
                f.write(content)
            chunks = document_processor.process_document(file_path, file.filename)
            processed_files.append(file.filename)
            total_chunks += len(chunks)
            for _ in range(5):
                try:
                    os.remove(file_path)
                    break
                except PermissionError:
                    time.sleep(0.2)

        return IngestionResponse(
            message="Documents ingested successfully",
            processed_files=processed_files,
            total_chunks=total_chunks,
        )
    except Exception as e:
        print("\n ERROR DURING INGEST:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing documents: {e}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        response_data = rag_pipeline.query(
            query=request.query,
            top_k=request.top_k
        )
        return QueryResponse(
            answer=response_data["answer"],
            sources=response_data["sources"],
            query=response_data["query"]
        )
    except Exception:
        print("\nERROR PROCESSING QUERY:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error while generating answer.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
