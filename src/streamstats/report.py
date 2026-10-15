import json
from pathlib import Path

from streamstats.models import AnalysisResult, SkippedEventsCount


def build_dict(
        result: AnalysisResult,
        skipped_events: SkippedEventsCount
) -> dict:
    # Формирование top-5 источников ошибок уровня ERROR/CRITICAL
    top5_error_sources = sorted(
        [(key, value) for key, value in result.error_sources.items()],
        key=lambda x: [-x[1], x[0]]
    )[:5]

    return {
        'event_total_count': result.event_total_count,
        'event_by_level': result.event_by_level,
        'event_by_source': result.event_by_source,
        'top_error_sources': dict(top5_error_sources),
        'first_timestamp': result.first_timestamp.isoformat() if result.first_timestamp else None,
        'last_timestamp': result.last_timestamp.isoformat() if result.last_timestamp else None,
        'skipped_events': skipped_events.count
    }


def write_report_json(report: dict,
                      output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )
