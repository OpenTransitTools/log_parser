"""
  Will read log_parser report .json data, and work to sort and catogrize based on user and place

  Measures:
   - requests with the same start and end lat,log coordinates
   - reversed end and start coordinates
   - same user id (won't work for proxy'd requests ala otp_prod)
   - elapsed time between requests
   - filter out 'uptime' checks using PDX->ZOO as coords from counts, etc...
"""
from concurrent.futures import process
from enum import unique
import os
import sys
from time import process_time
from urllib import request
from ott.utils import file_utils
from ott.utils import date_utils
from ott.utils import object_utils
from ott.utils.parse.cmdline.base_cmdline import file_cmdline

from .. import utils


class SimilarRequests(object):

    # number of repeated trips
    repeats = None
    reverse = None

    def __init__(self, ):
        self.requests=[]


class Requestor(object):
    """
    request obj = ip_hash,app_name,url,date,modes,companies,from,to
    """
    id=None
    requests=None

    # time between requests
    min_time = sys.maxsize
    max_time = 0.0
    avg_time = 0.0

    # app counts
    tot_tora = 0
    valid_tora = 0
    tot_old = 0
    valid_old = 0

    def __init__(self, id: str):
        self.id = id
        self.requests=[]

    def add_req(self, req):
        #import pdb; pdb.set_trace()
        self.requests.append(req)
        return True

    def num(self):
        return len(self.requests)

    def process_time(self):
        """
        calculate times for this batch of stuff
        """
        prev = None
        tot = 0.0
        cnt = 0

        # calculate shortest (min_time) and longest (max_time) time between requests
        for r in self.requests:
            if prev is not None:
                pt = date_utils.parse_datetime_seconds(prev.get('date'))
                rt = date_utils.parse_datetime_seconds(r.get('date'))
                t = rt - pt
                tot += t
                cnt += 1
                if t < self.min_time:
                    self.min_time = t
                if t > self.max_time:
                    self.max_time = t
            prev = r
        
        # calculate avg
        if cnt > 0:
            self.avg_time = tot / cnt
        else:
            self.min_time = 0.0

    def process_counts(self):
        for r in self.requests:
            url = r.get('url')
            if url.startswith('/otp_mod'):
                self.tot_tora += 1
            elif url.startswith('/otp_prod'):
                self.tot_old += 1

    def process(self):
        self.process_time()
        self.process_counts()

    def print_str(self):
        ret_val = "{} {} {} -- {} {}".format(self.min_time, self.max_time, self.avg_time, self.tot_tora, self.tot_old)
        return ret_val

class RequestorList(object):
    requestors={}

    def __init__(self, file: os.PathLike):
        #import pdb; pdb.set_trace()
        self.recs = file_utils.make_csv_reader(file)
        self._sort_requests()
        self._process_requests()

    def _sort_requests(self):
        for r in self.recs:
            id = r['ip_hash']
            req = self.requestors.get(id)
            if req is None:
                req = Requestor(id)
                self.requestors[id] = req
            req.add_req(r)

    def _process_requests(self):
        for r in self.list():
            r.process()
    
    def list(self):
        return self.requestors.values()

    def print(self):
        for r in self.list():
            print("{} -> {} requests - {}".format(r.id, r.num(), r.print_str()))


def main():
    cmd = file_cmdline("bin/reporter", "docs/test_report.csv")
    rl = RequestorList(cmd.file)
    rl.print()


if __name__ == "__main__":
    main()
