"""
  Will parse Apache log file, looking for requests to the OpenTripPlanner (OTP)

  :note: individual log entries look like this string
   172.25.102.10 "172.25.102.10" - - [26/Jan/2021:10:36:23 -0800] "GET /?sessionId=blah HTTP/1.1" 200 2972 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"

  :see: https://stackoverflow.com/questions/30627810/how-to-parse-this-custom-log-file-in-python/67607375#67607375
"""
import os
from pathlib import Path
from parse import parse

from .. import utils


def from_log(file: os.PathLike, fmt: str):
    """ return each entry in the file as a dict """
    with Path(file).open() as fp:
        for line in fp:
            parsed = parse(fmt, line)
            if parsed is not None:
                yield parsed


def parse_log_file(file: os.PathLike):
    ret_val = []

    fmt='{ip_a} "{ip_b}" - - [{apache_dt}] "{meth} {url} {http}" {code} {size} "{referer}" "{browser}"\n'
    for parsed_record in from_log(file, fmt):
        if utils.is_tripplan(parsed_record['url']):
            rec = parsed_record.named
            ret_val.append(rec)

    return ret_val


def main():
    file="docs/test2.log"
    recs = parse_log_file(file)
    print(recs)

    dt =  utils.convert_apache_dt(recs[0]['apache_dt'])
    print(dt.timestamp())



if __name__ == "__main__":
    main()

