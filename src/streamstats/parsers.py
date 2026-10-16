import csv
import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from streamstats import errors
from streamstats.models import Event, SkippedEventsCount

logger = logging.getLogger(__name__)


def validate_and_build_event(line_number: int,
                             path: Path,
                             path_number: int,
                             event_data: dict,
                             skipped_events: SkippedEventsCount,
                             skip_invalid: bool = False,
                             ) -> Event | False:
    """ Проверяет значения события на корректность и возвращает их в формате класса Event. """
    # Проверяем временную метку и преобразование её в datetime
    if not isinstance(event_data['timestamp'], str):
        if skip_invalid:
            logger.warning(
                'Временная метка строки %d в файле %d %s должна являться строкой',
                line_number,
                path_number,
                path
            )
            skipped_events.count += 1
            return False
        logger.error(
            'Временная метка строки %d в файле %d %s должна являться строкой',
            line_number,
            path_number,
            path
        )
        raise errors.InvalidTimestampError(f'Временная метка строки {line_number} в файле {path_number} {path} '
                                           f'должна являться строкой')
    try:
        timestamp = datetime.fromisoformat(event_data['timestamp'])

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        timestamp_utc = timestamp.astimezone(UTC)
    except ValueError:
        if skip_invalid:
            logger.warning('Некорректная запись времени в строке %d в файле %d %s', line_number, path_number, path)
            skipped_events.count += 1
            return False
        logger.error('Некорректная запись времени в строке %d в файле %d %s', line_number, path_number, path)
        raise errors.InvalidTimestampError(f'Некорректная запись времени в строке {line_number} в файле '
                                           f'{path_number} {path}')

    # Проверяем уровень
    if not isinstance(event_data['level'], str):
        if skip_invalid:
            logger.warning(
                'Уровень в строке %d в файле %d %s должен являться строкой',
                line_number,
                path_number,
                path
            )
            skipped_events.count += 1
            return False
        logger.error(
            'Уровень в строке %d в файле %d %s должен являться строкой',
            line_number,
            path_number,
            path
        )
        raise errors.InvalidEventError(f'Уровень в строке {line_number} в файле {path_number} {path} должен'
                                       f' являться строкой')

    if event_data['level'].upper() not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
        if skip_invalid:
            logger.warning('Некорректный уровень в строке %d в файле %d %s', line_number, path_number, path)
            skipped_events.count += 1
            return False
        logger.error('Некорректный уровень в строке %d в файле %d %s', line_number, path_number, path)
        raise errors.InvalidEventError(f'Некорректный уровень в строке {line_number} в файле {path_number} {path}')

    # Проверяем источник
    if isinstance(event_data['source'], str):
        source = event_data['source'].strip()
        if source == '':
            if skip_invalid:
                logger.warning(
                    'Источник строки %d в файле %d %s не может быть пустым или состоять только из пробелов',
                    line_number,
                    path_number,
                    path
                )
                skipped_events.count += 1
                return False
            logger.error(
                'Источник строки %d в файле %d %s не может быть пустым или состоять только из пробелов',
                line_number,
                path_number,
                path
            )
            raise errors.InvalidEventError(f'Источник строки {line_number} в файле {path_number} {path} не может '
                                           'быть пустым или состоять только из пробелов')
    else:
        if skip_invalid:
            logger.warning(
                'Источник строки %d в файле %d %s должен являться строкой',
                line_number,
                path_number,
                path
            )
            skipped_events.count += 1
            return False
        logger.error(
            'Источник строки %d в файле %d %s должен являться строкой',
            line_number,
            path_number,
            path
        )
        raise errors.InvalidEventError(f'Источник строки {line_number} в файле {path_number} {path} должен '
                                       'являться строкой')

    # Проверяем сообщение
    if not isinstance(event_data['message'], str):
        if skip_invalid:
            logger.warning(
                'Сообщение строки %d в файле %d %s должно являться строкой',
                line_number,
                path_number,
                path
            )
            skipped_events.count += 1
            return False
        logger.error(
            'Сообщение строки %d в файле %d %s должно являться строкой',
            line_number,
            path_number,
            path
        )
        raise errors.InvalidEventError(f'Сообщение строки {line_number} в файле {path_number} {path} должно '
                                       'являться строкой')

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
    """ Генератор, который выдаёт события в формате класса Event из JSONL-файла. """
    with path.open('r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, start=1):
            # Берём значение из строки json-файла
            try:
                event_data = json.loads(line)
            except json.JSONDecodeError:
                if skip_invalid:
                    logger.warning('Повреждённая строка %d в файле %d %s', line_number, path_number, path)
                    skipped_events.count += 1
                    continue
                logger.error('Повреждённая строка %d в файле %d %s', line_number, path_number, path)
                raise errors.InvalidEventError(f'Повреждённая строка {line_number} в файле {path_number} {path}')

            # Проверяем, является ли взятая строка словарём
            if not isinstance(event_data, dict):
                if skip_invalid:
                    logger.warning('Повреждённая строка %d в файле %d %s', line_number, path_number, path)
                    skipped_events.count += 1
                    continue
                logger.error('Повреждённая строка %d в файле %d %s', line_number, path_number, path)
                raise errors.InvalidEventError(f'Повреждённая строка {line_number} в файле {path_number} {path}')

            # Проверяем на наличие всех полей в строке
            if not {'level', 'message', 'source', 'timestamp'}.issubset(event_data.keys()):
                if skip_invalid:
                    logger.warning('Строка %d в файле %d %s не соответствует формату', line_number, path_number, path)
                    skipped_events.count += 1
                    continue
                logger.error('Строка %d в файле %d %s не соответствует формату', line_number, path_number, path)
                raise errors.InvalidEventError(f'Строка {line_number} в файле {path_number} {path} не '
                                               'соответствует формату')

            event = validate_and_build_event(
                line_number=line_number,
                path=path,
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

        # Проверяем пустой файла
        if reader.fieldnames is None:
            logger.error('CSV-файл %d %s пустой или не содержит заголовков', path_number, path)
            raise errors.InvalidEventError(f'CSV-файл {path_number} пустой или не содержит заголовков')

        # Проверяем на наличие всех обязательных столбцов
        if not {'level', 'message', 'source', 'timestamp'}.issubset(reader.fieldnames):
            logger.error('В CSV-файле %d %s отсутствуют обязательные столбцы', path_number, path)
            raise errors.InvalidEventError(f'В CSV-файле {path_number} отсутствуют обязательные столбцы')

        # Проверяем на повтор заголовков
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            logger.error('CSV-файл %d %s содержит повторяющиеся заголовки', path_number, path)
            raise errors.InvalidEventError(f'CSV-файл {path_number} содержит повторяющиеся заголовки')

        for line_number, event_data in enumerate(reader, start=2):
            # Проверяем на наличие всех обязательных строк
            if event_data['timestamp'] is None:
                if skip_invalid:
                    logger.warning(
                        'Отсутствует временная метка в строке %d в файле %d %s',
                        line_number,
                        path_number,
                        path
                    )
                    skipped_events.count += 1
                    continue
                logger.error(
                    'Отсутствует временная метка в строке %d в файле %d %s',
                    line_number,
                    path_number,
                    path
                )
                raise errors.InvalidTimestampError(
                    f'Отсутствует временная метка в строке {line_number} в файле {path_number} {path}'
                )
            if event_data['level'] is None:
                if skip_invalid:
                    logger.warning(
                        'Отсутствует уровень в строке %d в файле %d %s', line_number, path_number, path
                    )
                    skipped_events.count += 1
                    continue
                logger.error(
                    'Отсутствует уровень в строке %d в файле %d %s', line_number, path_number, path
                )
                raise errors.InvalidEventError(f'Отсутствует уровень в строке {line_number} в файле {path_number}'
                                               f' {path}')
            if event_data['source'] is None:
                if skip_invalid:
                    logger.warning('Отсутствует источник в строке %d в файле %d %s', line_number, path_number, path)
                    skipped_events.count += 1
                    continue
                logger.error('Отсутствует источник в строке %d в файле %d %s', line_number, path_number, path)
                raise errors.InvalidEventError(f'Отсутствует источник в строке {line_number} в файле {path_number} '
                                               f'{path}')
            if event_data['message'] is None:
                if skip_invalid:
                    logger.warning('Отсутствует сообщение в строке %d в файле %d %s', line_number, path_number, path)
                    skipped_events.count += 1
                    continue
                logger.error('Отсутствует сообщение в строке %d в файле %d %s', line_number, path_number, path)
                raise errors.InvalidEventError(f'Отсутствует сообщение в строке {line_number} в файле {path_number} '
                                               f'{path}')

            event = validate_and_build_event(
                line_number=line_number,
                path=path,
                path_number=path_number,
                event_data=event_data,
                skipped_events=skipped_events,
                skip_invalid=skip_invalid
            )
            if event:
                yield event
