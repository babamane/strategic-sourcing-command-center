from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.llm_client import LLMClient
from utils.vector_db import VectorDBManager
from utils.config import Config


class SummaryAgent:
    """
    Summarizes an entire company's earnings document using hierarchical (map–reduce)
    summarization over chunks stored in the vector DB.

    Flow:
    1. Get ALL chunks for the company from VectorDBManager (already pre-split).
    2. Summarize each chunk individually (map step).
    3. Recursively combine these summaries (reduce step) until a single final summary.
    """

    def __init__(
        self,
        group_size: int = 5,
    ):
        # LLM client
        self.llm = LLMClient().get_llm()

        # Vector DB manager (already ingested via create_dbs.py)
        self.vector_db = VectorDBManager()

        # How many summaries to combine at each reduce step
        self.group_size = group_size

        # ---- Prompts ----
        self._load_prompts()
        
        # Concurrency control
        self._processing = set()

    def _load_prompts(self):
        """Load prompts from text files."""
        prompts_dir = Config.PROMPTS_DIR
        
        # Helper to read file content
        def read_prompt(filename):
            path = prompts_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Prompt file not found: {path}")
            return path.read_text(encoding="utf-8").strip()

        # Chunk Summary Prompt
        chunk_template = read_prompt("chunk_summary.txt")
        self.chunk_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert financial document summarizer. Create clear, faithful, and concise summaries."),
            ("user", chunk_template)
        ])

        # Reduce Summary Prompt
        reduce_template = read_prompt("reduce_summary.txt")
        self.reduce_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at combining multiple earnings summaries into a single, coherent summary."),
            ("user", reduce_template)
        ])

        # Full Summary Prompt
        full_template = read_prompt("full_summary.txt")
        self.full_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert financial analyst. Produce a comprehensive, structured summary."),
            ("user", full_template)
        ])

    # ------------------------------------------------------------------
    # Helper: Cache Management
    # ------------------------------------------------------------------
    def _get_summary_path(self, company_name: str) -> Path:
        """Get the path to the cached summary file for a company."""
        # Sanitize company name for filename
        safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_').lower()
        return Config.OUTPUT_DIR / f"{safe_name}_summary.md"

    def _save_summary(self, company_name: str, summary_text: str):
        """Save the summary to a file."""
        path = self._get_summary_path(company_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(summary_text, encoding="utf-8")
        print(f"[SummaryAgent] Saved summary to {path}")

    def _load_cached_summary(self, company_name: str) -> str | None:
        """Load summary from file if it exists."""
        path = self._get_summary_path(company_name)
        if path.exists():
            print(f"[SummaryAgent] Loading cached summary from {path}")
            return path.read_text(encoding="utf-8")
        return None

    # ------------------------------------------------------------------
    # Map step: summarize a single chunk
    # ------------------------------------------------------------------
    def _summarize_chunk(self, chunk_text: str) -> str:
        chain = self.chunk_summary_prompt | self.llm | StrOutputParser()
        return chain.invoke({"chunk_text": chunk_text})

    # ------------------------------------------------------------------
    # Reduce step: combine a list of summaries into a higher-level summary
    # ------------------------------------------------------------------
    def _combine_summaries(self, summaries: List[str], company_name: str) -> str:
        joined = "\n\n---\n\n".join(summaries)
        chain = self.reduce_summary_prompt | self.llm | StrOutputParser()
        return chain.invoke({"summaries": joined, "company": company_name})

    # ------------------------------------------------------------------
    # Hierarchical reduce: keep combining until only one summary remains
    # ------------------------------------------------------------------
    def _hierarchical_reduce(self, summaries: List[str], company_name: str) -> str:
        """
        Recursively combine summaries in groups of self.group_size
        until only one final summary remains.
        """
        current = summaries

        while len(current) > 1:
            next_level: List[str] = []
            for i in range(0, len(current), self.group_size):
                group = current[i : i + self.group_size]
                combined = self._combine_summaries(group, company_name)
                next_level.append(combined)
            current = next_level

        return current[0]

    # ------------------------------------------------------------------
    # Fast step: summarize full text in one go
    # ------------------------------------------------------------------
    def _summarize_full_text(self, full_text: str) -> str:
        """
        Summarizes the entire document text in a single LLM call.
        Truncates to 700k characters to fit within context limits if necessary.
        """
        # Truncate to 700k characters
        limit = 700_000
        if len(full_text) > limit:
            print(f"[SummaryAgent] Text length {len(full_text)} exceeds {limit}. Truncating...")
            full_text = full_text[:limit]
        
        chain = self.full_summary_prompt | self.llm | StrOutputParser()
        return chain.invoke({"text": full_text})

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes the full-document summary generation process.

        Expected input_data:
          {
            "company_name": "Microsoft"
          }

        Returns:
          {
            "messages": [
              {
                "role": "assistant",
                "content": "<final summary text>"
              }
            ]
          }
        """
        company_name = input_data.get("company_name")
        method = Config.SUMMARY_METHOD  # Use config instead of input argument

        if not company_name:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Error: Company name not provided."
                    }
                ]
            }

        try:
            # Refresh LLM client to ensure fresh config (e.g. if API key changed)
            self.llm = LLMClient().get_llm()
            
            # Debug: Print model info
            provider = Config.LLM_PROVIDER.upper()
            if Config.LLM_PROVIDER == "openai":
                model = Config.OPENAI_MODEL
                api_key = Config.OPENAI_API_KEY
            elif Config.LLM_PROVIDER == "google":
                model = Config.GOOGLE_LLM_MODEL
                api_key = Config.GOOGLE_API_KEY
            elif Config.LLM_PROVIDER == "ollama":
                model = Config.OLLAMA_MODEL
                api_key = None
            else:
                model = Config.LLAMA_MODEL
                api_key = Config.LLAMA_API_KEY
            
            print(f"[SummaryAgent] Using {provider} Model: {model}")
            key_preview = f"{api_key[:10]}..." if api_key else "None"
            print(f"[SummaryAgent] Active API Key: {key_preview}")

            # 1. Check Cache
            cached_summary = self._load_cached_summary(company_name)
            if cached_summary:
                # Artificial delay for UX consistency as requested
                import time
                time.sleep(8)
                return {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": cached_summary,
                        }
                    ]
                }

            # 2. Check if already processing
            import time
            while company_name in self._processing:
                print(f"[SummaryAgent] {company_name} is already being processed. Waiting...")
                time.sleep(3)
                # Check cache again in case it finished
                cached_summary = self._load_cached_summary(company_name)
                if cached_summary:
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": cached_summary,
                            }
                        ]
                    }
            
            # Mark as processing
            self._processing.add(company_name)
            
            try:
                # 3. Generate if not cached
                print(f"[SummaryAgent] Getting all chunks from vector DB for {company_name}...")
                # This uses your pre-built vector DB; chunks are already split and ordered
                chunk_texts: List[str] = self.vector_db.get_all_chunk_texts(company_name)
                total_chunks = len(chunk_texts)
                print(f"[SummaryAgent] Found {total_chunks} chunks for {company_name}.")

                if total_chunks == 0:
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": (
                                    f"Error: No chunks found in the vector DB for {company_name}. "
                                    "Make sure you ran the ingestion (create_dbs.py) successfully."
                                ),
                            }
                        ]
                    }

                final_body = ""

                if method == "map_reduce":
                    # --- Map-Reduce ---
                    print(f"[SummaryAgent] Using Map-Reduce approach (slower, more detailed)...")
                    
                    # Map step: summarize each chunk individually
                    print(f"[SummaryAgent] Summarizing each chunk (map step)...")
                    chunk_summaries: List[str] = []
                    import time
                    for idx, chunk in enumerate(chunk_texts, start=1):
                        print(f"[SummaryAgent] Summarizing chunk {idx}/{total_chunks}...")
                        summary = self._summarize_chunk(chunk)
                        chunk_summaries.append(summary)
                        # Rate limiting for free tier (approx 15 RPM)
                        time.sleep(4)

                    # Reduce step: hierarchically combine all chunk summaries
                    print(f"[SummaryAgent] Combining chunk summaries hierarchically (reduce step)...")
                    final_body = self._hierarchical_reduce(chunk_summaries, company_name)

                else:
                    # --- Fast / Single-Shot ---
                    print(f"[SummaryAgent] Using Fast approach (single-shot, 700k limit)...")
                    
                    # Join all chunks into one massive string
                    full_text = "\n\n".join(chunk_texts)
                    final_body = self._summarize_full_text(full_text)

                # 4. Save to Cache
                self._save_summary(company_name, final_body)

                # Return the final body
                return {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": final_body,
                        }
                    ]
                }
            
            finally:
                # Ensure we remove the lock even if errors occur
                if company_name in self._processing:
                    self._processing.remove(company_name)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Error generating summary: {str(e)}",
                    }
                ]
            }


# Singleton instance
agent = SummaryAgent()
