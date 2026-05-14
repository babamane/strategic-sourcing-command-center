"""
LLM Client - Simple wrapper for Gemini and Llama models
Handles only LLM initialization and invocation
"""

import os
from typing import Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from llamaapi import LlamaAPI
from langchain_experimental.llms import ChatLlamaAPI
from langchain_openai import ChatOpenAI
from utils.config import Config


class LLMClient: 
    def __init__(self):
        if Config.LLM_PROVIDER == "google":
            self.llm = ChatGoogleGenerativeAI(model=Config.GOOGLE_LLM_MODEL, api_key=Config.GOOGLE_API_KEY)
        elif Config.LLM_PROVIDER == "llama":
            llama = LlamaAPI(Config.LLAMA_API_KEY)
            self.llm = ChatLlamaAPI(client=llama, model=Config.LLAMA_MODEL)
        elif Config.LLM_PROVIDER == "openai":
            self.llm = ChatOpenAI(model=Config.OPENAI_MODEL, api_key=Config.OPENAI_API_KEY)
        elif Config.LLM_PROVIDER == "ollama":
            self.llm = ChatOllama(model=Config.OLLAMA_MODEL,base_url=Config.OLLAMA_LOCAL_HOST)
        else:
            raise ValueError(f"Invalid LLM provider: {Config.LLM_PROVIDER}")

    def get_llm(self):
        return self.llm 

        

   