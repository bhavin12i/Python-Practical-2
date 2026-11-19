import os

from dotenv import load_dotenv

load_dotenv()


def env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class Settings:
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        self.llm_model = os.getenv("LLM_MODEL", "").strip()

        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").strip().rstrip("/")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

        self.llm_timeout_seconds = env_int("LLM_TIMEOUT_SECONDS", 45)
        self.llm_max_output_tokens = env_int("LLM_MAX_OUTPUT_TOKENS", 1800)
        self.website_timeout_seconds = env_int("WEBSITE_TIMEOUT_SECONDS", 12)
        self.website_max_bytes = env_int("WEBSITE_MAX_BYTES", 1500000)
        self.website_max_content_chars = env_int("WEBSITE_MAX_CONTENT_CHARS", 14000)
        self.cache_ttl_seconds = env_int("CACHE_TTL_SECONDS", 3600)

    def api_key(self):
        if self.llm_provider == "openai":
            return self.openai_api_key
        if self.llm_provider == "gemini":
            return self.gemini_api_key
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return ""

    def resolved_model(self):
        if self.llm_model:
            return self.llm_model
        defaults = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-3.5-flash-lite",
            "anthropic": "claude-3-5-haiku",
        }
        return defaults.get(self.llm_provider, "gpt-4o-mini")


settings = Settings()
