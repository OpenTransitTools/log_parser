"""
stats
"""
from datetime import datetime, timedelta
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
        self.requests = session.query(ProcessedRequests).all()
        for r in self.requests:
            if r.app_name in self.app_counts:
                c = self.app_counts[r.app_name]
            else:
                c = {'full': 0, 'filtered': 0, 'related': 0}
                self.app_counts[r.app_name] = c

            c['full'] += 1
            self.total_plans += 1
            if r.filter_request is None:
                c['filtered'] += 1
                self.filtered_plans += 1
            if r.related:
                c['related'] += 1

    def print(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        now = datetime.today() - timedelta(days=1)  # offset for cron job processing yesterday's data
        names = sorted(self.app_counts)
        print("\n{} {}".format(days[now.weekday()], now.strftime("%B %d, %Y")))
        print("Total Requests:  {}".format(self.total_plans))
        print("Unique Requests: {}\n".format(self.filtered_plans))
        print("  {:40} {:8} {:8} {:8}".format("APP NAME", "    total", "filtered", " related"))
        print("  {:40} {:8} {:8} {:8}".format("--------", "    -----", "--------", " -------"))
        for n in names:
            o = self.app_counts[n]
            print("  {:40}: {:8} {:8} {:8}".format(n, o['full'], o['filtered'], o['related']))
        print()


def main():
    session = utils.make_session(False)
    s = Stats(session)
    s.print()


if __name__ == "__main__":
    main()
