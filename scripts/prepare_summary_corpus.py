from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm_defense_graphrag.summary_corpus import prepare_summary_corpus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an isolated GraphRAG corpus from CSV summary values only."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/items_20260713T095333Z.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("summary_input/summary_corpus.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = prepare_summary_corpus(args.csv, args.output)
    print(
        json.dumps(
            {
                "source": str(args.csv),
                "output": str(args.output),
                "total_rows": stats.total_rows,
                "written_rows": stats.written_rows,
                "empty_rows": stats.empty_rows,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
