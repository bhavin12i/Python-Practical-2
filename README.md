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
- Structured JSON validated with Pydantic; no invented search volumes.

**Current verification status:** unit and mocked-integration tests pass. Live LLM analysis is **not verified** in this environment because no provider API key was supplied. See [docs/compliance-report.md](docs/compliance-report.md).

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
LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=your-real-key
```

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku
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

## 4. Sample structured JSON response

The following shape matches the required example structure. The values shown are illustrative until a live LLM call is made with a real API key.

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
- **Estimated input tokens:** ~5,000 per analysis
- **Estimated output tokens:** ~1,600 per analysis
- **Estimated cost:** ~$0.0017 per analysis at $0.15/M input and $0.60/M output
- **Expected response time:** ~4–18 s end-to-end estimate; **not measured** because no API key was available
- **Reason for selection:** cheap, widely available, reliable JSON mode and reported token usage for costing.
- **Alternative model:** Google `gemini-1.5-flash` (native JSON MIME response and a free development tier) or Anthropic `claude-3-5-haiku`.
- **Cost optimization:** HTML cleaning, token caps, one LLM call for all sections, local Pydantic validation, one retry maximum, and a one-hour response cache.

Accuracy and latency figures are estimates from documentation, not benchmark results produced in this repository.

## 7. Security considerations

- URL scheme restricted to HTTP/HTTPS; credentials in URLs rejected.
- DNS resolution and every redirect target checked against private, loopback, link-local, reserved, multicast and metadata addresses to reduce SSRF risk.
- Only ports 80 and 443 allowed; redirect chain limited to five hops.
- Download size capped at 1.5 MB; page text capped before LLM submission.
- API keys read only from environment variables; `.env` is gitignored; `.env.example` contains no real credentials.
- Error messages from the LLM provider are truncated and never include keys.
- Pydantic schemas with `extra="forbid"` on requests and strict response validation.
- No secrets, fabricated logs or invented volumes are committed.

## 8. Testing instructions

```bash
pip install -r requirements.txt
python -m pytest -q
```

The suite covers health/docs/OpenAPI, required response fields, exactly five queries, all five platform mappings, invalid and SSRF URLs, real HTML parsing with a mocked transport, and the OpenAI structured-JSON adapter with a mocked HTTP transport. Actual test output is stored in [docs/evidence/test-output.txt](docs/evidence/test-output.txt).

Manual local verification:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
curl http://localhost:4000/health
curl -X POST http://localhost:4000/link-analysis -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'
```

With a valid API key this returns a real LLM analysis. Without a key it returns HTTP 503 `llm_api_key_missing`, which is the expected graceful failure.

## 9. Deployment and live demo

| Requirement | URL |
|---|---|
| Live application | `[TO BE PROVIDED AFTER DEPLOYMENT]` |
| API endpoint | `[TO BE PROVIDED AFTER DEPLOYMENT]/link-analysis` |
| Swagger documentation | `[TO BE PROVIDED AFTER DEPLOYMENT]/docs` |
| Health check | `[TO BE PROVIDED AFTER DEPLOYMENT]/health` |

Deployment is being performed manually by the applicant; no public URL has been provided yet. Exact steps are in [docs/deployment-steps.md](docs/deployment-steps.md). Verification evidence will be recorded in `docs/evidence/deployment-verification.txt` only after real requests succeed.

## 10. Evidence

- Swagger UI screenshot: `docs/evidence/swagger-ui.png` (only added from a real browser capture)
- Successful request/response example: `docs/evidence/api-request-response.txt`
- Health check result: `docs/evidence/health-check.txt`
- Test execution output: `docs/evidence/test-output.txt`
- Deployment verification: `docs/evidence/deployment-verification.txt`

See [docs/evidence/README.md](docs/evidence/README.md) for what each file proves and its current status.

## 11. Recruitment verification (applicant action required)

The following must be completed personally by the applicant and are **not** claimed as completed here:

- [ ] Follow Dxora Technologies on LinkedIn: https://www.linkedin.com/company/dxora-technologies
- [ ] Follow CREST on Instagram: https://www.instagram.com/crestspot/
- Applicant LinkedIn profile URL: `[APPLICANT LINKEDIN PROFILE URL]`
- Applicant Instagram profile URL: `[APPLICANT INSTAGRAM PROFILE URL]`

## 12. Submission email

Template: [docs/submission-email.md](docs/submission-email.md). Fill every applicant placeholder before sending to `hr@chivoxai.com`.

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
