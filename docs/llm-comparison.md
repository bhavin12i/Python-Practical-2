# LLM comparison

I compared five models from three providers before choosing one for this project. The prices below are list prices in USD per one million tokens. They were checked while building the project, but you should confirm them on the provider pricing pages before relying on them for a real deployment.

| Provider | Model | Input | Output | JSON support | Notes |
|---|---|---:|---:|---|---|
| OpenAI | `gpt-4o-mini` | $0.15 | $0.60 | `response_format=json_object` | Cheap, widely available, reports token usage |
| OpenAI | `gpt-4.1-mini` | $0.40 | $1.60 | Structured JSON supported | Stronger model, costs more than the one above |
| Google | `gemini-3.5-flash-lite` | $0.30 | $2.50 | Native JSON MIME type | Free tier with no billing account; cheap paid tier |
| Google | `gemini-3.1-pro-preview` | $2.00 | $12.00 | Native JSON MIME type | Preview model, not free; higher capability |
| Anthropic | `claude-3-5-haiku` | $0.80 | $4.00 | JSON output via prompt | Fast, but output tokens are expensive |

## Chosen model

`gpt-4o-mini` on OpenAI is the default in `app/config.py`. It is not the absolute cheapest, but it combines a low price with reliable JSON mode and clear token counts, which makes cost estimates straightforward. The adapter also supports Gemini and Anthropic if their keys are configured instead.

## Cost per analysis

Each request sends roughly 5,000 input tokens and receives up to 1,600 output tokens. With `gpt-4o-mini` that works out to about $0.0017 per analysis:

- Input: 5,000 / 1,000,000 x $0.15 = $0.00075
- Output: 1,600 / 1,000,000 x $0.60 = $0.00096

The endpoint reports the actual cost in `metadata.estimated_cost_usd` when the provider returns token usage.

## Speed and measurements

No live provider key was available while building this project, so response times were not measured. The 4-18 second figure in the README is only an estimate from typical API behaviour, not a benchmark result from this repository. The same applies to all figures above: they come from published pricing, not from tests run here.

## Keeping costs down

- HTML is cleaned and page text is capped before it is sent.
- All five analysis sections are produced in one request.
- Output length is limited and validation allows at most one retry.
- Identical requests are cached for one hour.
