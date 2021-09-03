from ott.log_parser.db.processed_requests import ProcessedRequests
from .. import utils
from .loader import loader

import logging
log = logging.getLogger(__file__)


def load_and_post_process():
    loader()
    session = utils.make_session(False)
    ProcessedRequests.process(session)


def main():
    load_and_post_process()


if __name__ == "__main__":
    main()
