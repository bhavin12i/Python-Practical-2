PLATFORM_GUIDANCE = (
    "Give exactly five search queries. Use one or more of Google, Facebook, Instagram, LinkedIn "
    "and X for each query, and make sure all five platforms appear at least once. Include "
    "business_relevance and target_audience for every query."
)


def competitor_guidance(extracted):
    links = extracted.external_links[:10]
    observed = ", ".join(links) if links else "none observed"
    return (
        "Name at least three competitors when the page gives enough information. Use the page text "
        "and these observed external links as evidence: "
        + observed
        + ". Label any competitor you cannot verify as 'AI-generated suggestion'. Do not claim "
        "measured market share or search volume."
    )


def normalize_competitors(values):
    result = []
    for value in values:
        item = dict(value)
        if "source" not in item:
            item["source"] = "AI-generated suggestion"
        result.append(item)
    return result
