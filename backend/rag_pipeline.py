import os
import json
from typing import List, Dict, Any
from uuid import uuid4
from pinecone import Pinecone
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import OpenAI
import cohere
import redis
load_dotenv()
class RAGPipeline:
    def __init__(self):
        print("🔹 Initializing RAGPipeline...")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index("raga")
        self.cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))
        self.llm = ChatOpenAI(
            temperature=0.1,
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.prompt = PromptTemplate(
            template=(
                "You are a helpful assistant. Answer strictly based on the context.\n\n"
                "Context:\n{context}\n\n"
                "Question: {question}\n\n"
                "If answer is not in the context, reply: "
                "'I cannot answer based on the provided documents.'"
            ),
            input_variables=["context", "question"],
        )

        self.output_parser = StrOutputParser()
        self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        print("✔️ RAGPipeline initialization complete.")

    def generate_embedding(self, text: str):
        print(f"\n🧠 Generating embedding for query:\n{text}\n")
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        print("✔️ Embedding generated.")
        return response.data[0].embedding

    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        print(f"\n🔍 Retrieving top {top_k} chunks from Pinecone for query:\n{query}")
        query_embedding = self.generate_embedding(query)
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        contexts = []
        for match in results["matches"]:
            print(f"\n📄 Retrieved Chunk:\n"
                  f"ID: {match['id']}\n"
                  f"Score: {match['score']}\n"
                  f"Source: {match['metadata']['source']}\n"
                  f"Page: {match['metadata']['page']}\n"
                  f"Content Preview: {match['metadata']['text'][:200]}...")
            contexts.append({
                "chunk_text": match["metadata"]["text"],
                "source_filename": match["metadata"]["source"],
                "page_number": match["metadata"]["page"],
                "chunk_id": match["id"],
                "score": match["score"],
            })

        print(f"\n✔️ Total {len(contexts)} chunks retrieved.")
        return contexts

    def rerank_contexts(self, query: str, contexts: List[Dict[str, Any]], top_n: int = 3):
        print(f"\n⚖️ Performing Re-Ranking using Cohere for top {top_n} context chunks...")
        documents = [c["chunk_text"] for c in contexts]
        rerank_results = self.cohere_client.rerank(
            query=query,
            documents=documents,
            top_n=top_n,
            model="rerank-english-v3.0"
        )

        reranked_contexts = []
        for result in rerank_results.results:
            original_context = contexts[result.index]
            original_context["rerank_score"] = result.relevance_score
            print(f"\n🆎 Reranked Chunk:\n"
                  f"Original Rank: {result.index}\n"
                  f"Relevance Score: {result.relevance_score}\n"
                  f"Content Preview: {original_context['chunk_text'][:200]}...")
            reranked_contexts.append(original_context)

        print("\n✔️ Re-Ranking complete.\n")
        return sorted(reranked_contexts, key=lambda x: x["rerank_score"], reverse=True)

    def generate_answer(self, query: str, contexts: List[Dict[str, Any]]):
        print(f"\n💬 Generating final answer using GPT for query:\n{query}")
        if not contexts:
            print("⚠️ No relevant context found.")
            return "I cannot answer based on the provided documents.", []

        combined_context = "\n\n".join(
            [
                f"Source: {c['source_filename']} (Page {c['page_number']})\nContent: {c['chunk_text']}\n"
                for c in contexts
            ]
        )

        print("\n📚 Final merged context being passed to GPT:\n")
        print(combined_context[:1000], "...") 

        chain = self.prompt | self.llm | self.output_parser
        answer = chain.invoke({"context": combined_context, "question": query})

        print("\n✔️ Final Answer Generated.")
        return answer, contexts

    def query(self, query: str, top_k: int = 5, rerank_top_n: int = 3):
        cache_key = f"query_cache:{query.lower()}"
        cached_response = self.redis.get(cache_key)
        if cached_response:
            print("🔄 Cache Hit! Returning cached result.")
            return json.loads(cached_response)

        print("⚡ Cache Miss! Running full RAG pipeline...")
        contexts = self.retrieve_context(query, top_k)
        reranked_contexts = self.rerank_contexts(query, contexts, rerank_top_n)
        answer, contexts_used = self.generate_answer(query, reranked_contexts)
        response_data = {
            "answer": answer,
            "sources": contexts_used,
            "query": query
        }
        self.redis.setex(cache_key, 86400, json.dumps(response_data))
        return response_data
