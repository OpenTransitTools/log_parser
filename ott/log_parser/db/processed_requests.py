from sqlalchemy import Column, String, Boolean, Integer, DateTime, func
from sqlalchemy.orm import deferred, relationship

from .. import utils
from .base import Base
from .raw_log import RawLog

import logging
log = logging.getLogger(__file__)

TEST_SYSTEM="test system"


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
        if self.app_name == TEST_SYSTEM:
            self.filter_request = True

    @classmethod
    def get_app_name(cls, referer, browser = None, def_val = "Homepage (trimet.org)"):
        """ trimet specific -- override me for other agencies / uses """
        app_name = def_val
        if len(referer) > 3:
            if 'call-test' in referer or 'test.trimet' in referer:
                app_name = TEST_SYSTEM
            elif 'call' in referer:
                app_name = "CALL (call.trimet.org)"
            elif 'newplanner' in referer or 'betaplanner' in referer:
                app_name = "MOD (newplanner.trimet.org)"
            elif 'labs' in referer or 'beta' in referer:
                app_name = "TORA (new trimet.org)"
            elif 'maps.trimet' in referer or 'ride' in referer:
                app_name = "iMap (ride.trimet.org)"
            elif 'mobilitymap' in referer:
                app_name = "Mobility Map (mobilitymap.trimet.org)"
            elif 'trimet' in referer:
                app_name = def_val

        if browser and len(browser) > 3:
            if 'Java' in browser:
                app_name = "API (developer.trimet.org)"
            elif 'pdx%20bus' in browser.lower():
                app_name = "PDX Bus (developer.trimet.org)"
            elif 'trimet' in browser:
                app_name = def_val

        return app_name

    @classmethod
    def process(cls, session, chunk_size=10000):
        """
        will post-process
        """
        # import pdb; pdb.set_trace()
        try:
            logs = RawLog.query(session)
            if logs and len(logs) > 0:
                # step 1: clear out processed table
                ProcessedRequests.clear_table(session)

                # step 2: loop thru raw log file entries
                processed = []
                for l in logs:
                    p = ProcessedRequests(l)
                    processed.append(p)
                    # step 2b: save off the post-process data in 'chunks'
                    if len(processed) > chunk_size:
                        ProcessedRequests.persist_data(session, processed)
                        processed = []

                # step 2c: save off the any remaining data from the last 'chunk'
                ProcessedRequests.persist_data(session, processed)
        except Exception as e:
            log.exception(e)


def main():
    from .raw_log import main as raw_load
    raw_load()
    session = utils.make_session(False)
    ProcessedRequests.process(session)


if __name__ == "__main__":
    main()
