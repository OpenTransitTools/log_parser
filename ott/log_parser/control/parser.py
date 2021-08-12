import datetime
import logging
import os
from pathlib import Path
from boltons.tbutils import ParsedException
from parse import parse, with_pattern


LOGGING_DEFAULT_DATEFMT = f"{logging.Formatter.default_time_format},%f"

"""
https://stackoverflow.com/questions/30627810/how-to-parse-this-custom-log-file-in-python/67607375#67607375
"""

@with_pattern(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d")
def asctime_time(raw):
    return datetime.datetime.strptime(raw, LOGGING_DEFAULT_DATEFMT)

@with_pattern(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d")
def log_time(raw):
    return datetime.datetime.strptime(raw, LOGGING_DEFAULT_DATEFMT)

@with_pattern(r"\d\d\d\.\d\d\.\d\d\d\.\d\d")
def ip_address(raw):
    return raw


def from_log(file: os.PathLike, fmt: str):
    chunk = ""
    custom_parsers = {
        "asctime": log_time

    }

    with Path(file).open() as fp:
        for line in fp:
            parsed = parse(fmt, line)
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
    # 172.25.102.10 "172.25.102.10" - - [26/Jan/2021:10:36:23 -0800] "GET /?sessionId=poeueeq6sokun2134stk607dki HTTP/1.1" 200 2972 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
    fmt="{asctime:asctime} - {module} - {levelname} - {message}"  # test.log (example)
    fmt='{ip_a} "{ip_b}" - - [{date}] "{meth} {url} {http}" {code} {size} "{referer}" "{browser}"\n'
    for parsed_record in from_log(file="docs/test2.log", fmt=fmt):
        print(parsed_record)


if __name__ == "__main__":
    main()

