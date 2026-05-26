"""
LLM Client - Simple wrapper for Gemini and Llama models
Handles only LLM initialization and invocation
"""

from utils.config import Config


class LocalOllamaChat:
    def __init__(self, model: str, base_url: str):
        from langchain_core.language_models.chat_models import BaseChatModel

        class _DirectOllamaChat(BaseChatModel):
            model: str
            base_url: str

            @property
            def _llm_type(self) -> str:
                return "direct-ollama-chat"

            def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                import requests
                from langchain_core.messages import AIMessage
                from langchain_core.outputs import ChatGeneration, ChatResult

                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": self._message_role(message),
                            "content": getattr(message, "content", str(message)),
                        }
                        for message in messages
                    ],
                    "stream": False,
                }
                if stop:
                    payload["options"] = {"stop": stop}

                response = requests.post(
                    f"{self.base_url.rstrip('/')}/api/chat",
                    json=payload,
                    timeout=Config.OLLAMA_TIMEOUT,
                )
                response.raise_for_status()
                content = response.json().get("message", {}).get("content", "")
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

            @staticmethod
            def _message_role(message) -> str:
                message_type = getattr(message, "type", "")
                if message_type == "human":
                    return "user"
                if message_type == "ai":
                    return "assistant"
                return "system"

        self._chat = _DirectOllamaChat(model=model, base_url=base_url)

    def get_llm(self):
        return self._chat


class LLMClient: 
    def __init__(self):
        print(f"DEBUG: LLMClient initializing with provider: {Config.LLM_PROVIDER}")
        if Config.LLM_PROVIDER == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(model=Config.GOOGLE_LLM_MODEL, api_key=Config.GOOGLE_API_KEY)
        elif Config.LLM_PROVIDER == "llama":
            from llamaapi import LlamaAPI
            from langchain_experimental.llms import ChatLlamaAPI
            llama = LlamaAPI(Config.LLAMA_API_KEY)
            self.llm = ChatLlamaAPI(client=llama, model=Config.LLAMA_MODEL)
        elif Config.LLM_PROVIDER == "openai":
            from langchain_openai import ChatOpenAI
            key_preview = f"{Config.OPENAI_API_KEY[:10]}...{Config.OPENAI_API_KEY[-4:]}" if Config.OPENAI_API_KEY else "None"
            print(f"DEBUG: Initializing OpenAI with key: {key_preview}")
            self.llm = ChatOpenAI(model=Config.OPENAI_MODEL, api_key=Config.OPENAI_API_KEY)
        elif Config.LLM_PROVIDER == "ollama":
            self.llm = LocalOllamaChat(
                model=Config.OLLAMA_MODEL,
                base_url=Config.OLLAMA_LOCAL_HOST,
            ).get_llm()
        else:
            raise ValueError(f"Invalid LLM provider: {Config.LLM_PROVIDER}")

    def get_llm(self):
        return self.llm 

        

   
