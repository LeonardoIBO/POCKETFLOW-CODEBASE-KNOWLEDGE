import dotenv
import os
import argparse
# Import the function that creates the flow
from flow import create_tutorial_flow
from utils.estimate_repo_tokens import run_estimate_cli

dotenv.load_dotenv()

# Default file patterns
DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile",
    "*Makefile", "*.yaml", "*.yml",
}

DEFAULT_EXCLUDE_PATTERNS = {
    "assets/*", "data/*", "images/*", "public/*", "static/*", "temp/*",
    "*docs/*",
    "*venv/*",
    "*.venv/*",
    "*test*",
    "*tests/*",
    "*examples/*",
    "v1/*",
    "*dist/*",
    "*build/*",
    "*experimental/*",
    "*deprecated/*",
    "*misc/*",
    "*legacy/*",
    ".git/*", ".github/*", ".next/*", ".vscode/*",
    "*obj/*",
    "*bin/*",
    "*node_modules/*",
    "*.log"
}

# --- Main Function ---
def main():
    parser = argparse.ArgumentParser(description="Generate documentation or estimate repository token size.")

    subparsers = parser.add_subparsers(dest="command", required=False)

    # Subcommand: estimate-repo
    estimate_parser = subparsers.add_parser("estimate-repo", help="Estimate tokens required for a repository")
    estimate_source = estimate_parser.add_mutually_exclusive_group(required=True)
    estimate_source.add_argument("--repo", help="URL of the public GitHub repository.")
    estimate_source.add_argument("--dir", help="Path to local directory.")
    estimate_parser.add_argument("-t", "--token", help="GitHub personal access token (optional; reads from GITHUB_TOKEN env var if not provided).")
    estimate_parser.add_argument("-i", "--include", nargs="+", help="Include file patterns (e.g. '*.py' '*.js').")
    estimate_parser.add_argument("-e", "--exclude", nargs="+", help="Exclude file patterns (e.g. 'tests/*' 'docs/*').")
    estimate_parser.add_argument("-s", "--max-size", type=int, default=100000, help="Maximum file size in bytes (default: 100000).")
    estimate_parser.add_argument("--model", default="gpt-5", help="Model hint for tokenizer selection (default: gpt-5).")
    estimate_parser.add_argument("--max-context-tokens", type=int, default=200000, help="Context window to compare against (default: 200000).")
    estimate_parser.add_argument("--overhead-percent", type=float, default=3.0, help="Overhead percent for prompt scaffolding (default: 3.0).")
    estimate_parser.add_argument("--out", help="Optional path to write JSON output.")

    # Default command: generate tutorial (backward compatible; no subcommand)
    parser.add_argument("--repo", help="URL of the public GitHub repository.")
    parser.add_argument("--dir", help="Path to local directory.")
    parser.add_argument("-n", "--name", help="Project name (optional, derived from repo/directory if omitted).")
    parser.add_argument("-t", "--token", help="GitHub personal access token (optional, reads from GITHUB_TOKEN env var if not provided).")
    parser.add_argument("-o", "--output", default="output", help="Base directory for output (default: ./output).")
    parser.add_argument("-i", "--include", nargs="+", help="Include file patterns (e.g. '*.py' '*.js'). Defaults to common code files if not specified.")
    parser.add_argument("-e", "--exclude", nargs="+", help="Exclude file patterns (e.g. 'tests/*' 'docs/*'). Defaults to test/build directories if not specified.")
    parser.add_argument("-s", "--max-size", type=int, default=100000, help="Maximum file size in bytes (default: 100000, about 100KB).")
    parser.add_argument("--language", default="english", help="Language for the generated tutorial (default: english)")
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM response caching (default: caching enabled)")
    parser.add_argument("--max-abstractions", type=int, default=10, help="Maximum number of abstractions to identify (default: 10)")
    parser.add_argument("--audience-level", choices=["beginner", "professional"], default="professional", help="Target audience level for documentation tone (default: professional)")

    args = parser.parse_args()

    # If estimate-repo subcommand requested
    if args.command == "estimate-repo":
        exit_code = run_estimate_cli(args)
        raise SystemExit(exit_code)

    # Get GitHub token from argument or environment variable if using repo
    github_token = None
    if args.repo:
        github_token = args.token or os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("Warning: No GitHub token provided. You might hit rate limits for public repositories.")

    # Initialize the shared dictionary with inputs
    shared = {
        "repo_url": args.repo,
        "local_dir": args.dir,
        "project_name": args.name, # Can be None, FetchRepo will derive it
        "github_token": github_token,
        "output_dir": args.output, # Base directory for CombineTutorial output

        # Add include/exclude patterns and max file size
        "include_patterns": set(args.include) if args.include else DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": set(args.exclude) if args.exclude else DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": args.max_size,

        # Add language for multi-language support
        "language": args.language,
        
        # Add use_cache flag (inverse of no-cache flag)
        "use_cache": not args.no_cache,
        
        # Add max_abstraction_num parameter
        "max_abstraction_num": args.max_abstractions,

        # Add audience level for tone control
        "audience_level": args.audience_level,

        # Outputs will be populated by the nodes
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "chapters": [],
        "final_output_dir": None
    }

    # Display starting message with repository/directory and language
    print(f"Starting tutorial generation for: {args.repo or args.dir} in {args.language.capitalize()} language")
    print(f"LLM caching: {'Disabled' if args.no_cache else 'Enabled'}")

    # Create the flow instance
    tutorial_flow = create_tutorial_flow()

    # Run the flow
    tutorial_flow.run(shared)

if __name__ == "__main__":
    main()
