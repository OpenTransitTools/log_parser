from ast import Return
import imp
from sqlalchemy import Column, String, Boolean, Integer, Float, func, and_
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
    related_id = Column(Integer, unique=True, default=None)

    ip_hash = Column(String(255), default="unknown")
    app_name = Column(String(512), default="unknown")

    modes = Column(String())
    companies = Column(String())  # biketown, uber (eventually lyft), e-scooter company (or companies)

    from_lat = Column(Float())
    from_lon = Column(Float())
    to_lat = Column(Float())
    to_lon = Column(Float())

    filter_request = Column(Integer, default=None)

    log = relationship(
        'RawLog',
        primaryjoin='RawLog.id==ProcessedRequests.log_id',
        foreign_keys='(ProcessedRequests.log_id)',
        uselist=False, viewonly=True,
        lazy="joined", innerjoin=True,
    )

    related = relationship(
        'RawLog',
        primaryjoin='RawLog.id==ProcessedRequests.related_id',
        foreign_keys='(ProcessedRequests.related_id)',
        uselist=False, viewonly=True,
    )

    def __init__(self, raw_rec):
        #import pdb; pdb.set_trace()
        super(ProcessedRequests, self)
        self.log_id = raw_rec.id
        self.ip_hash = utils.obfuscate(raw_rec.ip)
        self.app_name = self.get_app_name(raw_rec)

        try:
            qs = utils.get_url_qs(raw_rec.url)
            self.parse_from(qs)
            self.parse_to(qs)
            self.parse_modes(qs)
            self.parse_companies(qs)
            self.apply_filters(raw_rec.url)
        except:
            self.filter_request = -111
            log.debug("couldn't parse " + raw_rec.url)

    def apply_filters(self, url, fltval=-222):
        """ filter out uptime test urls, etc... """
        if self.filter_request is None:
            if 'fromPlace=PDX' in url and ('toPlace=ZOO' in url or 'toPlace=SW%20Zoo%20Rd' in url):
                self.filter_request = fltval
            if 'fromPlace=Oregon+Zoo' in url and 'toPlace=2730+NW+Vaughn' in url:
                self.filter_request = fltval
            if 'fromPlace=4001+SW+Canyon+Rd' in url and 'toPlace=2730+NW+Vaughn' in url:
                self.filter_request = fltval
            if 'toPlace=4001+SW+Canyon+Rd' in url and 'fromPlace=2730+NW+Vaughn' in url:
                self.filter_request = fltval
            if 'fromPlace=45.456406%2C-122.579269' in url and 'toPlace=16380+Boones+Ferry' in url:
                self.filter_request = fltval
            if 'fromPlace=SE+82nd+%26+Johnson+Cr' in url and 'toPlace=45.513954%2C-122.679634' in url:
                self.filter_request = fltval
            if 'fromPlace=1230%20NW%2012TH' in url and 'toPlace=MULTNOMAH%20ATHLETIC%20CLUB' in url:
                self.filter_request = fltval
            if 'fromPlace=S+River+Pkwy' in url and 'toPlace=Gateway+Transit+Center' in url:
                self.filter_request = fltval
            if self.app_name == TEST_SYSTEM:
                self.filter_request = fltval
            if "OLD" in self.app_name and self.modes == "WALK_ONLY":
                # note: OLD planner WALK_ONLY trips are mostly (totally) robots (i.e., search engine and Knowlege AI junk)
                # better solution would be relating OLD app 'proxy' trips to original traffic and looking at referrer 
                self.filter_request = fltval

    @classmethod
    def get_app_name(cls, rec, def_val="no idea what app..."):
        """ trimet specific -- override me for other agencies / uses """
        app_name = def_val

        tora = "TORA (trimet.org)"
        call = "CALL (call.trimet.org)"
        imap = "MAP (maps.trimet.org)"
        mob = "MOBILITY MAP (mobilitymap.trimet.org)"
        mod = "MOD (newplanner.trimet.org)"
        api = "API (developer.trimet.org)"
        old = "OLD (trimet.org planner)"
        oldtxt = "OLD (text planner)"
        pdxbus = "API - PDXBus (developer.trimet.org)"
        pdxtransit = "API - PDXTransit (developer.trimet.org)"
        test = "UPTIME TEST"

        if len(rec.referer) > 3:
            referer = rec.referer.lower()
            if 'call-test' in referer or 'test.trimet' in referer:
                app_name = TEST_SYSTEM
            elif 'call' in referer:
                app_name = call
            elif 'newplanner' in referer or 'betaplanner' in referer:
                app_name = mod
            elif 'maps.trimet' in referer or 'ride' in referer:
                app_name = imap
            elif 'mobilitymap' in referer:
                app_name = mob
            elif 'labs' in referer or 'beta' in referer:
                app_name = tora

        if utils.is_mod_planner(rec.url):
            app_name = tora
        elif utils.is_old_text_planner(rec.url):
            app_name = oldtxt
        elif utils.is_old_trimet(rec.url):
            app_name = old

        if rec.browser and len(rec.browser) > 3:
            browser = rec.browser.lower()
            if 'java' in browser:
                app_name = api
            if 'python' in browser and utils.is_pdx_zoo(rec.url):
                app_name = test
            if 'pdx%20bus' in browser:
                app_name = pdxbus
            if 'pdx%20tran' in browser:
                app_name = pdxtransit

        if utils.is_developer_api(rec.url):
            rec.is_api = True
            if app_name is def_val:
                app_name = api 

        return app_name

    def parse_from(self, qs):
        ret_val = True
        lat,lon = utils.just_lat_lon(qs.get('fromPlace')[0])
        if utils.is_valid_lat_lon(lat, lon):
            self.from_lat = lat
            self.from_lon = lon
        else:        
            self.filter_request = -333
            ret_val = False
        return ret_val

    def parse_to(self, qs):
        ret_val = True
        lat,lon = utils.just_lat_lon(qs.get('toPlace')[0])
        if utils.is_valid_lat_lon(lat, lon):
            self.to_lat = lat
            self.to_lon = lon
        else:        
            self.filter_request = -333
            ret_val = False
        return ret_val

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
        if self.companies and self.companies == "NaN":
            self.companies = None

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

                # step 3: dedup requests -- batch into buck of requests by user, then compare URLs for 'sameness'
                #import pdb; pdb.set_trace()
                n = session.query(ProcessedRequests.ip_hash,  func.count(ProcessedRequests.ip_hash).label("count")).group_by(ProcessedRequests.ip_hash).all()
                for i in n:
                    if i.count > 1:
                        nreqs = session.query(ProcessedRequests).filter(ProcessedRequests.ip_hash == i.ip_hash).all()
                        for m, r in enumerate(nreqs):
                            if r.filter_request is not None:
                                continue
                            z = m+1
                            while z < len(nreqs):
                                l = nreqs[z]
                                if l and l.filter_request is None and l.log.url == r.log.url:
                                    # print(r)
                                    l.filter_request = r.log_id
                                z += 1
                        session.commit()
        except Exception as e:
            log.exception(e)

    def to_csv_dict(self):
        """
            defines the .csv output format
            # todo (adds):
                - dedup count
                - request datetime
                - ???
        """
        ua = utils.clean_useragent(self.log.browser)
        browser = utils.get_browser(ua)

        ret_val = {
            'ip_hash': self.ip_hash,
            'app_name': self.app_name,
            'date': self.log.date,
            'url': self.log.url,
            'modes': self.modes,
            'companies': self.companies,
            'from_lat': self.from_lat,
            'from_lon': self.from_lon,
            'to_lat': self.to_lat,
            'to_lon': self.to_lon
        }
        ret_val.update(browser)
        return ret_val


def main():
    from .raw_log import main as raw_load
    raw_load()
    session = utils.make_session(False)
    ProcessedRequests.process(session)


if __name__ == "__main__":
    main()
