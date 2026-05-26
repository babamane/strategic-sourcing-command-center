import os
from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path

class RAGToolInput(BaseModel):
    query: str = Field(description="The search query to look up in the knowledge base.")
    company_name: str = Field(description="The name of the company to search data for (e.g., 'Meta', 'Microsoft').")

class RAGTool(BaseTool):
    name: str = "knowledge_base_search"
    description: str = "Use this tool to search for specific information about a company's earnings, financials, or transcripts from the local knowledge base. ALWAYS use this tool FIRST before searching the internet."
    args_schema: Type[BaseModel] = RAGToolInput

    def _run(self, query: str, company_name: str) -> str:
        try:
            # Normalize company name for path
            safe_company_name = company_name.lower().replace(" ", "_")
            
            # Locate vector DB
            # Assuming vector_dbs is in the project root/vector_dbs
            # Adjust path logic if your structure is different
            base_dir = Path(__file__).resolve().parents[1]
            persist_dir = base_dir / "vector_dbs" / safe_company_name
            
            if not persist_dir.exists():
                return f"Error: No knowledge base found for company '{company_name}'. Please ensure the vector database is created."

            # Initialize embeddings from the local cache only. If the model is
            # not cached, fail fast instead of blocking the chatbot on network retries.
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            embedding = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"local_files_only": True},
            )
            vectorstore = Chroma(
                persist_directory=str(persist_dir),
                embedding_function=embedding
            )
            
            # Perform search
            # k=4 to get a good amount of context
            docs = vectorstore.similarity_search(query, k=4)
            
            if not docs:
                return "No relevant information found in the knowledge base."
            
            # Format results
            results = []
            for i, doc in enumerate(docs):
                source = doc.metadata.get('file_name', 'Unknown')
                page = doc.metadata.get('page', doc.metadata.get('page_number', 'N/A'))
                content = doc.page_content
                results.append(f"Source {i+1} (File: {source}, Page: {page}):\n{content}\n")
                
            return "\n---\n".join(results)

        except Exception as e:
            return f"Error querying knowledge base: {str(e)}"

    def _arun(self, query: str, company_name: str):
        raise NotImplementedError("RAGTool does not support async")
