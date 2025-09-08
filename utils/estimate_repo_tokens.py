import json
import os
from typing import Dict, Any, Optional, Tuple

from utils.crawl_local_files import crawl_local_files
from utils.crawl_github_files import crawl_github_files
from utils.token_count import count_tokens


def _gather_files(source_path: Optional[str], repo_url: Optional[str], include_patterns, exclude_patterns, max_file_size: int, github_token: Optional[str]) -> Dict[str, str]:
    if source_path:
        result = crawl_local_files(
            source_path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_file_size=max_file_size,
            use_relative_paths=True,
        )
        return result.get("files", {})

    if repo_url:
        result = crawl_github_files(
            repo_url,
            token=github_token,
            max_file_size=max_file_size,
            use_relative_paths=True,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        return result.get("files", {})

    raise ValueError("Either source_path or repo_url must be provided.")


def estimate_repo_tokens(
    *,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    include_patterns=None,
    exclude_patterns=None,
    max_file_size: int = 100000,
    model: Optional[str] = "gpt-5",
    overhead_percent: float = 3.0,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    files = _gather_files(path, repo, include_patterns, exclude_patterns, max_file_size, github_token)

    per_file = []
    sum_file_tokens = 0
    for file_path, content in files.items():
        tokens = count_tokens(content, model=model)
        size_bytes = len(content.encode("utf-8")) if content is not None else 0
        per_file.append({
            "path": file_path,
            "size_bytes": size_bytes,
            "tokens": tokens,
        })
        sum_file_tokens += tokens

    # Apply small overhead to account for prompt scaffolding and separators
    overhead_tokens = int(sum_file_tokens * (overhead_percent / 100.0))
    grand_total = sum_file_tokens + overhead_tokens

    return {
        "model": model,
        "max_context_tokens": None,  # filled by caller for printing decisions
        "overhead_percent": overhead_percent,
        "sum_file_tokens": sum_file_tokens,
        "overhead_tokens": overhead_tokens,
        "total_tokens": grand_total,
        "files": per_file,
    }


def run_estimate_cli(args) -> int:
    github_token = args.token or os.environ.get("GITHUB_TOKEN") if getattr(args, "repo", None) else None

    result = estimate_repo_tokens(
        path=args.dir,
        repo=args.repo,
        include_patterns=set(args.include) if args.include else None,
        exclude_patterns=set(args.exclude) if args.exclude else None,
        max_file_size=args.max_size,
        model=args.model,
        overhead_percent=args.overhead_percent,
        github_token=github_token,
    )

    result["max_context_tokens"] = args.max_context_tokens
    within_limit = result["total_tokens"] <= args.max_context_tokens

    payload = {
        **result,
        "within_limit": within_limit,
    }

    # Prepare concise stdout output (omit per-file details to keep terminal output short)
    file_count = len(result.get("files", []))
    printed = {k: v for k, v in payload.items() if k != "files"}
    printed["file_count"] = file_count
    print(json.dumps(printed, indent=2))

    # Optionally write to file
    if getattr(args, "out", None):
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to write output to {args.out}: {e}")

    # Exit code: 0 within limit, 2 over limit
    return 0 if within_limit else 2


