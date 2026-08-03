from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SummaryCorpusStats:
    total_rows: int
    written_rows: int
    empty_rows: int


class SummaryCorpusError(ValueError):
    """Raised when the summary-only source contract is violated."""


def prepare_summary_corpus(
    csv_path: Path, output_path: Path
) -> SummaryCorpusStats:
    documents: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or "summary" not in reader.fieldnames:
            raise SummaryCorpusError("CSV is missing required 'summary' column")
        for index, row in enumerate(reader, start=1):
            summary = row["summary"].strip()
            if not summary:
                raise SummaryCorpusError(f"CSV row {index} has an empty summary")
            documents.append(
                {
                    "id": f"summary-{index:06d}",
                    "title": f"Summary {index:06d}",
                    "text": summary,
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(output_path)
    return SummaryCorpusStats(
        total_rows=len(documents),
        written_rows=len(documents),
        empty_rows=0,
    )
