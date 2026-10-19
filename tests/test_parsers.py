import pytest
from pathlib import Path

from streamstats.models import SkippedEventsCount
from streamstats.parsers import parse_csv, parse_jsonl
from streamstats.errors import StreamStatsError


def test_parse_csv(tmp_path: Path):
    file = tmp_path / "events.csv"

    file.write_text(
        "timestamp,level,source,message\n"
        "2026-10-18T10:00:00Z,INFO,api,Started\n",
        encoding="utf-8"
    )

    skipped = SkippedEventsCount()

    events = list(
        parse_csv(
            path=file,
            path_number=1,
            skipped_events=skipped
        )
    )

    assert len(events) == 1
    assert events[0].level == "INFO"
    assert events[0].source == "api"
    assert events[0].message == "Started"
    assert skipped.count == 0


def test_parse_jsonl(tmp_path: Path):
    file = tmp_path / "events.jsonl"
    file.write_text(
        '{"timestamp": "2026-10-18T10:00:00Z", "level": "INFO", "source": "api", "message": "Started"}\n',
        encoding="utf-8",
    )

    skipped = SkippedEventsCount()

    events = list(
        parse_jsonl(
            path=file,
            path_number=1,
            skipped_events=skipped,
        )
    )

    assert len(events) == 1
    assert events[0].level == "INFO"
    assert events[0].source == "api"
    assert events[0].message == "Started"
    assert skipped.count == 0


def test_parse_empty_csv(tmp_path: Path):
    file = tmp_path / "empty.csv"
    file.write_text("", encoding="utf-8")

    skipped = SkippedEventsCount(count=0)

    with pytest.raises(StreamStatsError):
        list(
            parse_csv(
                path=file,
                path_number=1,
                skipped_events=skipped,
                skip_invalid=True
            )
        )


def test_parse_empty_csv_with_headlines(tmp_path: Path):
    csv_file = tmp_path / "empty_with_headers.csv"
    csv_file.write_text(
        "timestamp,level,source,message\n",
        encoding="utf-8",
    )

    skipped = SkippedEventsCount(count=0)

    events = list(
        parse_csv(
            path=csv_file,
            path_number=1,
            skipped_events=skipped,
        )
    )

    assert events == []
    assert skipped.count == 0


def test_parse_empty_jsonl(tmp_path: Path):
    jsonl_file = tmp_path / "empty.jsonl"
    jsonl_file.write_text("", encoding="utf-8")

    skipped = SkippedEventsCount(count=0)

    events = list(
        parse_jsonl(
            path=jsonl_file,
            path_number=1,
            skipped_events=skipped,
        )
    )

    assert events == []
    assert skipped.count == 0
