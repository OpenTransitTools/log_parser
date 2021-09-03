from ott.log_parser.control import parser
from ott.utils.parse.cmdline import db_cmdline
from ott.utils import file_utils

from .. import utils
from ..db.raw_log import RawLog


def load_log_file(file, session):
    """ load a log file into the db """
    logs = []
    recs = parser.parse_log_file(file)
    for r in recs:
        log = RawLog(r)
        logs.append(log)

    session.add_all(logs)
    session.commit()
    session.flush()
