import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_jsonl_timestamps_invalid_skip_invalid(tmp_path: Path):
    input_file = Path(__file__).parent / "data" / "timestamps_invalid.jsonl"
    output_file = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(output_file),
            "--skip-invalid",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert output_file.exists()

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report["event_total_count"] == 4
    assert report["event_by_level"] == {"INFO": 4}
    assert report["event_by_source"] == {"app": 4}
    assert report["top_error_sources"] == {}

    assert report["first_timestamp"] == "2025-01-15T00:00:00+00:00"
    assert report["last_timestamp"] == "2025-01-15T10:30:00+00:00"

    assert report["skipped_events"] == 8


def test_cli_jsonl_timestamps_without_skip_invalid(tmp_path: Path):
    input_file = Path(__file__).parent / "data" / "timestamps_invalid.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(tmp_path / "report.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 2


def test_cli_jsonl_all_invalid_cases_skip_invalid(tmp_path: Path):
    input_file = Path(__file__).parent / "data" / "invalid_mixed.jsonl"
    output_file = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(output_file),
            "--skip-invalid",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert output_file.exists()

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report == {
        "event_total_count": 4,
        "event_by_level": {
            "INFO": 1,
            "ERROR": 1,
            "WARNING": 1,
            "CRITICAL": 1,
        },
        "event_by_source": {
            "api": 2,
            "db": 2,
        },
        "top_error_sources": {
            "db": 2,
        },
        "first_timestamp": "2025-02-01T10:00:00+00:00",
        "last_timestamp": "2025-02-01T10:09:00+00:00",
        "skipped_events": 12,
    }


def test_cli_jsonl_multiple_files(tmp_path: Path):
    input_file_1 = Path(__file__).parent / "data" / "file_1.jsonl"
    input_file_2 = Path(__file__).parent / "data" / "file_2.jsonl"
    output_file = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file_1),
            str(input_file_2),
            "--format",
            "jsonl",
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert output_file.exists()

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report == {
        "event_total_count": 4,
        "event_by_level": {
            "INFO": 1,
            "ERROR": 1,
            "WARNING": 1,
            "CRITICAL": 1,
        },
        "event_by_source": {
            "api": 2,
            "db": 2,
        },
        "top_error_sources": {
            "db": 2,
        },
        "first_timestamp": "2025-02-01T10:00:00+00:00",
        "last_timestamp": "2025-02-01T10:03:00+00:00",
        "skipped_events": 0,
    }


def test_cli_jsonl_multiple_files_skip_invalid(tmp_path: Path):
    input_file_1 = Path(__file__).parent / "data" / "file_1.jsonl"
    input_file_2 = Path(__file__).parent / "data" / "file_3.jsonl"
    output_file = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file_1),
            str(input_file_2),
            "--format",
            "jsonl",
            "--output",
            str(output_file),
            "--skip-invalid",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert output_file.exists()

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report == {
        "event_total_count": 4,
        "event_by_level": {
            "INFO": 1,
            "ERROR": 1,
            "WARNING": 1,
            "CRITICAL": 1,
        },
        "event_by_source": {
            "api": 2,
            "db": 2,
        },
        "top_error_sources": {
            "db": 2,
        },
        "first_timestamp": "2025-02-01T10:00:00+00:00",
        "last_timestamp": "2025-02-01T10:03:00+00:00",
        "skipped_events": 2,
    }


def test_cli_jsonl_unicode(tmp_path: Path):
    input_file = Path(__file__).parent / "data" / "unicode.jsonl"
    output_file = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert output_file.exists()

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report == {
        "event_total_count": 3,
        "event_by_level": {
            "INFO": 1,
            "WARNING": 1,
            "ERROR": 1,
        },
        "event_by_source": {
            "приложение": 1,
            "数据库": 1,
            "app": 1,
        },
        "top_error_sources": {
            "app": 1,
        },
        "first_timestamp": "2025-03-01T10:00:00+00:00",
        "last_timestamp": "2025-03-01T10:02:00+00:00",
        "skipped_events": 0,
    }


def test_cli_jsonl_integration(tmp_path: Path):
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "report.json"

    input_file.write_text(
        '{"timestamp": "2025-03-01T10:00:00Z", '
        '"level": "INFO", "source": "app", "message": "Запуск"}\n'
        '{"timestamp": "2025-03-01T10:01:00Z", '
        '"level": "ERROR", "source": "db", "message": "Ошибка базы"}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert output_file.exists()

    report = json.loads(output_file.read_text(encoding="utf-8"))

    assert report == {
        "event_total_count": 2,
        "event_by_level": {
            "INFO": 1,
            "ERROR": 1,
        },
        "event_by_source": {
            "app": 1,
            "db": 1,
        },
        "top_error_sources": {
            "db": 1,
        },
        "first_timestamp": "2025-03-01T10:00:00+00:00",
        "last_timestamp": "2025-03-01T10:01:00+00:00",
        "skipped_events": 0,
    }
