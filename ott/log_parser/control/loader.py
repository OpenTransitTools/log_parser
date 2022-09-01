from ott.log_parser.control import parser

from ott.log_parser.db.processed_requests import ProcessedRequests
from .. import utils
from ..db.raw_log import RawLog

import logging
logging.basicConfig(level = logging.INFO)
log = logging.getLogger(__file__)


def load_log_file(file, session):
    """ load a log file into the db """
    logs = []
    recs = parser.parse_log_file(file)
    log.info("from file {}, parsed {} number of records".format(file, len(recs)))
    for r in recs:
        rawlog = RawLog(r)
        logs.append(rawlog)
    RawLog.persist_data(session, logs)


def loader():
    #import pdb; pdb.set_trace()
    files, cmdline = utils.cmd_line_loader()
    if len(files) == 0:
        if cmdline.log_directory == "CLEAR":
            utils.make_session(cmdline.create)
        else:
            print("ERROR: {} has no .log files!".format(cmdline.log_directory))
    else:
        session = utils.make_session(cmdline.create)
        for f in files:
            load_log_file(f, session)
    return files, cmdline


def load_and_post_process():
    loader()
    ProcessedRequests.process()
    ProcessedRequests.post_process()


def main():
    loader()


if __name__ == "__main__":
    main()
