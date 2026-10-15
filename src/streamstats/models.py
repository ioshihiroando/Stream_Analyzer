from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    timestamp: datetime
    level: str
    source: str
    message: str


@dataclass
class AnalysisResult:
    event_total_count: int
    event_by_level: dict[str, int]
    event_by_source: dict[str, int]
    error_sources: dict[str, int]

    first_timestamp: datetime | None
    last_timestamp: datetime | None


@dataclass
class SkippedEventsCount:
    count: int = 0
