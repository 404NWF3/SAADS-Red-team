import json
from pathlib import Path

import pytest

from llm_defense_graphrag.summary_corpus import (
    SummaryCorpusError,
    prepare_summary_corpus,
)


def test_prepare_summary_corpus_uses_only_summary_values(tmp_path: Path) -> None:
    source = tmp_path / "items.csv"
    source.write_text(
        "item_id,title,summary,source_uri\n"
        "forbidden-id,forbidden-title,Allowed summary.,https://forbidden.test\n",
        encoding="utf-8-sig",
    )

    output = tmp_path / "summary_corpus.json"
    stats = prepare_summary_corpus(source, output)
    output_text = output.read_text(encoding="utf-8")
    rows = json.loads(output_text)

    assert rows == [
        {
            "id": "summary-000001",
            "title": "Summary 000001",
            "text": "Allowed summary.",
        }
    ]
    assert stats.total_rows == 1
    assert stats.written_rows == 1
    assert stats.empty_rows == 0
    assert "forbidden" not in output_text.lower()


def test_prepare_summary_corpus_requires_summary_column(tmp_path: Path) -> None:
    source = tmp_path / "items.csv"
    source.write_text("item_id,title\n1,No summary\n", encoding="utf-8-sig")

    with pytest.raises(SummaryCorpusError, match="missing required 'summary' column"):
        prepare_summary_corpus(source, tmp_path / "summary_corpus.json")


def test_prepare_summary_corpus_rejects_empty_summary(tmp_path: Path) -> None:
    source = tmp_path / "items.csv"
    source.write_text(
        "item_id,summary\n1,Allowed\n2,   \n",
        encoding="utf-8-sig",
    )

    with pytest.raises(SummaryCorpusError, match="row 2 has an empty summary"):
        prepare_summary_corpus(source, tmp_path / "summary_corpus.json")
