import asyncio
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import settings
from app.schemas import AnalysisMetadata, AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisServiceError, analyze_website
from app.services.website_extractor import WebsiteFetchError, extract_website
from app.utils.validators import UnsafeUrlError, UrlValidationError

app = FastAPI(
    title="Website Link Analysis API",
    description="Extracts a public website and returns competitor, search query, SEO, service and audience analysis.",
    version="1.0.0",
)

_response_cache = {}
_cache_lock = asyncio.Lock()
_CACHE_MAX_ENTRIES = 128


def error_response(status_code, code, message):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": {"code": code, "message": message}},
    )


@app.exception_handler(UrlValidationError)
async def invalid_url_handler(request: Request, exc: UrlValidationError):
    return error_response(400, "invalid_url", str(exc))


@app.exception_handler(UnsafeUrlError)
async def unsafe_url_handler(request: Request, exc: UnsafeUrlError):
    return error_response(403, "unsafe_url", str(exc))


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return error_response(422, "invalid_request", "Request body must contain a valid website URL")


@app.exception_handler(WebsiteFetchError)
async def website_fetch_handler(request: Request, exc: WebsiteFetchError):
    return error_response(exc.status_code, "website_fetch_failed", str(exc))


@app.exception_handler(AnalysisServiceError)
async def analysis_handler(request: Request, exc: AnalysisServiceError):
    return error_response(exc.status_code, "analysis_failed", str(exc))


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return error_response(502, "invalid_analysis_output", "Analysis output failed validation")


@app.exception_handler(Exception)
async def unexpected_handler(request: Request, exc: Exception):
    return error_response(500, "internal_error", "An unexpected server error occurred")


@app.get("/")
async def root():
    return {
        "service": "Website Link Analysis API",
        "docs": "/docs",
        "health": "/health",
        "endpoint": "POST /link-analysis",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_provider": settings.llm_provider,
        "llm_model": settings.resolved_model(),
        "llm_api_key_configured": bool(settings.api_key()),
        "version": app.version,
    }


@app.post("/link-analysis", response_model=AnalysisResponse)
async def link_analysis(request: AnalysisRequest):
    started = time.perf_counter()
    url = request.url.strip()
    cache_key = (url, settings.llm_provider, settings.resolved_model())

    async with _cache_lock:
        cached = _response_cache.get(cache_key)
        if cached and time.time() - cached[0] < settings.cache_ttl_seconds:
            response = cached[1].model_copy(deep=True)
            response.metadata.cache_hit = True
            response.metadata.duration_ms = int((time.perf_counter() - started) * 1000)
            return response

    extracted = await extract_website(url)
    analysis, brand, llm_result = await analyze_website(extracted)

    model = settings.resolved_model()
    metadata = AnalysisMetadata(
        llm_provider=settings.llm_provider,
        llm_model=model,
        input_tokens=llm_result.input_tokens,
        output_tokens=llm_result.output_tokens,
        estimated_cost_usd=llm_result.estimated_cost_usd(model),
        extraction=extracted.as_dict(),
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    response = AnalysisResponse(
        success=True,
        website=url,
        brand=brand,
        analysis=analysis,
        metadata=metadata,
    )

    async with _cache_lock:
        if len(_response_cache) >= _CACHE_MAX_ENTRIES:
            oldest = min(_response_cache, key=lambda key: _response_cache[key][0])
            _response_cache.pop(oldest, None)
        _response_cache[cache_key] = (time.time(), response)
    return response
