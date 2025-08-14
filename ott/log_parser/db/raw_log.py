from sqlalchemy import Column, String, Integer, DateTime, Boolean, func
from .base import Base
from .. import utils
from ott.utils import num_utils

import logging
log = logging.getLogger(__file__)


class RawLog(Base):
    __tablename__ = 'raw_log'

    ip = Column(String(255), default="unknown")  # fk to table with ip -> guid id (share with partners)
    date = Column(DateTime())
    url = Column(String(2084))
    payload = Column(String())
    code = Column(Integer())
    referer = Column(String(2084))
    browser = Column(String(2084))
    is_api = Column(Boolean(), default=False)

    def __init__(self, rec):
        super(RawLog, self)
        self.ip = rec.get('ip', "")
        self.date = utils.convert_apache_dt(rec.get('apache_dt', None))
        self.url = rec.get('url', "")
        self.payload = rec.get('payload', "")
        self.code = num_utils.to_int(rec.get('code', 212), 212)
        self.referer = rec.get('referer', "")
        self.browser = rec.get('browser', "")
        self.is_json = rec.get('is_json', False)
        #import pdb; pdb.set_trace()

def main():
    from ..control.loader import load_log_file
    session = utils.make_session(False)
    load_log_file('docs/test2.log', session)


if __name__ == "__main__":
    main()
