# Website Link Analysis API

A FastAPI service that fetches a public website, extracts readable content, sends it to a real LLM provider, and returns structured competitor, search-query, SEO, service and target-audience analysis.

## 1. Project overview

The service implements the assignment at https://github.com/chivoxai/practical-test/blob/main/link-analysis.md.

- Single endpoint: `POST /link-analysis`
- Port: `4000`
- Local Swagger docs: http://localhost:4000/docs
- Health check: `GET /health`
- Five analysis sections: competitor comparison, five target search queries, SEO improvements, top five services, target audience.
- Real extraction via `httpx` + `BeautifulSoup`; real LLM calls via OpenAI, Gemini or Anthropic REST APIs.
- Social/JS-heavy pages (Instagram, Facebook, YouTube, X, LinkedIn, etc.) are supported by recovering Open Graph, Twitter card, JSON-LD and meta-tag content; `metadata.extraction.content_source` reports whether the prompt used `page_text`, `page_text+metadata` or `page_metadata`.
- Pages that block crawlers and expose no readable text return a structured 422 error instead of a generic analysis.
- Structured JSON validated with Pydantic; no invented search volumes.

Live Gemini analysis has been verified for the Instagram link from the review along with Facebook, X, YouTube, LinkedIn and `example.com`. See [docs/verification.md](docs/verification.md) for the full list and [docs/evidence/social-live-analysis.txt](docs/evidence/social-live-analysis.txt) for the raw response.

## 2. Installation and execution

Python 3.9+ is required.

```bash
git clone https://github.com/bhavin12i/Python-Practical-2.git
cd Python-Practical-2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set one provider key in `.env`:

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your-real-key
```

Alternatives:

```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
GEMINI_API_KEY=your-real-key
```

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=your-real-key
```

Run the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

## 3. API endpoint and request example

```bash
curl -X POST http://localhost:4000/link-analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Health check:

```bash
curl http://localhost:4000/health
```

Social profile links work with the same request:

```bash
curl -X POST http://localhost:4000/link-analysis \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/crestspot"}'
```

Error responses are structured as:

```json
{
  "success": false,
  "error": {
    "code": "invalid_url",
    "message": "URL must start with http:// or https://"
  }
}
```

A page that returns no readable content (for example, a crawler-blocked social page) returns HTTP 422 with `code: website_fetch_failed` and a message explaining that the site may require JavaScript or block automated requests.

## 4. Sample structured JSON response

The following shape matches the required example structure. The values shown are illustrative; a real response depends on the submitted URL and LLM provider (a live Gemini response is recorded in `docs/evidence/live-analysis.txt`).

```json
{
  "success": true,
  "website": "https://example.com",
  "brand": {
    "name": "ABC Technologies",
    "category": "Technology Services",
    "summary": "A technology company providing digital solutions."
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "ABC Technologies offers web development and digital consulting services.",
      "competitors": [
        {
          "name": "XYZ Technologies",
          "main_service": "Web Development",
          "target_market": "Enterprise",
          "key_strength": "Established brand",
          "weakness_or_gap": "Slow delivery",
          "source": "AI-generated suggestion"
        },
        {
          "name": "Example Digital",
          "main_service": "Digital Consulting",
          "target_market": "SMB",
          "key_strength": "Flexible pricing",
          "weakness_or_gap": "Limited case studies",
          "source": "AI-generated suggestion"
        },
        {
          "name": "Sample Web Studio",
          "main_service": "Website Design",
          "target_market": "Startups",
          "key_strength": "Design portfolio",
          "weakness_or_gap": "Narrow service range",
          "source": "AI-generated suggestion"
        }
      ],
      "strengths": ["Affordable solutions", "Broad service coverage"],
      "opportunities": ["Improve online visibility", "Add industry landing pages"],
      "brand_name": "ABC Technologies",
      "business_overview": "Digital solutions provider.",
      "main_category": "Technology Services",
      "products_and_services": ["Web development", "Digital consulting"],
      "competitor_weaknesses": ["Slow delivery", "Limited case studies"],
      "competitive_advantages": ["Affordable solutions"],
      "comparison": [
        {
          "field": "Target Market",
          "your_brand": "Small Businesses",
          "competitor": "Enterprise"
        }
      ],
      "evidence_note": "Competitors are AI-generated suggestions unless supported by observed website links."
    },
    "target_search_queries": [
      {
        "query": "best web development company",
        "platforms": ["Google"],
        "intent": "Service Search",
        "business_relevance": "Matches the main web development service",
        "target_audience": "Small business owners",
        "keyword_source": "AI-generated suggestion",
        "measured_search_volume": null
      },
      {
        "query": "website development services",
        "platforms": ["Facebook"],
        "intent": "Business Discovery",
        "business_relevance": "Matches the service catalogue",
        "target_audience": "Local business owners",
        "keyword_source": "AI-generated suggestion",
        "measured_search_volume": null
      },
      {
        "query": "website design ideas",
        "platforms": ["Instagram"],
        "intent": "Inspiration",
        "business_relevance": "Showcases design capability",
        "target_audience": "Brand managers",
        "keyword_source": "AI-generated suggestion",
        "measured_search_volume": null
      },
      {
        "query": "web development company for startups",
        "platforms": ["LinkedIn"],
        "intent": "B2B Search",
        "business_relevance": "Matches B2B development work",
        "target_audience": "Startup founders",
        "keyword_source": "AI-generated suggestion",
        "measured_search_volume": null
      },
      {
        "query": "affordable web development services",
        "platforms": ["X"],
        "intent": "Service Discovery",
        "business_relevance": "Matches value-focused buyers",
        "target_audience": "Small business owners",
        "keyword_source": "AI-generated suggestion",
        "measured_search_volume": null
      }
    ],
    "seo_improvements": {
      "primary_keyword": "web development company",
      "secondary_keywords": ["website design services", "digital consulting"],
      "recommended_title": "Web Development Company | Digital Solutions",
      "meta_description": "Web development and digital consulting for growing businesses.",
      "supporting_content": ["Service landing pages", "FAQ page", "Industry-specific pages", "Blog topics"],
      "long_tail_keywords": ["affordable web development services for small businesses"],
      "relevant_business_keywords": ["custom software", "website redesign"],
      "recommended_title_structure": "Primary keyword | Value proposition",
      "keyword_data_source": "AI-generated suggestion",
      "measured_search_volume": null
    },
    "top_services": [
      {
        "service_name": "Web development",
        "description": "Custom websites and web applications.",
        "target_industry": "Technology",
        "target_customer": "Small businesses",
        "main_benefit": "Stronger online presence",
        "source": "extracted from website"
      },
      {
        "service_name": "Website design",
        "description": "Responsive UI design.",
        "target_industry": "Retail",
        "target_customer": "Startups",
        "main_benefit": "Better user experience",
        "source": "extracted from website"
      },
      {
        "service_name": "Digital consulting",
        "description": "Technology strategy support.",
        "target_industry": "Professional services",
        "target_customer": "Business owners",
        "main_benefit": "Clearer technology decisions",
        "source": "extracted from website"
      },
      {
        "service_name": "SEO services",
        "description": "Organic search improvement.",
        "target_industry": "Local services",
        "target_customer": "Growth teams",
        "main_benefit": "More qualified traffic",
        "source": "AI-generated inference"
      },
      {
        "service_name": "Maintenance",
        "description": "Ongoing website support.",
        "target_industry": "Technology",
        "target_customer": "Existing website owners",
        "main_benefit": "Reduced downtime",
        "source": "AI-generated inference"
      }
    ],
    "target_audience": {
      "primary_audience": ["Small businesses", "Startups"],
      "secondary_audience": ["Enterprise companies", "Professional services"],
      "industries": ["Technology", "Retail", "Professional services"],
      "customer_needs": ["Website development", "Online visibility", "Digital solutions"],
      "business_types": ["SMB", "Startup", "Enterprise"],
      "customer_profiles": ["Founder", "Marketing manager", "Operations lead"],
      "location_focus": "Not stated on website",
      "customer_interests": ["Growth", "Automation", "Brand visibility"],
      "recommended_marketing_segments": ["Local service businesses", "Early-stage startups"]
    }
  },
  "metadata": {
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "keyword_data_source": "AI-generated keyword suggestions; no measured search volume was used",
    "competitor_data_source": "AI-generated suggestions from extracted website content",
    "input_tokens": 5000,
    "output_tokens": 1600,
    "estimated_cost_usd": 0.0017,
    "extraction": {
      "status_code": 200,
      "word_count": 420
    },
    "cache_hit": false,
    "duration_ms": 6200
  }
}
```

## 5. The five analysis sections

1. **Competitor vs your brand details** — brand overview, inferred competitors (minimum three where reliable information is available), strengths, weaknesses, advantages, comparison table, opportunities.
2. **Top five target search queries** — exactly five queries covering Google, Facebook, Instagram, LinkedIn and X, each with intent, business relevance, target audience and an explicit `AI-generated suggestion` source.
3. **SEO improvement** — primary, secondary, long-tail and business keywords, recommended title, meta description and supporting content ideas. No search volume is invented.
4. **Top five services** — service name, description, industry, customer and benefit, with each item labelled `extracted from website` or `AI-generated inference`.
5. **Target audience identification** — primary and secondary audiences, industries, business types, profiles, location focus, customer needs and recommended segments.

## 6. LLM comparison summary

Full research: [docs/llm-comparison.md](docs/llm-comparison.md).

- **Recommended provider:** OpenAI
- **Recommended model:** `gpt-4o-mini`
- **Tokens observed in live runs:** 770–4,326 input and 1,895–2,277 output per analysis
- **Estimated cost:** ~$0.0014 for a 1,000 input / 2,000 output analysis at $0.15/M input and $0.60/M output
- **Response time:** 6.1 s measured for the live Instagram request; no cross-provider benchmark was run
- **Reason for selection:** cheap, widely available, reliable JSON mode and reported token usage for costing.
- **Alternative model:** Google `gemini-3.5-flash-lite` (native JSON MIME response and a free development tier) or Anthropic `claude-haiku-4-5-20251001`.
- Live verification used Gemini; `LLM_MAX_OUTPUT_TOKENS` is 8,192 so the full JSON response is not truncated.
- **Cost optimization:** HTML cleaning, token caps, one LLM call for all sections, local Pydantic validation, one retry maximum, and a one-hour response cache.

Pricing comes from provider documentation; response times are from local runs rather than a formal benchmark.

## 7. Security considerations

- URL scheme restricted to HTTP/HTTPS; credentials in URLs rejected.
- DNS resolution and every redirect target checked against private, loopback, link-local, reserved, multicast and metadata addresses to reduce SSRF risk.
- Only ports 80 and 443 allowed; redirect chain limited to five hops.
- Download size capped at 1.5 MB; page text capped before LLM submission.
- API keys read only from environment variables; `.env` is gitignored; `.env.example` contains no real credentials.
- Error messages from the LLM provider are truncated and never include keys.
- Pydantic schemas with `extra="forbid"` on requests and strict response validation.
- No credentials are committed, and the response schema rejects invented search volumes.

## 8. Testing instructions

```bash
pip install -r requirements.txt
python -m pytest -q
```

The 16 tests cover health/docs/OpenAPI, response fields, five queries and services, all five platform mappings, no invented search volumes, invalid and SSRF URLs, social metadata extraction, status-before-content-type handling, Gemini response parsing, malformed-JSON retries and each provider adapter with a mocked HTTP transport. Output is in [docs/evidence/test-output.txt](docs/evidence/test-output.txt).

Manual local verification:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
curl http://localhost:4000/health
curl -X POST http://localhost:4000/link-analysis -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'
```

With a valid API key this returns a real LLM analysis. Without a key it returns HTTP 503 with error code `analysis_failed` and a message saying no API key is configured, which is the expected graceful failure.

## 9. Deployment and live demo

| Requirement | URL |
|---|---|
| Live application | `[TO BE PROVIDED AFTER DEPLOYMENT]` |
| API endpoint | `[TO BE PROVIDED AFTER DEPLOYMENT]/link-analysis` |
| Swagger documentation | `[TO BE PROVIDED AFTER DEPLOYMENT]/docs` |
| Health check | `[TO BE PROVIDED AFTER DEPLOYMENT]/health` |

Deployment is manual. Use `render.yaml` or the `Dockerfile`, set the provider key in the hosting dashboard, then replace the URLs above with the deployed ones.

## 10. Evidence

- Swagger UI: `docs/evidence/swagger-ui.png`
- Mock-provider response: `docs/evidence/api-request-response.txt`
- Live responses: `docs/evidence/live-analysis.txt`, `docs/evidence/social-live-analysis.txt`
- Health check: `docs/evidence/health-check.txt`
- Test output: `docs/evidence/test-output.txt`

See [docs/evidence/README.md](docs/evidence/README.md) for details.

## 11. Recruitment verification (applicant action required)

The following must be completed personally by the applicant and are **not** claimed as completed here:

- [ ] Follow Dxora Technologies on LinkedIn: https://www.linkedin.com/company/dxora-technologies
- [ ] Follow CREST on Instagram: https://www.instagram.com/crestspot/
- Applicant LinkedIn profile URL: `[APPLICANT LINKEDIN PROFILE URL]`
- Applicant Instagram profile URL: `[APPLICANT INSTAGRAM PROFILE URL]`

## 12. Submission email

Send the email to `hr@chivoxai.com` with the applicant details listed in section 11 and the public repository URL. No email template file is kept in this repository.

## 13. Evaluation weightage (unchanged)

| Criterion | Marks |
|---|---:|
| FastAPI implementation and API structure | 10 |
| Website extraction and content understanding | 15 |
| LLM integration and structured output | 15 |
| Competitor and search query analysis | 15 |
| SEO recommendations and keyword intelligence | 10 |
| Services and target audience identification | 10 |
| LLM model research and cost optimization | 15 |
| Error handling, code quality and documentation | 10 |
| **Total** | **100** |
