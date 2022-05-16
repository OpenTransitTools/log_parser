"""
  Will read log_parser report .json data, and work to sort and catogrize based on user and place
"""
from enum import unique
import os
from urllib import request
from ott.utils import file_utils
from .. import utils


class Requestor(object):
    id=None

    def __init__(self, id: str):
        self.id = id
        self.requests=[]

    def add_req(self, req):
        #import pdb; pdb.set_trace()
        self.requests.append(req)
        return True

    def num(self):
        return len(self.requests)


class RequestorList(object):
    requestors={}

    def __init__(self, file: os.PathLike):
        #import pdb; pdb.set_trace()
        self.recs = file_utils.make_csv_reader(file)
        self._sort_requests()

    def _sort_requests(self):
        for r in self.recs:
            id = r['ip_hash']
            req = self.requestors.get(id)
            if req is None:
                req = Requestor(id)
                self.requestors[id] = req
            req.add_req(r)
    
    def list(self):
        return self.requestors.values()

def main():
    file="docs/test_report.csv"
    rl = RequestorList(file)
    for r in rl.list():
        print("{} -> {} requests".format(r.id, r.num()))


if __name__ == "__main__":
    main()
