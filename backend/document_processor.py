import os
import PyPDF2
from docx import Document
import pandas as pd
from uuid import uuid4
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
load_dotenv()


class DocumentProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        if "raga" not in pc.list_indexes().names():
            pc.create_index(
                name="raga",
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        self.index = pc.Index("raga")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2500,  
            chunk_overlap=800, 
            length_function=len,
        )

    def generate_embedding(self, text: str):
        """Generate embedding using text-embedding-3-small"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def create_chunk(self, chunk_text, filename, page_number):
        return {
            "chunk_id": str(uuid4()),
            "chunk_text": chunk_text,
            "source_filename": filename,
            "page_number": page_number,
            "embedding": self.generate_embedding(chunk_text), 
        }

    def process_pdf(self, file_path, filename):
        chunks = []
        pdf = PyPDF2.PdfReader(open(file_path, "rb"))

        for page_number, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text or not text.strip():
                continue

            for chunk_text in self.text_splitter.split_text(text):
                chunks.append(self.create_chunk(chunk_text, filename, page_number + 1))

        return chunks
    def process_txt(self, file_path, filename):
        text = open(file_path, "r", encoding="utf-8").read()
        return [
            self.create_chunk(chunk, filename, 1)
            for chunk in self.text_splitter.split_text(text)
        ]

    def process_docx(self, file_path, filename):
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return [
            self.create_chunk(chunk, filename, 1)
            for chunk in self.text_splitter.split_text(text)
        ]

    def process_csv(self, file_path, filename):
        df = pd.read_csv(file_path)
        text = "\n".join([" | ".join([f"{col}: {val}" for col, val in row.items()]) for _, row in df.iterrows()])
        return [
            self.create_chunk(chunk, filename, 1)
            for chunk in self.text_splitter.split_text(text)
        ]

    def process_document(self, file_path, filename):
        ext = filename.split(".")[-1].lower()
        if ext == "pdf":
            chunks = self.process_pdf(file_path, filename)
        elif ext == "txt":
            chunks = self.process_txt(file_path, filename)
        elif ext == "docx":
            chunks = self.process_docx(file_path, filename)
        elif ext == "csv":
            chunks = self.process_csv(file_path, filename)
        else:
            raise ValueError("Unsupported file type")
        if chunks:
            vectors = [
                (
                    c["chunk_id"],
                    c["embedding"],
                    {
                        "text": c["chunk_text"],
                        "source": c["source_filename"],
                        "page": c["page_number"],
                    }
                )
                for c in chunks
            ]

            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                self.index.upsert(vectors=vectors[i:i + batch_size])
        return chunks
