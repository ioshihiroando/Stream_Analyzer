from collections.abc import Iterable

from streamstats.models import AnalysisResult, Event


def create_analysis_result_object() -> AnalysisResult:
    return AnalysisResult(
        event_total_count=0,
        event_by_level={},
        event_by_source={},
        error_sources={},
        first_timestamp=None,
        last_timestamp=None
    )


def analyze_events(
        analysis_result: AnalysisResult,
        events: Iterable[Event]
):

    for event in events:
        # Увеличение общего числа событий
        analysis_result.event_total_count += 1

        # Увеличение числа событий для уровня текущего события
        analysis_result.event_by_level[event.level] = analysis_result.event_by_level.get(event.level, 0) + 1

        # Увеличение числа событий для источника текущего события
        analysis_result.event_by_source[event.source] = analysis_result.event_by_source.get(event.source, 0) + 1

        # Увеличение числа ошибок уровня ERROR/CRITICAL для источника текущего события
        if event.level in ('ERROR', 'CRITICAL'):
            analysis_result.error_sources[event.source] = analysis_result.error_sources.get(event.source, 0) + 1

        # Сравнение временной метки с текущими первой и последней временными метками файла
        if analysis_result.first_timestamp is None:
            analysis_result.first_timestamp = event.timestamp
        if analysis_result.last_timestamp is None:
            analysis_result.last_timestamp = event.timestamp

        analysis_result.first_timestamp = min(analysis_result.first_timestamp, event.timestamp)

        analysis_result.last_timestamp = max(analysis_result.last_timestamp, event.timestamp)
