import argparse
import logging
import sys
from pathlib import Path

from streamstats.analysis import analyze_events, create_analysis_result_object
from streamstats.errors import StreamStatsError
from streamstats.logging_config import setup_logging
from streamstats.models import SkippedEventsCount
from streamstats.parsers import parse_csv, parse_jsonl
from streamstats.report import build_dict, write_report_json

ROOT = Path(__file__).resolve().parents[2]


def main():
    # устанавливаем журнал логов
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info('Программа начала работу')

    parser = argparse.ArgumentParser(
        prog='python -m streamstats',
        description='Streaming File Analyzer',
        epilog=(
            'Examples:\n'
            '   python -m streamstats analyze INPUT [INPUT ...] --format csv|jsonl --output REPORT.json\n'
            '   python -m streamstats analyze INPUT --format jsonl --skip-invalid'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(
        dest='command',
        required=True
    )

    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze event files'
    )

    analyze_parser.add_argument(
        'input',
        nargs='+',
        type=Path,
        help='Input files to analyze'
    )

    analyze_parser.add_argument(
        '--format',
        dest='format',
        choices=['csv', 'jsonl'],
        required=True,
        help='Input file format'
    )

    analyze_parser.add_argument(
        '--output',
        dest='output_path',
        type=Path,
        default=ROOT / 'reports' / 'report.json',
        help='Output JSON report path (default: reports/report.json)'
    )

    analyze_parser.add_argument(
        '--skip-invalid',
        dest='skip_invalid',
        action='store_true',
        help='Skip invalid records instead of stopping'
    )

    args = parser.parse_args()

    try:
        if args.command == 'analyze':
            skip_events_count = SkippedEventsCount()
            analysis_result = create_analysis_result_object()
            for path_number, path in enumerate(args.input, start=1):
                try:
                    logger.info('Начало анализа файла %d %s', path_number, path)

                    # проверяем файл на соответствие формату .jsonl и создание итератора для построчного чтения файла
                    if args.format == 'jsonl':
                        if path.suffix != '.jsonl':
                            logger.error('Файл %d %s не имеет расширения .jsonl', path_number, path)
                            raise StreamStatsError(f'Файл {path} не имеет расширения .jsonl')

                        iterator = parse_jsonl(
                            path=path,
                            path_number=path_number,
                            skipped_events=skip_events_count,
                            skip_invalid=args.skip_invalid
                        )

                    # проверяем файл на соответствие формату .csv и создание итератора для построчного чтения файла
                    elif args.format == 'csv':
                        if path.suffix != '.csv':
                            logger.error('Файл %d %s не имеет расширения .csv', path_number, path)
                            raise StreamStatsError(f'Файл {path} не имеет расширения .csv')
                        iterator = parse_csv(
                            path=path,
                            path_number=path_number,
                            skipped_events=skip_events_count,
                            skip_invalid=args.skip_invalid
                        )
                    else:
                        logger.error('Неизвестный тип файла %d %s: %s', path_number, path, args.format)
                        raise StreamStatsError(f'Неизвестный тип файла: {args.format}')

                    # запускаем анализатора логов, который выдаст статистику в analysis_result
                    analyze_events(
                        analysis_result=analysis_result,
                        events=iterator
                    )
                    logger.info('Анализ файла %d %s завершён успешно', path_number, path)

                except FileNotFoundError as error:
                    logger.error('Файл %d %s не найден', path_number, path)
                    raise StreamStatsError(f'Файл {path} не найден') from error

            # создаём словарь с данными анализа и запись отчёта
            report = build_dict(
                result=analysis_result,
                skipped_events=skip_events_count
            )

            output_path = Path(args.output_path)

            write_report_json(
                report=report,
                output_path=output_path
            )
            logger.info('Отчёт сохранён успешно')

        else:
            parser.print_help()
        logger.info('Программа завершила работу успешно')
        return 0

    # выводим ошибку, если она возникла
    except StreamStatsError as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
