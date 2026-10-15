import argparse
import sys
from pathlib import Path

from streamstats.analysis import analyze_events, create_analysis_result_object
from streamstats.errors import StreamStatsError
from streamstats.models import SkippedEventsCount
from streamstats.parsers import parse_csv, parse_jsonl
from streamstats.report import build_dict, write_report_json

ROOT = Path(__file__).resolve().parents[2]


def main():
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

                    if args.format == 'jsonl':
                        if path.suffix != '.jsonl':
                            raise StreamStatsError(f'Файл {path} не имеет расширения .jsonl')

                        iterator = parse_jsonl(
                            path=path,
                            path_number=path_number,
                            skipped_events=skip_events_count,
                            skip_invalid=args.skip_invalid
                        )
                    elif args.format == 'csv':
                        if path.suffix != '.csv':
                            raise StreamStatsError(f'Файл {path} не имеет расширения .csv')
                        iterator = parse_csv(
                            path=path,
                            path_number=path_number,
                            skipped_events=skip_events_count,
                            skip_invalid=args.skip_invalid
                        )
                    else:
                        raise StreamStatsError(f'Неизвестный тип файла: {args.format}')

                    analyze_events(
                        analysis_result=analysis_result,
                        events=iterator
                    )

                except FileNotFoundError as error:
                    raise StreamStatsError(f'Файл {path} не найден') from error

            report = build_dict(
                result=analysis_result,
                skipped_events=skip_events_count
            )

            output_path = Path(args.output_path)

            write_report_json(
                report=report,
                output_path=output_path
            )

        else:
            parser.print_help()

        return 0

    except StreamStatsError as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
