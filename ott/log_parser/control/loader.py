from ott.log_parser.control import parser
from ott.log_parser.control import parser_modsec

from ott.log_parser.db.processed_requests import ProcessedRequests
from .. import utils
from ..db.raw_log import RawLog

import logging
logging.basicConfig(level = logging.INFO)
log = logging.getLogger(__file__)


def load_log_file(file, session):
    """ load a log file into the db """
    try:
        recs = parser.parse_log_file(file)
    except:
        recs = None
    if recs is None or len(recs) == 0:
        # with no recs from first parser, maybe this is a mod_security file containing trip plans
        #import pdb; pdb.set_trace()
        recs = parser_modsec.parse_log_file(file)

    if recs and len(recs) > 0:
        log.info("from file {}, parsed {} number of records".format(file, len(recs)))
        logs = []
        for r in recs:
            rawlog = RawLog(r)
            logs.append(rawlog)
        RawLog.persist_data(session, logs)


def loader():
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
