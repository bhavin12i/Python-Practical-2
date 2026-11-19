from urllib.parse import urlsplit

from pydantic import ValidationError

from app.config import settings
from app.schemas import Analysis, Brand
from app.services.competitor_service import PLATFORM_GUIDANCE, competitor_guidance
from app.services.llm_service import LLMService, LLMServiceError
from app.services.website_extractor import ExtractedWebsite

SYSTEM_PROMPT = (
    "You analyse business websites. Base your answer on the page text you are given and on general "
    "market knowledge that you clearly label as a suggestion. Return one JSON object only, with no "
    "markdown or commentary. Do not invent search volumes, rankings, market share or benchmark "
    "figures. Mark suggestions as AI-generated and facts as coming from the website."
)

RESPONSE_OUTLINE = """{
  "brand": {"name": "", "category": "", "summary": ""},
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "", "competitors": [{"name": "", "main_service": "",
      "target_market": "", "key_strength": "", "weakness_or_gap": "", "source": ""}],
      "strengths": [], "opportunities": [], "brand_name": "", "business_overview": "",
      "main_category": "", "products_and_services": [], "competitor_weaknesses": [],
      "competitive_advantages": [], "comparison": [{"field": "", "your_brand": "",
      "competitor": ""}], "evidence_note": ""
    },
    "target_search_queries": [{"query": "", "platforms": [], "intent": "",
      "business_relevance": "", "target_audience": "", "keyword_source": "AI-generated suggestion",
      "measured_search_volume": null}],
    "seo_improvements": {"primary_keyword": "", "secondary_keywords": [],
      "recommended_title": "", "meta_description": "", "supporting_content": [],
      "long_tail_keywords": [], "relevant_business_keywords": [],
      "recommended_title_structure": "", "keyword_data_source": "AI-generated suggestion",
      "measured_search_volume": null},
    "top_services": [{"service_name": "", "description": "", "target_industry": "",
      "target_customer": "", "main_benefit": "", "source": ""}],
    "target_audience": {"primary_audience": [], "secondary_audience": [], "industries": [],
      "customer_needs": [], "business_types": [], "customer_profiles": [],
      "location_focus": "", "customer_interests": [], "recommended_marketing_segments": []}
  }
}"""


class AnalysisServiceError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def build_user_prompt(extracted: ExtractedWebsite) -> str:
    content = extracted.prompt_content(settings.website_max_content_chars)
    parts = [
        "Website content:\n" + content,
        competitor_guidance(extracted),
        PLATFORM_GUIDANCE,
        "Give exactly five search queries and between one and five top services. Use 'extracted "
        "from website' for a service only when the page describes it directly; otherwise use "
        "'AI-generated inference'. Keywords are suggestions, so leave every measured_search_volume "
        "null. Include primary, secondary, long-tail and business keywords, supporting content "
        "ideas, audiences, industries and customer needs.",
        "Return JSON with these keys:\n" + RESPONSE_OUTLINE,
    ]
    return "\n\n".join(parts)


def _fallback_brand(extracted: ExtractedWebsite) -> dict:
    domain = urlsplit(extracted.final_url).netloc
    return {
        "name": extracted.title or domain,
        "category": "Not stated on website",
        "summary": extracted.meta_description or "No descriptive summary was found on the website.",
    }


async def analyze_website(extracted: ExtractedWebsite):
    service = LLMService()
    user_prompt = build_user_prompt(extracted)
    last_error = ""

    for attempt in range(2):
        prompt = user_prompt
        if last_error:
            prompt += "\n\nThe last response failed validation: " + last_error + ". Return valid JSON only."

        try:
            result = await service.generate_json(SYSTEM_PROMPT, prompt)
        except LLMServiceError as exc:
            raise AnalysisServiceError(str(exc), exc.status_code) from exc

        payload = result.payload
        try:
            analysis = Analysis.model_validate(payload.get("analysis", payload))
            brand = Brand.model_validate(payload.get("brand") or _fallback_brand(extracted))
            return analysis, brand, result
        except ValidationError as exc:
            last_error = str(exc)[:600]
            if attempt == 1:
                raise AnalysisServiceError("Analysis output failed validation: " + last_error) from exc

    raise AnalysisServiceError("Analysis output could not be validated")
