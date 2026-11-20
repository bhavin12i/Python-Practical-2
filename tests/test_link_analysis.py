import pytest
from httpx import ASGITransport, AsyncClient, MockTransport, Request, Response

from app.config import settings
from app.main import _response_cache, app
from app.schemas import Analysis, Brand
from app.services.llm_service import LLMResult, LLMService
from app.services.website_extractor import ExtractedWebsite, WebsiteFetchError, extract_website

SAMPLE_PAYLOAD = {
    "brand": {
        "name": "Acme Digital",
        "category": "Digital marketing services",
        "summary": "A digital agency offering SEO, web design and paid advertising.",
    },
    "analysis": {
        "competitor_analysis": {
            "brand_overview": "Acme Digital provides SEO, web design and advertising services.",
            "competitors": [
                {
                    "name": "Rival Media",
                    "main_service": "SEO",
                    "target_market": "Small businesses",
                    "key_strength": "Established brand",
                    "weakness_or_gap": "Limited local pages",
                    "source": "AI-generated suggestion",
                },
                {
                    "name": "Bright Web",
                    "main_service": "Web design",
                    "target_market": "Startups",
                    "key_strength": "Design portfolio",
                    "weakness_or_gap": "Few case studies",
                    "source": "AI-generated suggestion",
                },
                {
                    "name": "Growth Labs",
                    "main_service": "Paid advertising",
                    "target_market": "E-commerce",
                    "key_strength": "Large ad budget",
                    "weakness_or_gap": "Slow support",
                    "source": "AI-generated suggestion",
                },
            ],
            "strengths": ["Integrated SEO and design", "Local market focus"],
            "opportunities": ["Build industry landing pages", "Publish case studies"],
            "brand_name": "Acme Digital",
            "business_overview": "Digital marketing services for growing businesses.",
            "main_category": "Digital marketing",
            "products_and_services": ["SEO", "Web design", "Paid advertising"],
            "competitor_weaknesses": ["Limited local pages", "Few case studies"],
            "competitive_advantages": ["Bundled services"],
            "comparison": [{"field": "Main service", "your_brand": "SEO", "competitor": "SEO"}],
            "evidence_note": "Competitors are AI-generated suggestions from extracted content.",
        },
        "target_search_queries": [
            {
                "query": "best digital marketing agency",
                "platforms": ["Google"],
                "intent": "Service Search",
                "business_relevance": "Matches core SEO offering",
                "target_audience": "Small business owners",
            },
            {
                "query": "website design services for local businesses",
                "platforms": ["Facebook"],
                "intent": "Business Discovery",
                "business_relevance": "Matches web design service",
                "target_audience": "Local business owners",
            },
            {
                "query": "modern website design ideas",
                "platforms": ["Instagram"],
                "intent": "Inspiration",
                "business_relevance": "Showcases design capability",
                "target_audience": "Brand managers",
            },
            {
                "query": "SEO agency for B2B startups",
                "platforms": ["LinkedIn"],
                "intent": "B2B Search",
                "business_relevance": "Matches SEO offering",
                "target_audience": "Startup founders",
            },
            {
                "query": "affordable SEO services",
                "platforms": ["X (Twitter)"],
                "intent": "Service Discovery",
                "business_relevance": "Matches pricing-sensitive buyers",
                "target_audience": "Small business owners",
            },
        ],
        "seo_improvements": {
            "primary_keyword": "digital marketing agency",
            "secondary_keywords": ["SEO services", "web design services"],
            "recommended_title": "Digital Marketing Agency | SEO and Web Design",
            "meta_description": "SEO, web design and paid advertising for growing businesses.",
            "supporting_content": ["Service landing pages", "FAQ page", "Industry-specific pages"],
            "long_tail_keywords": ["affordable SEO services for small businesses"],
            "relevant_business_keywords": ["paid advertising", "local SEO"],
            "recommended_title_structure": "Primary keyword | Secondary keyword",
            "keyword_data_source": "AI-generated suggestion",
            "measured_search_volume": None,
        },
        "top_services": [
            {
                "service_name": "SEO",
                "description": "Organic search optimisation.",
                "target_industry": "Professional services",
                "target_customer": "Small businesses",
                "main_benefit": "More qualified traffic",
                "source": "extracted from website",
            },
            {
                "service_name": "Web design",
                "description": "Responsive website design.",
                "target_industry": "Retail",
                "target_customer": "Startups",
                "main_benefit": "Better conversion rate",
                "source": "extracted from website",
            },
            {
                "service_name": "Paid advertising",
                "description": "Paid search campaigns.",
                "target_industry": "E-commerce",
                "target_customer": "Growth teams",
                "main_benefit": "Faster lead generation",
                "source": "extracted from website",
            },
            {
                "service_name": "Content marketing",
                "description": "Blog and landing page content.",
                "target_industry": "Technology",
                "target_customer": "Marketing managers",
                "main_benefit": "Higher search visibility",
                "source": "AI-generated inference",
            },
            {
                "service_name": "Analytics reporting",
                "description": "Performance dashboards.",
                "target_industry": "Professional services",
                "target_customer": "Business owners",
                "main_benefit": "Measurable ROI",
                "source": "AI-generated inference",
            },
        ],
        "target_audience": {
            "primary_audience": ["Small business owners"],
            "secondary_audience": ["Startup founders"],
            "industries": ["Retail", "Professional services"],
            "customer_needs": ["More leads", "Better online visibility"],
            "business_types": ["SMB", "Startup"],
            "customer_profiles": ["Marketing manager", "Founder"],
            "location_focus": "Not specified on website",
            "customer_interests": ["Growth", "Brand visibility"],
            "recommended_marketing_segments": ["Local service businesses"],
        },
    },
}


def sample_services():
    return (
        Analysis.model_validate(SAMPLE_PAYLOAD["analysis"]),
        Brand.model_validate(SAMPLE_PAYLOAD["brand"]),
        LLMResult(payload=SAMPLE_PAYLOAD, input_tokens=4200, output_tokens=1500),
    )


@pytest.fixture(autouse=True)
def clear_cache():
    _response_cache.clear()
    yield
    _response_cache.clear()


@pytest.mark.asyncio
async def test_health_root_and_docs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/health")
        root = await client.get("/")
        docs = await client.get("/docs")
        schema = await client.get("/openapi.json")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert root.json()["endpoint"] == "POST /link-analysis"
    assert docs.status_code == 200
    assert "/link-analysis" in schema.json()["paths"]


@pytest.mark.asyncio
async def test_link_analysis_success(monkeypatch):
    extracted = ExtractedWebsite(
        requested_url="https://example.com",
        final_url="https://example.com",
        title="Acme Digital",
        meta_description="Digital marketing services.",
        text="We provide SEO, web design and paid advertising.",
        word_count=8,
        char_count=48,
    )

    async def fake_extract(url, client=None):
        return extracted

    async def fake_analyze(website):
        return sample_services()

    monkeypatch.setattr("app.main.extract_website", fake_extract)
    monkeypatch.setattr("app.main.analyze_website", fake_analyze)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/link-analysis", json={"url": "https://example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["website"] == "https://example.com"

    analysis = body["analysis"]
    for key in ("competitor_analysis", "target_search_queries", "seo_improvements", "top_services", "target_audience"):
        assert key in analysis
    for key in ("brand_overview", "competitors", "strengths", "opportunities"):
        assert key in analysis["competitor_analysis"]
    for key in ("primary_keyword", "secondary_keywords", "recommended_title", "meta_description", "supporting_content"):
        assert key in analysis["seo_improvements"]
    for key in ("primary_audience", "secondary_audience", "industries", "customer_needs"):
        assert key in analysis["target_audience"]

    assert len(analysis["target_search_queries"]) == 5
    assert len(analysis["top_services"]) == 5
    covered = {p for query in analysis["target_search_queries"] for p in query["platforms"]}
    assert covered == {"Google", "Facebook", "Instagram", "LinkedIn", "X"}
    for query in analysis["target_search_queries"]:
        assert query["keyword_source"] == "AI-generated suggestion"
        assert query["measured_search_volume"] is None


@pytest.mark.asyncio
async def test_invalid_and_ssrf_urls_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        invalid = await client.post("/link-analysis", json={"url": "not-a-url"})
        bad_port = await client.post("/link-analysis", json={"url": "http://example.com:abc"})
        localhost = await client.post("/link-analysis", json={"url": "http://localhost"})
        loopback = await client.post("/link-analysis", json={"url": "http://127.0.0.1"})
        metadata = await client.post("/link-analysis", json={"url": "http://169.254.169.254/latest/meta-data"})

    assert invalid.status_code == 400
    assert bad_port.status_code == 400
    assert localhost.status_code == 403
    assert loopback.status_code == 403
    assert metadata.status_code == 403


def test_schema_requires_exactly_five_queries():
    payload = dict(SAMPLE_PAYLOAD["analysis"])
    payload["target_search_queries"] = payload["target_search_queries"][:4]
    with pytest.raises(ValueError, match="Exactly five"):
        Analysis.model_validate(payload)


def test_schema_requires_exactly_five_services():
    payload = dict(SAMPLE_PAYLOAD["analysis"])
    payload["top_services"] = payload["top_services"][:3]
    with pytest.raises(ValueError, match="Exactly five"):
        Analysis.model_validate(payload)


def test_schema_rejects_invented_search_volume():
    payload = dict(SAMPLE_PAYLOAD["analysis"])
    queries = [dict(query) for query in payload["target_search_queries"]]
    queries[0]["measured_search_volume"] = "5000/mo"
    payload["target_search_queries"] = queries
    with pytest.raises(ValueError, match="Measured search volumes"):
        Analysis.model_validate(payload)


def test_shared_address_space_is_blocked():
    from app.utils.validators import _is_blocked_ip

    assert _is_blocked_ip("100.100.100.200") is True
    assert _is_blocked_ip("8.8.8.8") is False


@pytest.mark.asyncio
async def test_extraction_from_real_html(monkeypatch):
    async def fake_validate(url):
        return url

    monkeypatch.setattr("app.services.website_extractor.validate_public_url", fake_validate)
    monkeypatch.setattr("app.services.website_extractor.validate_redirect_url", fake_validate)

    html = b"""
    <html><head><title>Acme Digital</title>
    <meta name="description" content="Digital marketing services"></head>
    <body><h1>SEO services</h1><p>We help local businesses grow.</p>
    <a href="https://rival.example">A competitor</a>
    <script>ignore this</script></body></html>
    """

    def handler(request: Request) -> Response:
        return Response(200, text=html.decode(), headers={"content-type": "text/html; charset=utf-8"})

    async with AsyncClient(transport=MockTransport(handler)) as client:
        result = await extract_website("https://example.com", client=client)

    assert result.title == "Acme Digital"
    assert result.meta_description == "Digital marketing services"
    assert "SEO services" in result.headings
    assert "We help local businesses grow." in result.text
    assert "ignore this" not in result.text
    assert result.external_links == ["https://rival.example"]


@pytest.mark.asyncio
async def test_extraction_recovers_social_profile_metadata(monkeypatch):
    async def fake_validate(url):
        return url

    monkeypatch.setattr("app.services.website_extractor.validate_public_url", fake_validate)
    monkeypatch.setattr("app.services.website_extractor.validate_redirect_url", fake_validate)

    html = b"""
    <html><head><title>CREST #1 (@crestspot) &bull; Instagram photos and videos</title>
    <meta property="og:site_name" content="Instagram">
    <meta property="og:type" content="profile">
    <meta property="og:title" content="CREST #1 (@crestspot)">
    <meta property="og:description" content="970 Followers, 1,177 Following, 52 Posts - CREST #1">
    <meta name="description" content="CREST #1 on Instagram: &quot;Claim Top Spot #1 Own it. Be seen.&quot;">
    <meta name="twitter:label1" content="Posts"><meta name="twitter:data1" content="52">
    <script type="application/ld+json">
      {"@context":"https://schema.org","@type":"ProfilePage","name":"CREST #1",
       "description":"Digital marketing and business promotion account."}
    </script>
    </head><body><script>window.__bootstrap = {}</script></body></html>
    """

    def handler(request: Request) -> Response:
        return Response(200, text=html.decode(), headers={"content-type": "text/html; charset=utf-8"})

    async with AsyncClient(transport=MockTransport(handler)) as client:
        result = await extract_website("https://www.instagram.com/crestspot", client=client)

    assert result.content_source == "page_metadata"
    assert result.word_count > 0
    assert result.title == "CREST #1 (@crestspot)"
    assert result.meta_description == "970 Followers, 1,177 Following, 52 Posts - CREST #1"
    assert "970 Followers" in result.text
    assert "Claim Top Spot #1" in result.text
    assert "Posts 52" in result.text
    assert "Digital marketing and business promotion account." in result.text
    assert "bootstrap" not in result.text
    assert result.as_dict()["content_source"] == "page_metadata"
    assert "Content source: page_metadata" in result.prompt_content(4000)


@pytest.mark.asyncio
async def test_extraction_keeps_unique_metadata_on_text_heavy_pages(monkeypatch):
    async def fake_validate(url):
        return url

    monkeypatch.setattr("app.services.website_extractor.validate_public_url", fake_validate)
    monkeypatch.setattr("app.services.website_extractor.validate_redirect_url", fake_validate)

    body_text = " ".join(["We provide digital marketing services for growing brands."] * 6)
    html = f"""
    <html><head><title>Acme Digital</title>
    <meta property="og:site_name" content="Acme Site">
    <meta property="og:description" content="Affordable SEO packages for local businesses.">
    </head><body><h1>SEO services</h1><p>{body_text}</p></body></html>
    """

    def handler(request: Request) -> Response:
        return Response(200, text=html, headers={"content-type": "text/html; charset=utf-8"})

    async with AsyncClient(transport=MockTransport(handler)) as client:
        result = await extract_website("https://example.com", client=client)

    assert result.content_source == "page_text+metadata"
    assert "SEO services" in result.text
    assert "Affordable SEO packages for local businesses." in result.text
    assert "Acme Site" in result.text


@pytest.mark.asyncio
async def test_extraction_of_blocked_page_reports_unavailable(monkeypatch):
    async def fake_validate(url):
        return url

    monkeypatch.setattr("app.services.website_extractor.validate_public_url", fake_validate)
    monkeypatch.setattr("app.services.website_extractor.validate_redirect_url", fake_validate)

    def handler(request: Request) -> Response:
        return Response(
            200,
            text="<html><title>Facebook</title><body></body></html>",
            headers={"content-type": "text/html; charset=utf-8"},
        )

    async with AsyncClient(transport=MockTransport(handler)) as client:
        with pytest.raises(WebsiteFetchError, match="No readable content") as exc_info:
            await extract_website("https://www.facebook.com/privatepage", client=client)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_llm_openai_structured_json_adapter(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings", settings)
    captured = {}

    def handler(request: Request) -> Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        return Response(
            200,
            json={
                "choices": [{"message": {"content": '```json\n{"brand": {"name": "Acme"}}\n```'}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            },
        )

    async with AsyncClient(transport=MockTransport(handler)) as client:
        service = LLMService(client=client)
        service.provider = "openai"
        service.model = "gpt-4o-mini"
        service.api_key = "test-key-not-real"
        result = await service.generate_json("system", "user")

    assert result.payload == {"brand": {"name": "Acme"}}
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.estimated_cost_usd("gpt-4o-mini") == pytest.approx(0.000045)


@pytest.mark.asyncio
async def test_llm_gemini_multipart_and_thought_parts(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings", settings)

    def handler(request: Request) -> Response:
        return Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {"text": "thinking", "thought": True},
                                {"text": '{"brand": {"name": "Acme"}}'},
                            ]
                        },
                    }
                ],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20},
            },
        )

    async with AsyncClient(transport=MockTransport(handler)) as client:
        service = LLMService(client=client)
        service.provider = "gemini"
        service.model = "gemini-3.5-flash-lite"
        service.api_key = "test-key-not-real"
        result = await service.generate_json("system", "user")

    assert result.payload == {"brand": {"name": "Acme"}}
    assert result.input_tokens == 10
    assert result.output_tokens == 20


@pytest.mark.asyncio
async def test_llm_gemini_truncated_response_rejected(monkeypatch):
    from app.services.llm_service import LLMBadResponseError

    monkeypatch.setattr("app.services.llm_service.settings", settings)

    def handler(request: Request) -> Response:
        return Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": '{"brand":'}]}}
                ]
            },
        )

    async with AsyncClient(transport=MockTransport(handler)) as client:
        service = LLMService(client=client)
        service.provider = "gemini"
        service.model = "gemini-3.5-flash-lite"
        service.api_key = "test-key-not-real"
        with pytest.raises(LLMBadResponseError, match="truncated"):
            await service.generate_json("system", "user")


@pytest.mark.asyncio
async def test_analysis_retries_malformed_llm_json(monkeypatch):
    from app.services.analysis_service import analyze_website
    from app.services.llm_service import LLMResult

    calls = []

    async def fake_generate_json(self, system, prompt):
        calls.append(prompt)
        if len(calls) == 1:
            from app.services.llm_service import LLMBadResponseError

            raise LLMBadResponseError("LLM response was not valid JSON")
        return LLMResult(payload=SAMPLE_PAYLOAD, input_tokens=100, output_tokens=100)

    monkeypatch.setattr(LLMService, "generate_json", fake_generate_json)

    extracted = ExtractedWebsite(
        requested_url="https://example.com",
        final_url="https://example.com",
        title="Acme Digital",
        text="We provide SEO services.",
        word_count=4,
        char_count=24,
    )
    analysis, brand, result = await analyze_website(extracted)

    assert len(calls) == 2
    assert "failed validation" in calls[1]
    assert brand.name == "Acme Digital"
    assert len(analysis.target_search_queries) == 5


@pytest.mark.asyncio
async def test_error_status_takes_priority_over_content_type(monkeypatch):
    async def fake_validate(url):
        return url

    monkeypatch.setattr("app.services.website_extractor.validate_public_url", fake_validate)
    monkeypatch.setattr("app.services.website_extractor.validate_redirect_url", fake_validate)

    def handler(request: Request) -> Response:
        return Response(
            404,
            text='{"error":"not found"}',
            headers={"content-type": "application/json"},
        )

    async with AsyncClient(transport=MockTransport(handler)) as client:
        with pytest.raises(WebsiteFetchError, match="HTTP 404"):
            await extract_website("https://example.com/missing", client=client)
