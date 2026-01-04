## Background

A PR was created targeting `main` instead of the configured branch (e.g., `source-clean-up`), even though the workflow explicitly set `base_branch: 'source-clean-up'`. The base branch had to be manually changed before merging.

**Root Cause**: There are two confusingly similar input parameters in `action.yml`:
- `default_base_branch` (line 30): "Default base branch if not specified in project config or event context"
- `base_branch` (line 45): "Base branch where spec files must exist and where pull requests will target"

The `parse-event` step (line 127) only receives `inputs.default_base_branch`, not `inputs.base_branch`. So when a user sets `base_branch: 'source-clean-up'`:

1. `inputs.base_branch` = `'source-clean-up'`
2. `inputs.default_base_branch` = `''` (not set by user)
3. Parse-event gets `DEFAULT_BASE_BRANCH=''` → falls back to `"main"`
4. Parse-event calls `context.get_default_base_branch()` which returns `ref_name` (the branch workflow was triggered from = `main`)
5. Parse-event outputs `base_branch: "main"`
6. Subsequent steps use `steps.parse.outputs.base_branch` (`main`) instead of falling back to `inputs.base_branch`

The two inputs appear to serve the same purpose and should be consolidated.

## Phases

- [x] Phase 1: Consolidate input parameters

Remove `base_branch` input and use only `default_base_branch` throughout:

1. **action.yml changes**:
   - Remove `base_branch` input (lines 45-48)
   - Update line 79-81 output to reference `default_base_branch`:
     ```yaml
     base_branch:
       description: 'Resolved base branch'
       value: ${{ steps.parse.outputs.base_branch || inputs.default_base_branch }}
     ```
   - Update line 162 (prepare step): `BASE_BRANCH: ${{ steps.parse.outputs.base_branch || inputs.default_base_branch }}`
   - Update line 224 (finalize step): `BASE_BRANCH: ${{ steps.parse.outputs.base_branch || inputs.default_base_branch }}`
   - Line 127 already correctly uses `inputs.default_base_branch`

2. **parse_event.py changes**:
   - Update the logic: if `default_base_branch` is explicitly provided, use it directly instead of trying to derive from event context

- [x] Phase 2: Fix parse-event logic for workflow_dispatch

The `get_default_base_branch()` method returns `get_checkout_ref()` for all event types, which for `workflow_dispatch` returns the branch the workflow was triggered from (often `main`), not the configured base branch.

**Changes to parse_event.py**:
```python
# Current logic (buggy):
try:
    base_branch = context.get_default_base_branch()
except ValueError:
    base_branch = default_base_branch

# Fixed logic:
# If default_base_branch was explicitly provided, use it
if default_base_branch:
    base_branch = default_base_branch
else:
    # Only derive from event context if not explicitly set
    try:
        base_branch = context.get_default_base_branch()
    except ValueError:
        base_branch = "main"  # Ultimate fallback
```

- [x] Phase 3: Update documentation

Update `docs/feature-guides/setup.md` and `README.md` if they reference `base_branch` to use `default_base_branch` instead.

- [x] Phase 4: Validation

1. Run unit tests: `pytest tests/unit/ -v`
2. Run integration tests: `pytest tests/integration/ -v`
3. Specifically verify tests in:
   - `tests/unit/domain/test_github_event.py`
   - `tests/integration/cli/commands/test_parse_event.py`
4. Add test case for `workflow_dispatch` with explicit `default_base_branch` to ensure it's respected
