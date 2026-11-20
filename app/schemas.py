from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CANONICAL_PLATFORMS = ("Google", "Facebook", "Instagram", "LinkedIn", "X")

PLATFORM_ALIASES = {
    "google": "Google",
    "google search": "Google",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "x": "X",
    "twitter": "X",
    "x (twitter)": "X",
}


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=8, max_length=2048, description="Public website URL to analyze")


class Competitor(BaseModel):
    name: str
    main_service: str = ""
    target_market: str = ""
    key_strength: str = ""
    weakness_or_gap: str = ""
    source: str = "AI-generated suggestion"


class CompetitorAnalysis(BaseModel):
    brand_overview: str
    competitors: List[Competitor] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    brand_name: str = ""
    business_overview: str = ""
    main_category: str = ""
    products_and_services: List[str] = Field(default_factory=list)
    competitor_weaknesses: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)
    comparison: List[dict] = Field(default_factory=list)
    evidence_note: str = "Competitors are AI-generated suggestions unless an observed website link supports them."


def _no_measured_volume(value):
    if value is not None:
        raise ValueError("Measured search volumes must not be reported unless backed by a data source")
    return value


class TargetSearchQuery(BaseModel):
    query: str
    platforms: List[str] = Field(default_factory=list)
    intent: str
    business_relevance: str = ""
    target_audience: str = ""
    keyword_source: Literal["AI-generated suggestion"] = "AI-generated suggestion"
    measured_search_volume: Optional[str] = None

    @field_validator("platforms")
    @classmethod
    def normalize_platforms(cls, value: List[str]) -> List[str]:
        result = []
        for item in value:
            platform = PLATFORM_ALIASES.get(str(item).strip().lower())
            if platform and platform not in result:
                result.append(platform)
        return result

    @field_validator("measured_search_volume")
    @classmethod
    def no_measured_search_volume(cls, value):
        return _no_measured_volume(value)


class SeoImprovements(BaseModel):
    primary_keyword: str
    secondary_keywords: List[str] = Field(default_factory=list)
    recommended_title: str
    meta_description: str
    supporting_content: List[str] = Field(default_factory=list)
    long_tail_keywords: List[str] = Field(default_factory=list)
    relevant_business_keywords: List[str] = Field(default_factory=list)
    recommended_title_structure: str = ""
    keyword_data_source: Literal["AI-generated suggestion"] = "AI-generated suggestion"
    measured_search_volume: Optional[str] = None

    @field_validator("measured_search_volume")
    @classmethod
    def no_measured_search_volume(cls, value):
        return _no_measured_volume(value)


class Service(BaseModel):
    service_name: str
    description: str
    target_industry: str = ""
    target_customer: str = ""
    main_benefit: str = ""
    source: Literal["extracted from website", "AI-generated inference"] = "AI-generated inference"


class TargetAudience(BaseModel):
    primary_audience: List[str] = Field(default_factory=list)
    secondary_audience: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    customer_needs: List[str] = Field(default_factory=list)
    business_types: List[str] = Field(default_factory=list)
    customer_profiles: List[str] = Field(default_factory=list)
    location_focus: str = ""
    customer_interests: List[str] = Field(default_factory=list)
    recommended_marketing_segments: List[str] = Field(default_factory=list)


class Brand(BaseModel):
    name: str
    category: str
    summary: str


class Analysis(BaseModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: List[TargetSearchQuery]
    seo_improvements: SeoImprovements
    top_services: List[Service]
    target_audience: TargetAudience

    @field_validator("target_search_queries")
    @classmethod
    def exactly_five_queries(cls, value: List[TargetSearchQuery]) -> List[TargetSearchQuery]:
        if len(value) != 5:
            raise ValueError("Exactly five target search queries are required")
        return value

    @model_validator(mode="after")
    def cover_all_platforms(self):
        covered = set()
        for query in self.target_search_queries:
            covered.update(query.platforms)
        for platform in CANONICAL_PLATFORMS:
            if platform not in covered:
                raise ValueError("Queries must cover Google, Facebook, Instagram, LinkedIn and X")
        if len(self.top_services) != 5:
            raise ValueError("Exactly five top services are required")
        return self


class AnalysisMetadata(BaseModel):
    llm_provider: str
    llm_model: str
    keyword_data_source: str = "AI-generated keyword suggestions; no measured search volume was used"
    competitor_data_source: str = "AI-generated suggestions from extracted website content"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    extraction: dict = Field(default_factory=dict)
    cache_hit: bool = False
    duration_ms: Optional[int] = None


class AnalysisResponse(BaseModel):
    success: bool = True
    website: str
    brand: Brand
    analysis: Analysis
    metadata: AnalysisMetadata
