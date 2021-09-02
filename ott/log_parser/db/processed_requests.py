from sqlalchemy import Column, String, Integer, DateTime, func
from .base import Base
from .. import utils
from ott.utils import num_utils

import logging
log = logging.getLogger(__file__)


class ProcessedRequests(Base):
    __tablename__ = 'processed_requests'

    ip_hash = Column(String(255), default="unknown")
    request_date = Column(DateTime())
    spread = Column(Integer())

    def __init__(self, rec):
        super(ProcessedRequests, self)
        self.browser = rec['browser']

    @classmethod
    def load(cls, session, chunk_size=10000, do_print=True):
        """
        will find all stop-stop pairs from stop_times/trip data, and create stop-stop segments in the database
        """
        # import pdb; pdb.set_trace()
        try:
            segment_cache = {}

            if segment_cache is None:
                cls.clear_tables(session)

                session.add_all(segment_cache.values())
                session.flush()
                session.commit()
                session.flush()

        except Exception as e:
            log.exception(e)

    @classmethod
    def to_geojson(cls, session):
        """
        """
        pass

def main():
    pass

if __name__ == "__main__":
    main()
