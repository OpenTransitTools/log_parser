from dateutil import parser as dateutil_parser

import logging
log = logging.getLogger(__file__)


def convert_apache_dt(dt):
    """ break '26/Jan/2021:10:36:23 -0800' into date and time pieces, then parse those as string dateutil"""
    return dateutil_parser.parse(dt[:11] + " " + dt[12:])


def is_match_all(matches: list, string: str):
    """ match all strings from list in str """
    return True if all(x in string for x in matches) else False


def is_match_any(matches: list, string: str):
    """ match at least one string from list in str """
    return True if any(x in string for x in matches) else False


def is_tripplan(url, filter_tests=True):
    """ determine if string is an OTP trip request """
    ret_val = False

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

