"""
stats
"""
from urllib import request
from ott.log_parser.db.processed_requests import ProcessedRequests
from .. import utils

import logging
log = logging.getLogger(__file__)


class Stats(object):
    requests = None
    app_counts = {}
    total_plans = 0
    filtered_plans = 0

    def __init__(self, session):
        self.requests = ProcessedRequests.query(session)
        for r in self.requests:
            if r.app_name in self.app_counts:
                c = self.app_counts[r.app_name]
            else:
                c = {'full': 0, 'filtered': 0}
                self.app_counts[r.app_name] = c

            c['full'] += 1
            self.total_plans += 1
            if r.filter_request is None:
                c['filtered'] += 1
                self.filtered_plans += 1

    def print(self):
        names = sorted(self.app_counts)
        print("Total Requests: {}".format(self.total_plans))
        print("Unique Requests: {}".format(self.filtered_plans))
        for n in names:
            o = self.app_counts[n]
            print("  {:40}: {:6} {:6}".format(n, o['full'], o['filtered']))


def main():
    session = utils.make_session(False)
    s = Stats(session)
    s.print()


if __name__ == "__main__":
    main()
