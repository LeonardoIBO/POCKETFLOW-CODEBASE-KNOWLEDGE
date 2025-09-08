# Roadmap: Calculate Repository Size (Token Estimator)

## Goal
Build a small preflight utility that estimates tokens required to analyze a repository using the same inputs and filtering as the documentation generator. If the estimate exceeds 200,000 tokens (configurable), warn and abort early.

## Acceptance Criteria
- Prints total estimated tokens and per-file breakdown.
- Uses the same file discovery and content normalization as the generator.
- Exits with non-zero code if total_tokens > max_context_tokens.
- Threshold configurable via flag/env; default 200,000.

## Approach (Simple)
- Reuse existing loaders: `utils/crawl_local_files.py` and `utils/crawl_github_files.py`.
- Normalize content exactly as the generator does (trim, skip binaries, respect ignores).
- Count tokens per file and aggregate.
  - Prefer model-specific tokenizers when available (e.g., tiktoken).
  - Fallback heuristic: ceil(len(text) / 4) with small overhead buffer (e.g., 3%).

## CLI (Examples)
```bash
# Local path
python main.py estimate-repo --path /path/to/repo --model gpt-4o

# GitHub URL
python main.py estimate-repo --repo https://github.com/org/repo --model claude-3-5-sonnet
```

Flags: --model, --path | --repo, --max-context-tokens, --overhead-percent, --out (optional JSON file).

## Implementation Steps
1) Token utility: `utils/token_count.py` with model-aware counting and heuristic fallback.
2) Estimator: `utils/estimate_repo_tokens.py` that
   - gathers files via existing crawlers,
   - applies generator-equivalent normalization,
   - computes per-file and total tokens, applies overhead,
   - returns a JSON-serializable dict.
3) CLI: add `estimate-repo` subcommand in `main.py`, print JSON and set exit code based on threshold.
4) Optional: preflight check in the documentation command to abort early with guidance when over limit.

## Risks / Notes
- Token counts vary by provider/model; communicate that this is an estimate.
- Keep estimator fast; do not load filtered files; stream when possible.
- Align any future generator filtering changes with the estimator to maintain parity.
