from ott.log_parser.control import parser

from ott.log_parser.db.processed_requests import ProcessedRequests
from .. import utils
from ..db.raw_log import RawLog


def load_log_file(file, session):
    """ load a log file into the db """
    logs = []
    recs = parser.parse_log_file(file)
    for r in recs:
        log = RawLog(r)
        logs.append(log)
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
    session = utils.make_session(False)
    ProcessedRequests.process(session)


def main():
    loader()


if __name__ == "__main__":
    main()
