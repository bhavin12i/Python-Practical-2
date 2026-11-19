import json
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import settings

PRICING_PER_MILLION = {
    "gpt-4o-mini": (0.15, 0.60),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "claude-3-5-haiku": (0.80, 4.00),
}


class LLMServiceError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class LLMResult:
    payload: dict
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    def estimated_cost_usd(self, model):
        prices = PRICING_PER_MILLION.get(model)
        if not prices or self.input_tokens is None or self.output_tokens is None:
            return None
        cost = (self.input_tokens / 1000000) * prices[0] + (self.output_tokens / 1000000) * prices[1]
        return round(cost, 8)


def _extract_json(text):
    if not text:
        raise LLMServiceError("LLM returned an empty response")

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise LLMServiceError("LLM response did not contain a JSON object")

    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMServiceError("LLM response was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise LLMServiceError("LLM response was not a JSON object")
    return payload


def _request_error(response):
    message = None
    try:
        body = response.json()
        if isinstance(body.get("error"), dict):
            message = body["error"].get("message") or body["error"].get("type")
        if not message:
            message = body.get("message")
    except (ValueError, AttributeError):
        pass

    text = "LLM provider returned HTTP " + str(response.status_code)
    if message:
        text += ": " + str(message)[:200]
    return text


class LLMService:
    def __init__(self, client=None):
        self.provider = settings.llm_provider
        self.model = settings.resolved_model()
        self.api_key = settings.api_key()
        self.client = client

    def _endpoint(self):
        if self.provider == "openai":
            return settings.openai_api_base + "/chat/completions"
        if self.provider == "gemini":
            return (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                + self.model
                + ":generateContent"
            )
        if self.provider == "anthropic":
            return "https://api.anthropic.com/v1/messages"
        raise LLMServiceError("Unsupported LLM provider: " + str(self.provider), 500)

    def _headers(self):
        if self.provider == "openai":
            return {
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
            }
        if self.provider == "gemini":
            return {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _body(self, system_prompt, user_prompt, force_json):
        if self.provider == "openai":
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_completion_tokens": settings.llm_max_output_tokens,
            }
            if force_json:
                body["response_format"] = {"type": "json_object"}
            return body

        if self.provider == "gemini":
            return {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.2,
                    "maxOutputTokens": settings.llm_max_output_tokens,
                },
            }

        messages = [{"role": "user", "content": user_prompt}]
        if force_json:
            messages.append({"role": "assistant", "content": "{"})
        return {
            "model": self.model,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": settings.llm_max_output_tokens,
        }

    def _parse_response(self, data, prefilled):
        if self.provider == "openai":
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return LLMResult(
                _extract_json(text),
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
            )

        if self.provider == "gemini":
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            return LLMResult(
                _extract_json(text),
                usage.get("promptTokenCount"),
                usage.get("candidatesTokenCount"),
            )

        text = data["content"][0]["text"]
        if prefilled:
            text = "{" + text
        usage = data.get("usage", {})
        return LLMResult(_extract_json(text), usage.get("input_tokens"), usage.get("output_tokens"))

    async def generate_json(self, system_prompt, user_prompt):
        if not self.api_key:
            raise LLMServiceError(
                "No API key configured for provider '" + str(self.provider) + "'.",
                503,
            )

        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=settings.llm_timeout_seconds)
        last_error = None

        try:
            for attempt in range(2):
                force_json = attempt == 0
                try:
                    response = await client.post(
                        self._endpoint(),
                        headers=self._headers(),
                        json=self._body(system_prompt, user_prompt, force_json),
                    )
                    if response.status_code >= 400:
                        message = _request_error(response)
                        if response.status_code == 400 and force_json:
                            last_error = message
                            continue
                        raise LLMServiceError(message)

                    data = response.json()
                    prefilled = self.provider == "anthropic" and force_json
                    return self._parse_response(data, prefilled)
                except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                    last_error = "LLM provider request failed or timed out"
                    if attempt == 1:
                        raise LLMServiceError(last_error) from exc
                except (KeyError, IndexError, TypeError) as exc:
                    raise LLMServiceError("LLM provider returned an unexpected response shape") from exc

            raise LLMServiceError(last_error or "LLM provider request failed")
        finally:
            if owns_client:
                await client.aclose()
