from sqlalchemy import Column, String, Boolean, Integer, DateTime, func
from sqlalchemy.orm import deferred, relationship

from .. import utils
from .base import Base
from .raw_log import RawLog

import logging
log = logging.getLogger(__file__)


class ProcessedRequests(Base):
    __tablename__ = 'processed_requests'

    log_id = Column(Integer, unique=True, index=True)

    ip_hash = Column(String(255), default="unknown")
    app_name = Column(String(512), default="unknown")

    request_date = Column(DateTime())
    is_now_request = Column(Boolean(), default=True)
    filter_request = Column(Boolean(), default=False)

    raw_logs = relationship(
        'RawLog',
        primaryjoin='RawLog.id==ProcessedRequests.log_id',
        foreign_keys='(ProcessedRequests.log_id)',
        uselist=False, viewonly=True,
        lazy="joined", innerjoin=True,
    )

    def __init__(self, raw_rec):
        super(ProcessedRequests, self)
        self.log_id = raw_rec.id
        self.ip_hash = utils.obfuscate(raw_rec.ip)
        self.app_name = self.get_app_name(raw_rec.referer, raw_rec.browser)

    @classmethod
    def get_app_name(cls, referer, browser = None, def_val = "trimet.org / maps.trimet.org"):
        """ trimet specific -- override me for other agencies / uses """
        app_name = def_val
        if len(referer) > 3:
            if 'call-test' in referer or 'test.trimet' in referer:
                app_name = "test system"
            elif 'call' in referer:
                app_name = "call taker app"
            elif 'labs' in referer or 'beta' in referer:
                app_name = "TORA (new trimet.org)"
            elif 'maps.trimet' in referer or 'ride' in referer:
                app_name = "Interactive Map - ride.trimet.org"
            elif 'mobilitymap' in referer:
                app_name = "Mobility Map - mobilitymap.trimet.org"
            elif 'trimet' in referer:
                app_name = "Homepage - trimet.org"

        if browser and len(browser) > 3:
            if 'pdx bus' in browser.lower():
                app_name = "PDX Bus"
            elif 'trimet' in browser:
                app_name = "xxxxx"

        return app_name

    @classmethod
    def load(cls, session, chunk_size=10000):
        """
        will post-process
        """
        # import pdb; pdb.set_trace()
        try:
            logs = RawLog.query(session)
            if logs and len(logs) > 0:
                processed = []
                ProcessedRequests.clear_table(session)
                for l in logs:
                    p = ProcessedRequests(l)
                    processed.append(p)
                    if len(processed) > chunk_size:
                        ProcessedRequests.persist_data(session, processed)
                        processed = []
                ProcessedRequests.persist_data(session, processed)
        except Exception as e:
            log.exception(e)


def main():
    from .raw_log import main as raw_load
    raw_load()
    session = utils.make_session(False)
    ProcessedRequests.load(session)


if __name__ == "__main__":
    main()
