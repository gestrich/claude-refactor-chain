# Token-Based Cost Calculation

## Background

The `claude-code-action` has a bug where it calculates costs using incorrect pricing rates. Our research on PR #24 from `gestrich/swift-lambda-sample` showed that when using `claude-3-haiku-20240307`, the action calculated costs using Sonnet rates ($3/$15 per MTok) instead of Haiku 3 rates ($0.25/$1.25 per MTok), resulting in a 12x overcharge in the displayed cost.

To work around this, we will:
1. Parse token counts from Claude Code execution files (which are accurate)
2. Use hardcoded per-model pricing rates in the app
3. Calculate cost per-model using correct rates, then sum for total
4. Always display token breakdown in addition to cost

### Claude Code Execution File Structure

The execution file JSON contains:

**Top-level fields:**
- `total_cost_usd` - Total cost (INACCURATE - uses wrong rates)

**Per-model breakdown (`modelUsage`):**
```json
"modelUsage": {
  "claude-haiku-4-5-20251001": {
    "inputTokens": 4271,           // ACCURATE
    "outputTokens": 389,           // ACCURATE
    "cacheReadInputTokens": 0,     // ACCURATE
    "cacheCreationInputTokens": 12299,  // ACCURATE
    "costUSD": 0.02158975,         // INACCURATE - wrong rates
    "webSearchRequests": 0,
    "contextWindow": 200000
  },
  "claude-3-haiku-20240307": {
    "inputTokens": 15,
    "outputTokens": 426,
    "cacheReadInputTokens": 90755,
    "cacheCreationInputTokens": 30605,
    "costUSD": 0.14843025,         // INACCURATE - uses Sonnet rates
    ...
  }
}
```

**Key insight:** Token counts are accurate, cost values are not. Since multiple models may be used in a single execution, we must calculate cost per-model and sum those costs (NOT sum tokens across models).

### Pricing Formula

All Claude models follow consistent pricing multipliers:
```
model_cost = (input * rate) + (output * rate * 5) + (cache_write * rate * 1.25) + (cache_read * rate * 0.1)
total_cost = sum of all model_cost values
```

### Hardcoded Model Rates (per MTok input)

Model name patterns and their input rates:
- `claude-3-haiku` or `claude-haiku-3`: $0.25
- `claude-haiku-4` or `claude-4-haiku`: $1.00
- `claude-3-5-sonnet` or `claude-sonnet-3-5`: $3.00
- `claude-sonnet-4` or `claude-4-sonnet`: $3.00
- `claude-opus-4` or `claude-4-opus`: $15.00

Unknown models: log warning, use $3.00 as default (middle ground)

## Phases

- [x] Phase 1: Extract token data and update display format

Extend `CostBreakdown` in `src/claudestep/domain/cost_breakdown.py`:
- Add fields: `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens` (all `int`, default 0)
- Update `_extract_from_file()` to also extract tokens from `modelUsage` section (sum across all models)
- Update `format_for_github()` to show token breakdown alongside existing cost (from `total_cost_usd`)
- Update Slack formatting similarly
- Maintain backward compatibility when `modelUsage` is missing (tokens default to 0)

The domain model owns parsing logic per project architecture principles.

Add tests for:
- Token extraction from execution files with `modelUsage` section
- Updated `format_for_github()` output includes tokens
- Backward compatibility when `modelUsage` is missing

- [ ] Phase 2: Add hardcoded model pricing and per-model cost calculation

Add model pricing lookup to `ModelUsage`:
- Add `MODEL_RATES` dict mapping model name patterns to input rates (per MTok)
- Add `get_rate_for_model(model_name: str) -> float` function that matches patterns
- Add `calculate_cost() -> float` method on `ModelUsage` that uses the formula and model's rate

Update `ExecutionUsage`:
- Add `calculated_cost` property that sums `calculate_cost()` across all models
- This replaces the inaccurate `total_cost_usd` from the file

Update `CostBreakdown`:
- Use `calculated_cost` from `ExecutionUsage` instead of `total_cost_usd`
- Remove reliance on file's cost values entirely

Add tests for:
- `get_rate_for_model()` with various model name patterns
- `ModelUsage.calculate_cost()` with known rates
- `ExecutionUsage.calculated_cost` sums per-model costs correctly
- Unknown model names use default rate and log warning

- [ ] Phase 3: Validation

Run full test suite:
```bash
python3 -m pytest tests/unit/domain/test_cost_breakdown.py -v
python3 -m pytest tests/integration/cli/commands/test_post_pr_comment.py -v
```

Manual verification:
- Run workflow and verify calculated cost differs from original `total_cost_usd`
- Verify token breakdown displays correctly per model
