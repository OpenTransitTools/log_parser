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


def loader():
    parser = db_cmdline.db_parser('log_parser', url_required=False)
    parser.add_argument(
        '--logs', '-logs', '-l',
        required=True,
        help="Directory of .log files..."
    )
    cmdline = parser.parse_args()
    session = utils.make_session(cmdline.create)
    files = file_utils.find_files(cmdline.logs, ".log", True)

    #import pdb; pdb.set_trace()
    for f in files:
        load_log_file(f, session)


def main():
    loader()

if __name__ == "__main__":
    main()
