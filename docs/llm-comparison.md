# LLM comparison

I compared five models from three providers before choosing one for this project. The prices below are list prices in USD per one million tokens. They were checked while building the project, but you should confirm them on the provider pricing pages before relying on them for a real deployment.

| Provider | Model | Input | Output | JSON support | Notes |
|---|---|---:|---:|---|---|
| OpenAI | `gpt-4o-mini` | $0.15 | $0.60 | `response_format=json_object` | Cheap, widely available, reports token usage |
| OpenAI | `gpt-4.1-mini` | $0.40 | $1.60 | Structured JSON supported | Stronger model, costs more than the one above |
| Google | `gemini-3.5-flash-lite` | $0.30 | $2.50 | Native JSON MIME type | Free tier with no billing account; cheap paid tier |
| Google | `gemini-3.1-pro-preview` | $2.00 | $12.00 | Native JSON MIME type | Preview model, not free; higher capability |
| Anthropic | `claude-haiku-4-5-20251001` | $1.00 | $5.00 | JSON output via prompt | Active replacement for the retired Claude 3.5 Haiku; output tokens are expensive |

## Chosen model

`gpt-4o-mini` on OpenAI is the default in `app/config.py`. It is not the absolute cheapest, but it combines a low price with reliable JSON mode and clear token counts, which makes cost estimates straightforward. The adapter also supports Gemini and Anthropic if their keys are configured instead.

## Cost per analysis

Live runs recorded 770-4,326 input tokens (depending on page length) and 1,895-2,277 output tokens for the full five-section response. `LLM_MAX_OUTPUT_TOKENS` defaults to 8,192 so Gemini does not truncate the JSON. With `gpt-4o-mini`, a typical 1,000 input / 2,000 output token analysis costs about $0.0014:

- Input: 1,000 / 1,000,000 x $0.15 = $0.00015
- Output: 2,000 / 1,000,000 x $0.60 = $0.00120

The endpoint reports the actual cost in `metadata.estimated_cost_usd` when the provider returns token usage.

## Speed and measurements

Live Gemini runs with a real key verified the response shape for the reviewer's Instagram link and other social URLs (`docs/evidence/social-live-analysis.txt`); that key is not stored in the repository. Measured end-to-end latency was 6.1 seconds for the Instagram request. Response times were not benchmarked across providers, so no cross-provider speed claim is made here. All pricing figures above come from published provider pricing pages.

## Keeping costs down

- HTML is cleaned and page text is capped before it is sent.
- All five analysis sections are produced in one request.
- Output length is limited and validation allows at most one retry.
- Identical requests are cached for one hour.
