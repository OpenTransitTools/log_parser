import datetime
import logging
import os
from pathlib import Path
from boltons.tbutils import ParsedException
from parse import parse, with_pattern


LOGGING_DEFAULT_DATEFMT = f"{logging.Formatter.default_time_format},%f"

"""
https://stackoverflow.com/questions/30627810/how-to-parse-this-custom-log-file-in-python
"""

# TODO better pattern
@with_pattern(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d")
def parse_logging_time(raw):
    return datetime.datetime.strptime(raw, LOGGING_DEFAULT_DATEFMT)


def from_log(file: os.PathLike, fmt: str):
    chunk = ""
    custom_parsers = {"asctime": parse_logging_time}

    with Path(file).open() as fp:
        for line in fp:
            parsed = parse(fmt, line, custom_parsers)
            if parsed is not None:
                yield parsed
            else:  # try parsing the stacktrace
                chunk += line
                try:
                    yield ParsedException.from_string(chunk)
                    chunk = ""
                except (IndexError, ValueError):
                    pass


def main():
    for parsed_record in from_log(file="docs/test.log", fmt="{asctime:asctime} - {module} - {levelname} - {message}"):
        print(parsed_record)


if __name__ == "__main__":
    main()

