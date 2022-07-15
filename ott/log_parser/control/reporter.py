"""
  Will read log_parser report .json data, and work to sort and catogrize based on user and place

  Measures:
   - requests with the same start and end lat,log coordinates
   - reversed end and start coordinates
   - same user id (won't work for proxy'd requests ala otp_prod)
   - elapsed time between requests
   - filter out 'uptime' checks using PDX->ZOO as coords from counts, etc...

  Ideas:
   - number of unique customers per app
   - 

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
    id = None
    requests = None
    count = 0

    def __init__(self, id):
        self.id = id
        self.requests = []

    @classmethod
    def make_id(self, request):
       return "{}::{}".format(request.get('from'), request.get('to'))

    @classmethod
    def is_common(cls, request_a, request_b):
        return (
            request_a.get('from') == request_b.get('from') 
            or request_a.get('to') == request_b.get('to')
            or request_a.get('from') == request_b.get('to') 
            or request_a.get('to') == request_b.get('from') 
        )

    @classmethod
    def is_same(cls, request_a, request_b):
        return request_a.get('from') == request_b.get('from') and request_a.get('to') == request_b.get('to')

    @classmethod
    def is_reverse(cls, request_a, request_b):
        return request_a.get('from') == request_b.get('to') and request_a.get('to') == request_b.get('from')

    @classmethod
    def factory(cls, request, cache):
        id = cls.make_id(request)
        c = None
        if id not in cache:
            c = SimilarRequests(id)
            cache[id] = c
        else:
            c = cache[id]
        c.count += 1
        return None


class Requestor(object):
    """
    request obj = ip_hash,app_name,url,date,modes,companies,from,to
    """
    id=None
    similars=None

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

    def num_sims(self):
        ret_val = []
        if self.similars:
             # import pdb; pdb.set_trace()
             for s in self.similars.values():
                ret_val.append(s.count)
        else:
            ret_val.append(1)
        return ret_val

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
            if utils.is_mod_planner(url):
                self.tot_tora += 1
            elif utils.is_old_text_planner(url):
                self.tot_old += 1

    def process_similars(self):
        if self.num() > 1:
            self.similars={}
            for r in self.requests:
                SimilarRequests.factory(r, self.similars)

    def process(self):
        self.requests = sorted(self.requests, key=lambda k: k['date'])
        self.process_time()
        self.process_counts()
        self.process_similars()

    def print_str(self):
        ret_val = "{} {} {} -- {} {} - {}".format(self.min_time, self.max_time, self.avg_time, self.tot_tora, self.tot_old, self.num_sims())
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
