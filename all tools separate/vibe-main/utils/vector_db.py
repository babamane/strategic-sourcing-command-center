import os
from pathlib import Path
from typing import List, Optional

from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from utils.config import Config


class VectorDBManager:
    def __init__(self):
        # Base directory where all per-company vector DBs live
        self.persist_directory = Config.BASE_DIR / "vector_dbs"
        self.persist_directory.mkdir(exist_ok=True)

        # Choose embeddings based on provider
        if Config.LLM_PROVIDER == "google":
            # Use local model (embeddinggemma is gated, so we use MiniLM)
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        elif Config.LLM_PROVIDER == "openai":
            self.embeddings = OpenAIEmbeddings(api_key=Config.OPENAI_API_KEY)
        else:
            # Fallback to local model
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _get_company_db_dir(self, company_name: str) -> Path:
        """
        Normalize company name to a folder name.
        Example: 'Microsoft' -> 'microsoft'
        """
        return self.persist_directory / company_name.lower().replace(" ", "_")

    def _load_vectorstore(self, company_name: str) -> Chroma:
        """
        Load an existing Chroma vectorstore for a given company.
        """
        company_db_dir = self._get_company_db_dir(company_name)
        if not company_db_dir.exists():
            raise ValueError(
                f"Vector DB for {company_name} not found at {company_db_dir}. "
                f"Run create_vector_db() or create_dbs.py first."
            )

        vectorstore = Chroma(
            embedding_function=self.embeddings,
            persist_directory=str(company_db_dir),
        )
        return vectorstore

    # ---------------------------------------------------------------------
    # Ingestion: create vector DB per company
    # ---------------------------------------------------------------------
    def create_vector_db(self, company_name: str, pdf_path: str):
        """
        Creates (or overwrites) a vector database for a specific company's document
        using PyMuPDF4LLMLoader.

        - Reads the PDF
        - Splits into chunks
        - Adds useful metadata (company_name, file_name, chunk_index)
        - Stores in Chroma at: vector_dbs/{company_name_normalized}
        """
        print(f"Creating vector DB for {company_name} from {pdf_path}...")

        pdf_path = str(pdf_path)
        file_name = Path(pdf_path).name

        # Use PyMuPDF4LLMLoader for LLM-optimized text extraction
        loader = PyMuPDF4LLMLoader(pdf_path)
        docs = loader.load()  # List[Document]

        # Attach base metadata at document level
        for d in docs:
            if d.metadata is None:
                d.metadata = {}
            d.metadata["company_name"] = company_name
            d.metadata["file_name"] = file_name

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=300,
            add_start_index=True,
        )
        splits = text_splitter.split_documents(docs)

        # Add chunk index metadata so we can sort later
        for idx, d in enumerate(splits):
            if d.metadata is None:
                d.metadata = {}
            d.metadata.setdefault("company_name", company_name)
            d.metadata.setdefault("file_name", file_name)
            d.metadata["chunk_index"] = idx

        # Use a separate directory for each company
        company_db_dir = self._get_company_db_dir(company_name)

        # If an old DB exists, you may optionally clear it
        # (uncomment if you want clean rebuilds)
        # if company_db_dir.exists():
        #     import shutil
        #     shutil.rmtree(company_db_dir)

        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=str(company_db_dir),
        )
        print(
            f"Vector DB created for {company_name} in {company_db_dir} "
            f"with {len(splits)} chunks."
        )
        return vectorstore

    # ---------------------------------------------------------------------
    # Retriever: top-k similarity search (for Q&A)
    # ---------------------------------------------------------------------
    def get_retriever(self, company_name: str, k: int = 6):
        """
        Gets a similarity retriever for a specific company.

        This is what you'll typically use in a RAG chain for Q&A:
          retriever = db_manager.get_retriever("Microsoft", k=6)
          docs = retriever.invoke("What was total revenue?")
        """
        vectorstore = self._load_vectorstore(company_name)

        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )
        return retriever

    # ---------------------------------------------------------------------
    # NEW: Get all chunks for a company (for full-document summarization)
    # ---------------------------------------------------------------------
    def get_all_chunks(self, company_name: str) -> List[Document]:
        """
        Return ALL chunks (as LangChain Documents) for a given company.

        This is ideal for:
        - Hierarchical / map-reduce summarization over the full document.
        - Any processing where you want every chunk, not just top-k.

        Since each company has its own persist_directory, we simply read
        everything in that vectorstore and sort by chunk_index.
        """
        vectorstore = self._load_vectorstore(company_name)

        # Access underlying Chroma collection to fetch all documents + metadata
        raw = vectorstore._collection.get(include=["documents", "metadatas"])
        documents: List[str] = raw.get("documents", [])
        metadatas: List[dict] = raw.get("metadatas", [])

        docs: List[Document] = []
        for content, meta in zip(documents, metadatas):
            meta = meta or {}
            docs.append(Document(page_content=content, metadata=meta))

        # Sort by chunk_index if present, so order roughly follows the original doc
        docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))

        return docs

    def get_all_chunk_texts(self, company_name: str) -> List[str]:
        """
        Convenience helper: return only the text content (page_content)
        of all chunks for a given company.
        """
        return [d.page_content for d in self.get_all_chunks(company_name)]
