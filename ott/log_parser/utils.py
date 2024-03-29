from email.policy import default
import hmac
import hashlib
from tkinter.messagebox import NO
from tokenize import Number
import urllib
from dateutil import parser as dateutil_parser

from ott.utils.parse.cmdline import db_cmdline
from ott.utils import file_utils

import logging
log = logging.getLogger(__file__)


def clean_useragent(useragent, fltr=['python-requests/', 'Java/']):
    """ filter / fix up the user agent """
    if useragent is None or len(useragent) < 5:
        ret_val = ""
    elif any(useragent.startswith(f) for f in fltr):
        ret_val = ""
    else:
        ret_val = useragent
    return ret_val


def get_browser(useragent):
    """ return a human-readable string (ala 'Samsung G970U / Android 12 / Chrome 99.1.2') """
    def mk_response(b="", d="", o="", ov="", br="", brv=""):
        return {
            'brand': b,
            'device': d,
            'os': o,
            'os_version': ov,
            'browser': br,
            'browser_version': brv
        }

    ret_val = mk_response()
    try:
        #import pdb; pdb.set_trace()
        import user_agents
        if useragent and len(useragent) > 5:
            ua = user_agents.parse(useragent)
            ret_val = mk_response(
                ua.device.brand,
                ua.device.model,
                ua.os.family,
                ua.os.version_string,
                ua.browser.family,
                ua.browser.version_string
            )
    except Exception as e:
        log.error(e)
    return ret_val


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
    # NOTE: getting rid of timezone, which is messing with the date/time on linux
    #       OLD format with TZ dateutil_parser.parse(dt[:11] + " " + dt[12:])
    return dateutil_parser.parse(dt[:11] + " " + dt[12:20])


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
        # planner_keys = ["plan?", "prod?"]
        planner_keys = ["plan?", "prod?", "/tpws", "/tripplanner"]  # includes initial API calls, which eventually redirect to 'prod?'
        planner_keys = ["plan?", "prod?", "/tpws", "/tripplanner", "/ride/planner.html", "/ride/ws/planner.html"]
        if any(p in url for p in planner_keys):
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


def obfuscate(input, key=u'key'):
    digest = hmac.new(bytearray(key, 'ascii'), input.encode('utf-8'), hashlib.sha1).hexdigest()
    return digest


def cmd_line_loader(prog_name='log_parser/bin/loader', sub_dirs=["maps8", "maps9", "maps10"]):
    parser = db_cmdline.db_parser(prog_name, url_required=False)
    parser.add_argument(
        '--log_directory', '--logs', '-logs', '-l',
        required=True,
        help="Directory of .log files..."
    )
    parser.add_argument(
        '--files', '--ff', '-ff',
        required=False,
        default=".log",
        help="Directory of .log files..."
    )
    cmdline = parser.parse_args()
    files = file_utils.find_files(cmdline.log_directory, cmdline.files, True)
    if len(files) == 0:
        files = file_utils.find_files(cmdline.log_directory, cmdline.files, True, sub_dirs)
    return files, cmdline


def just_name_of_ncoord(named_coord, def_val=None):
    ret_val = def_val
    try:
        s = named_coord
        if "::" in named_coord:
            s = named_coord.split("::")[0]

        if s and len(s) > 0:
            ret_val = s
    except Exception as e:
        log.debug(e)
    return ret_val


def just_lat_lon(named_coord):
    lat = lon = None
    try:
        s = named_coord
        if "::" in named_coord:
            s = named_coord.split("::")[1]

        ll = s.split(",")
        lat = float(ll[0])
        lon = float(ll[1])
    except Exception as e:
        log.debug(e)
    return lat,lon


def is_valid_lat_lon(lat, lon, coord_check=(45.5, -122.6), max_distance_km=300):
    """ checks that a lat, lon contains two values
        plus an optional distance check on said coordinate

        :param coord: is a string in the form of "45.5,-122.5"
        :params coord_check: if not null, used to check distance of coord to coord_check (validity)
        :max_distance_km: how far from coord_check in km (default is region wide 300 km - PDX to Pendelton)        
    """
    ret_val = False
    try:
        #import pdb; pdb.set_trace()
        if lat and lon:
            if coord_check:
                from haversine import haversine, Unit
                if haversine((lat, lon), coord_check, unit=Unit.KILOMETERS) <= max_distance_km:
                    ret_val = True
            else:
                ret_val = True
    except Exception as e:
        log.debug(e)
        ret_val = False
    return ret_val


def append_string(result, string, sep=","):
    """ append string to result, with proper sep """
    ret_val = string
    if result and string not in result:
        ret_val = "{}{}{}".format(result, sep, string)
    return ret_val

def find_proxy_and_target(a, b, localhost='127.0.0.1 "127.0.0.1"'):
    """ find one of records with ip of localhost """
    proxy = target = None
    if localhost == a.log.ip and localhost != b.log.ip:
        proxy = a
        target = b
    elif localhost != a.log.ip and localhost == b.log.ip:
        proxy = b
        target = a
    return proxy,target

def is_mod_planner(url):
    return url.startswith('/otp_mod')


def is_old_trimet(url):
    return url.startswith('/otp_prod') or url.startswith("/ride/ws/planner.html")


def is_old_text_planner(url):
    return url.startswith("/ride/planner.html")


def is_developer_api(url):
    return '/tpws/' in url or "/ride/ws/planner.html" in url


def is_pdx_zoo(url):
    return 'fromPlace=pdx&toPlace=zoo' in url

