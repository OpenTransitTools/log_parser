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

    fmt='{ip} - - [{apache_dt}] "{meth} {url} {http}" {code} {size} "{referer}" "{browser}"\n'
    for parsed_record in from_log(file, fmt):
        rec = parsed_record.named
        if rec and utils.is_tripplan(rec.get('url')):
            ret_val.append(rec)

    return ret_val


def parse_companies(qs: dict):
    companies = qs.get('companies', [None])[0]


def parse_shared_modes(ret_val: dict, modes: str):
    has_mod = False
    if 2 == 2:
        # todo ... general check for mod mods and companies
        has_mod = True

        if 'BIKESHARE' in modes: ret_val['bike_rental'] = True
        if 'RIDESHARE' in modes: ret_val['rideshare'] = True
        if 'CARSHARE' in modes: ret_val['carshare'] = True
        if 'SCOOTER' in modes: ret_val['scooter_rental'] = True

    return has_mod


def parse_modes(qs: dict):
    ret_val = {
        'walk': False,
        'bike': False,
        'bike_rental': False,
        'scooter_rental': False,
        'rideshare': False,
        'carshare': False,
    }

    #import pdb; pdb.set_trace()
    modes = qs.get('mode', [None])[0]
    ret_val.update(utils.parse_transit_modes(modes))

    if 'WALK' in modes: ret_val['walk'] = True
    if 'BIKE' in modes: ret_val['bike'] = True

    has_mod = parse_shared_modes(ret_val, modes)

    return ret_val


def main():
    file="docs/test2.log"
    recs = parse_log_file(file)
    #print(recs)

    dt =  utils.convert_apache_dt(recs[0].get('apache_dt'))
    print(dt.timestamp())

    ip = recs[0]['ip']
    ip_obf = utils.obfuscate(ip)
    print(ip)
    print(ip_obf)

    qs = utils.get_url_qs(recs[0]['url'])
    m = parse_modes(qs)
    m['user'] = ip_obf
    print(m)


if __name__ == "__main__":
    main()
