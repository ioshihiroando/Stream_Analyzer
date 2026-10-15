import csv
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from streamstats import errors
from streamstats.models import Event, SkippedEventsCount


def validate_and_build_event(line_number: int,
                             path_number: int,
                             event_data: dict,
                             skipped_events: SkippedEventsCount,
                             skip_invalid: bool = False,
                             ) -> Event | False:
    """ Проверяет значения события на корректность и возвращает их в формате класса Event """
    # Проверка временной метки и преобразование её в datetime
    if not isinstance(event_data['timestamp'], str):
        if skip_invalid:
            skipped_events.count += 1
            return False
        raise errors.InvalidTimestampError(f'Временная метка строки {line_number} в файле {path_number} должна ' +
                                           f'являться строкой: {event_data}')
    try:
        timestamp = datetime.fromisoformat(event_data['timestamp'])

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        timestamp_utc = timestamp.astimezone(UTC)
    except ValueError as error:
        if skip_invalid:
            skipped_events.count += 1
            return False
        raise errors.InvalidTimestampError(f'Некорректная запись времени в строке {line_number} в файле ' +
                                           f'{path_number}: "{event_data["timestamp"]}"\n' +
                                           f'Полная строка: {event_data}') from error

    # Проверка уровня
    if not isinstance(event_data['level'], str):
        if skip_invalid:
            skipped_events.count += 1
            return False
        raise errors.InvalidEventError(f'Уровень в строке {line_number} в файле {path_number} должен' +
                                       f' являться строкой: {event_data}')

    if event_data['level'].upper() not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
        if skip_invalid:
            skipped_events.count += 1
            return False
        raise errors.InvalidEventError(f'Некорректный уровень в строке {line_number} в файле {path_number}: ' +
                                       f'"{event_data["level"]}"\nПолная строка: {event_data}')

    # Проверка источника
    if isinstance(event_data['source'], str):
        source = event_data['source'].strip()
        if source == '':
            if skip_invalid:
                skipped_events.count += 1
                return False
            raise errors.InvalidEventError(f'Источник строки {line_number} в файле {path_number} не может быть ' +
                                           f'пустым или состоять только из пробелов: "{event_data["source"]}"\n' +
                                           f'Полная строка: {event_data}')
    else:
        if skip_invalid:
            skipped_events.count += 1
            return False
        raise errors.InvalidEventError(f'Источник строки {line_number} в файле {path_number} должен являться ' +
                                       f'строкой: {event_data}')

    # Проверка сообщения
    if not isinstance(event_data['message'], str):
        if skip_invalid:
            skipped_events.count += 1
            return False
        raise errors.InvalidEventError(f'Сообщение строки {line_number} в файле {path_number} должно являться ' +
                                       f'строкой: {event_data}')

    event = Event(
        timestamp=timestamp_utc,
        level=event_data['level'].upper(),
        source=source,
        message=event_data['message']
    )

    return event


def parse_jsonl(path: Path,
                path_number: int,
                skipped_events: SkippedEventsCount,
                skip_invalid: bool = False,
                ) -> Iterator[Event]:
    """ Генератор, который выдаёт события в формате класса Event из JSONL-файла """
    with path.open('r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, start=1):
            try:
                event_data = json.loads(line)
            except json.JSONDecodeError as error:
                if skip_invalid:
                    skipped_events.count += 1
                    continue
                raise errors.InvalidEventError(f'Повреждённая строка {line_number} в файле {path_number}: {line}') \
                    from error

            if not isinstance(event_data, dict):
                if skip_invalid:
                    skipped_events.count += 1
                    continue
                raise errors.InvalidEventError(f'Повреждённая строка {line_number} в файле {path_number}: {line}')

            # Проверка на наличие всех полей в строке
            if not {'level', 'message', 'source', 'timestamp'}.issubset(event_data.keys()):
                if skip_invalid:
                    skipped_events.count += 1
                    continue
                raise errors.InvalidEventError(f'Строка {line_number} в файле {path_number} не соответствует' +
                                               f' формату: {line}')

            event = validate_and_build_event(
                line_number=line_number,
                path_number=path_number,
                event_data=event_data,
                skipped_events=skipped_events,
                skip_invalid=skip_invalid
            )
            if event:
                yield event


def parse_csv(path: Path,
              path_number: int,
              skipped_events: SkippedEventsCount,
              skip_invalid: bool = False,
              ) -> Iterator[Event]:
    """ Генератор, который выдаёт события в формате класса Event из CSV-файла """
    with path.open('r', encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)

        # Проверка пустого файла
        if reader.fieldnames is None:
            raise errors.InvalidEventError(f'CSV-файл {path_number} пустой или не содержит заголовков')

        # Проверка на наличие всех обязательных столбцов
        if not {'level', 'message', 'source', 'timestamp'}.issubset(reader.fieldnames):
            raise errors.InvalidEventError(f'В CSV-файле {path_number} отсутствуют обязательные столбцы')

        # Проверка на повтор заголовков
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise errors.InvalidEventError(f'CSV-файл {path_number} содержит повторяющиеся заголовки')

        for line_number, event_data in enumerate(reader, start=2):
            # Проверка на наличие всех обязательных строк
            if event_data['timestamp'] is None:
                if skip_invalid:
                    skipped_events.count += 1
                    continue
                raise errors.InvalidTimestampError(
                    f'Отсутствует временная метка в строке {line_number} в файле {path_number}: \n{event_data}')
            if event_data['level'] is None:
                if skip_invalid:
                    skipped_events.count += 1
                    continue
                raise errors.InvalidEventError(f'Отсутствует уровень в строке {line_number} в файле {path_number}: ' +
                                               f'\n{event_data}')
            if event_data['source'] is None:
                if skip_invalid:
                    skipped_events.count += 1
                    continue
                raise errors.InvalidEventError(f'Отсутствует источник в строке {line_number} в файле {path_number}: ' +
                                               f'\n{event_data}')
            if event_data['message'] is None:
                if skip_invalid:
                    skipped_events.count += 1
                    continue
                raise errors.InvalidEventError(f'Отсутствует сообщение в строке {line_number} в файле {path_number}: ' +
                                               f'\n{event_data}')

            event = validate_and_build_event(
                line_number=line_number,
                path_number=path_number,
                event_data=event_data,
                skipped_events=skipped_events,
                skip_invalid=skip_invalid
            )
            if event:
                yield event
