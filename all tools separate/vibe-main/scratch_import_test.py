import sys
from pathlib import Path

print("Testing imports...")
try:
    from langchain_pymupdf4llm import PyMuPDF4LLMLoader
    print("[OK] langchain_pymupdf4llm imported")
    from langchain_chroma import Chroma
    print("[OK] langchain_chroma imported")
    from langchain_huggingface import HuggingFaceEmbeddings
    print("[OK] langchain_huggingface imported")
    from langchain_openai import OpenAIEmbeddings
    print("[OK] langchain_openai imported")
    from fastapi import FastAPI
    print("[OK] fastapi imported")
    import uvicorn
    print("[OK] uvicorn imported")
    print("All critical imports successful!")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
