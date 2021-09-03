from sqlalchemy import Column, String, Boolean, Integer, Float
from sqlalchemy.orm import relationship

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

    modes = Column(String())
    companies = Column(String())  # biketown, uber (eventually lyft), e-scooter company (or companies)

    from_lat_lon = Column(String())
    to_lat_lon = Column(String())

    filter_request = Column(Boolean(), default=False)

    log = relationship(
        'RawLog',
        primaryjoin='RawLog.id==ProcessedRequests.log_id',
        foreign_keys='(ProcessedRequests.log_id)',
        uselist=False, viewonly=True,
        lazy="joined", innerjoin=True,
    )

    def __init__(self, raw_rec):
        #import pdb; pdb.set_trace()
        super(ProcessedRequests, self)
        self.log_id = raw_rec.id
        self.ip_hash = utils.obfuscate(raw_rec.ip)
        self.app_name = self.get_app_name(raw_rec.referer, raw_rec.browser)
        if self.app_name == TEST_SYSTEM:
            self.filter_request = True

        try:
            qs = utils.get_url_qs(raw_rec.url)
            self.parse_from(qs)
            self.parse_to(qs)
            self.parse_modes(qs)
            self.parse_companies(qs)
        except:
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

    def parse_from(self, qs):
        self.from_lat_lon = utils.just_lat_lon(qs.get('fromPlace')[0])

    def parse_to(self, qs):
        self.to_lat_lon = utils.just_lat_lon(qs.get('toPlace')[0])

    def parse_modes(self, qs):
        """
           BUS, TRAIN, (GONDOLA, BOAT, etc...), ala transit modes
           [BIKE or BIKE_SHARE] [CAR or CAR_SHARE] [SCOOTER or SCOOTER_SHARE] [RIDE_SHARE]
           or WALK_ONLY or BIKE_ONLY or BIKE_SHARE_ONLY
        """
        modes = qs.get('mode')[0].upper().strip()

        # step 1: handle transit modes ... distilled down to just BUS,TRAIN (note order important)
        if "BUS" in modes:
            self.modes = utils.append_string(self.modes, "BUS")
        if "TRANSIT" in modes:
            self.modes = utils.append_string(self.modes, "BUS")
            self.modes = utils.append_string(self.modes, "RAIL")
        if utils.is_match_any(["RAIL", "SUBWAY", "TRAIN", "TRAM", "GONDOLA"], modes):
            self.modes = utils.append_string(self.modes, "RAIL")
        if "CAR_PARK" in modes:
            self.modes = utils.append_string(self.modes, "CAR")  # Drive to Park & Ride

        # step 2: bike
        if "BICYCLE_RENT" in modes:
            self.modes = utils.append_string(self.modes, "BIKE_SHARE")
        elif "BICYCLE" in modes:
            self.modes = utils.append_string(self.modes, "BIKE")

        # step 3: shared modes
        if "CAR_HAIL" in modes:
            self.modes = utils.append_string(self.modes, "CAR_SHARE")
        if "MICROMOBILITY_RENT" in modes:
            self.modes = utils.append_string(self.modes, "SCOOTER_SHARE")
        elif "MICROMOBILITY" in modes:
            self.modes = utils.append_string(self.modes, "SCOOTER")

        # step 4: walk / bike / etc... only
        if self.modes is None: self.modes = "WALK_ONLY"
        elif self.modes == "BIKE": self.modes = "BIKE_ONLY"
        elif self.modes == "BIKE_SHARE": self.modes = "BIKE_SHARE_ONLY"
        elif self.modes == "SCOOTER": self.modes = "SCOOTER_ONLY"
        elif self.modes == "SCOOTER_SHARE": self.modes = "SCOOTER_SHARE_ONLY"

    def parse_companies(self, qs):
        self.companies = qs.get('companies', [None])[0]
        if self.companies:
            self.companies = self.companies.strip("NaN")

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

    def to_csv_dict(self):
        ret_val = {
            'ip_hash': self.ip_hash,
            'app_name': self.app_name,
            'url': self.log.url,
            'date': self.log.date,
            'modes': self.modes,
            'companies': self.companies,
            'from': self.from_lat_lon,
            'to': self.to_lat_lon
        }
        return ret_val


def main():
    from .raw_log import main as raw_load
    raw_load()
    session = utils.make_session(False)
    ProcessedRequests.process(session)


if __name__ == "__main__":
    main()
