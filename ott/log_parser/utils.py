import urllib
from dateutil import parser as dateutil_parser

import logging
log = logging.getLogger(__file__)


def get_url_qs(url: str):
    u = urllib.parse.urlparse(url)
    ret_val = urllib.parse.parse_qs(u.query)
    return ret_val


def parse_transit_modes(modes: str):
    """
    takes in a mode url param string to OTP
    :returns: dict with transit modes specified https://developers.google.com/transit/gtfs/reference#routestxt
    """
    val = True if modes and 'TRANSIT' in modes else False
    ret_val = {
        'bus': val,
        'aerial_tram': val,
        'light_rail': val,
        'rail': val,
        'subway': val,
        'ferry': val,
        'cablecar': val,
        'trolleybus': val,
        'monorail': val,
        'funicular': val
    }

    if modes and not val:
        if 'BUS' in modes: ret_val['bus'] = True
        if 'TRAM' in modes: ret_val['light_rail'] = True
        if 'RAIL' in modes: ret_val['rail'] = True
        if 'GONDOLA' in modes: ret_val['aerial_tram'] = True
        if 'SUBWAY' in modes: ret_val['subway'] = True
        if 'CABLECAR' in modes: ret_val['cablecar'] = True
        if 'TROLLEYBUS' in modes: ret_val['trolleybus'] = True
        if 'MONORAIL' in modes: ret_val['monorail'] = True
        if 'FUNICULAR' in modes: ret_val['funicular'] = True

    return ret_val


def convert_apache_dt(dt):
    """ break '26/Jan/2021:10:36:23 -0800' into date and time pieces, then parse those as string dateutil"""
    return dateutil_parser.parse(dt[:11] + " " + dt[12:])


def is_match_all(matches: list, string: str):
    """ match all strings from list in str """
    return True if all(x in string for x in matches) else False


def is_match_any(matches: list, string: str):
    """ match at least one string from list in str """
    return True if any(x in string for x in matches) else False


def is_tripplan(url: str, filter_tests=True):
    """ determine if string is an OTP trip request """
    ret_val = False

    # step 0: is valid string
    if url and len(url) > 0:
        # step 1: check that the url looks like a trip plan
        if "plan?" in url:
            ret_val = True

        # step 2: filter urls that 'test' OTP for uptime, etc...
        if ret_val and filter_tests:
            if is_match_all(["834", "SE", "Lambert"], url):
                ret_val = False
            if ret_val is False:
                log.info("filtering: {}".format(url))

    return ret_val


def make_session(create=False, section="db"):
    #url = string_utils.get_val(args.database_url, config.get('database_url'))
    from ott.utils.config_util import ConfigUtil
    from .db.database import Database

    config = ConfigUtil.factory(section=section)
    url = config.get('database_url')
    schema = config.get('schema')
    is_geospatial = config.get('is_geospatial')
    session = Database.make_session(url, schema, is_geospatial, create)
    return session
