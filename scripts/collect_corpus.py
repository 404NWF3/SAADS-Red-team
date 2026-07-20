from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm_defense_graphrag.corpus import DEFAULT_CONFIG, collect, validate_existing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect and audit the LLM defense GraphRAG corpus."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--min-docs", type=int, default=100)
    parser.add_argument(
        "--strict", action="store_true", help="Fail if any configured source cannot be collected."
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Validate local files without network access."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = (
        validate_existing(args.min_docs)
        if args.validate_only
        else collect(args.config, args.min_docs, args.strict)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
