from ast import Return
#import imp -- MARCH 7 2026 .. removed this depricated core util (any errors?)
from re import S
from sqlalchemy import Column, String, Boolean, Integer, Float, func, and_
from sqlalchemy.orm import relationship

import json
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
    agencies = Column(String())
    companies = Column(String())  # biketown, uber (eventually lyft), e-scooter company (or companies)

    from_lat = Column(Float())
    from_lon = Column(Float())
    to_lat = Column(Float())
    to_lon = Column(Float())
    ft_stop = Column(String())
    ft_pr = Column(String())
    ft_map = Column(String())
    ft_gps = Column(String())

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
        super(ProcessedRequests, self)
        self.log_id = raw_rec.id
        self.ip_hash = utils.obfuscate(raw_rec.ip)
        self.app_name = self.get_app_name(raw_rec)

        # TODO - refactor, this is a confusing mix of model and controller / parser
        try:
            #import pdb; pdb.set_trace()
            if raw_rec.payload and len(raw_rec.payload) > 20:
                # OTP 2.x (e.g., graphql json response)
                qs = json.loads(raw_rec.payload)
                modes = utils.get_modes_otp2(qs)
                tm_only = False
            else:
                # OTP 1.x (e.g., GET query string)
                qs = utils.get_url_qs(raw_rec.url)
                modes = utils.get_modes_otp1(qs)
                tm_only = True

            self.parse_from(qs)
            self.parse_to(qs)
            self.parse_from_to_metadata(qs)
            self.parse_agencies(qs, tm_only)
            self.parse_modes(modes)
            self.parse_companies(qs)
            self.apply_filters(raw_rec.url)
        except:
            self.filter_request = -111
            log.debug("couldn't parse " + raw_rec.url)

    def apply_filters(self, url, fltval=-222):
        """ filter out uptime test urls, etc... """
        #import pdb; pdb.set_trace()        
        if self.filter_request is None:
            if 'fromPlace=PDX' in url and ('toPlace=ZOO' in url or 'toPlace=SW%20Zoo%20Rd' in url):
                self.filter_request = fltval
            if 'fromPlace=Oregon+Zoo' in url and 'toPlace=2730+NW+Vaughn' in url:
                self.filter_request = fltval + 1
            if '=4001+SW+Canyon+Rd' in url and '=2730+NW+Vaughn' in url:
                self.filter_request = fltval + 2
            if 'fromPlace=45.456406%2C-122.579269' in url and 'toPlace=16380+Boones+Ferry' in url:
                self.filter_request = fltval + 3
            if 'fromPlace=SE+82nd+%26+Johnson+Cr' in url and 'toPlace=45.513954%2C-122.679634' in url:
                self.filter_request = fltval + 4
            if 'fromPlace=1230%20NW%2012TH' in url and 'toPlace=MULTNOMAH%20ATHLETIC%20CLUB' in url:
                self.filter_request = fltval + 5
            if 'fromPlace=S+River+Pkwy' in url and 'toPlace=Gateway+Transit+Center' in url:
                self.filter_request = fltval + 6
            if 'UPTEST' in url or 'UPTIME_TEST' in url:
                self.filter_request = fltval + 7
            if "OLD" in self.app_name:
                if self.modes == "WALK_ONLY" and '%20%26%20' in self.log.url:
                    # note: OLD planner WALK_ONLY trips using 'intersections' are mostly (totally) robots (i.e., search 
                    # engine and Knowlege AI junk). Better solution would be relating OLD app 'proxy' trips to original
                    # traffic and looking at referrer, but that's a TODO item... 
                    self.filter_request = fltval + 8
                    pass
            if self.app_name == TEST_SYSTEM:
                self.filter_request = fltval + 55

    @classmethod
    def get_app_name(cls, rec, def_val="no idea what app..."):
        """ trimet specific -- override me for other agencies / uses """
        app_name = def_val

        tora = "TORA (trimet.org)"
        rtp = "RTP (rtp.trimet.org)"
        call = "CALL (call.trimet.org)"
        call2 = "CALL2 (call.trimet.org)"
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
            if 'localhost:8000' in referer or 'labs' in referer or 'test.trimet' in referer:
                app_name = TEST_SYSTEM
            elif 'call-test' in referer:
                app_name = call2
            elif 'call' in referer:
                app_name = call
            elif 'newplanner' in referer or 'betaplanner' in referer:
                app_name = mod
            elif 'maps.trimet' in referer or 'ride' in referer:
                app_name = imap
            elif 'mobilitymap' in referer:
                app_name = mob
            elif 'trimet.org' in referer or 'beta.trimet.org' in referer:
                app_name = tora

        if utils.is_mod_planner(rec.url):
            app_name = tora
        elif utils.is_old_text_planner(rec.url):
            app_name = oldtxt
        elif utils.is_old_trimet(rec.url):
            app_name = old

        if utils.is_developer_api(rec.url):
            rec.is_api = True
            if app_name is def_val:
                app_name = api

        if rec.browser and len(rec.browser) > 3:
            browser = rec.browser.lower()
            if 'java' in browser:
                app_name = api
            if 'nagios' in browser:
                app_name = test
            if 'python' in browser and utils.is_pdx_zoo(rec.url):
                app_name = test
            if 'pdx%20bus' in browser:
                app_name = pdxbus
                #print(rec.__dict__)
            if 'pdx%20tran' in browser:
                app_name = pdxtransit

        if app_name == def_val:
            #import pdb; pdb.set_trace()
            #print(rec.__dict__)
            pass

        return app_name

    def parse_from(self, qs):
        ret_val = True
        lat,lon = utils.just_lat_lon(qs.get('fromPlace'))
        if utils.is_valid_lat_lon(lat, lon):
            self.from_lat = lat
            self.from_lon = lon
        else:
            #import pdb; pdb.set_trace()
            self.filter_request = -333
            ret_val = False
        return ret_val

    def parse_to(self, qs):
        ret_val = True
        lat,lon = utils.just_lat_lon(qs.get('toPlace'))
        if utils.is_valid_lat_lon(lat, lon):
            self.to_lat = lat
            self.to_lon = lon
        else:
            self.filter_request = -333
            ret_val = False
        return ret_val

    def parse_from_to_metadata(self, qs):
        fm = qs.get('fromPlace')
        to = qs.get('toPlace')

        #import pdb; pdb.set_trace()
        self.ft_gps = utils.parse_ft_metadata(fm, to, "GPS")
        self.ft_stop = utils.parse_ft_metadata(fm, to, "STOP")
        self.ft_pr = utils.parse_ft_pr(fm, to)
        self.ft_map = utils.parse_ft_map(fm, to)

    def parse_agencies(self, qs, tm_only=False):
        """
        return the list of agencies implied in the request
        will look at the banned agencies param, and trim the list of possible request agencies
        """
        tm_map = {
            "TRIMET:TRAM":"Aerial Tram",
            "TRIMET:PSC":"Streetcar",
            "TRIMET:TRIMET":"TriMet",
        }
        rtp_map = {
            "CLACKAMAS":"Clackamas",
            "CTRAN":"C-TRAN",
            "CTRAN_FLEX":"The Current",
            "MULT":"Multnomah",
            "RIDECONNECTION:":"Ride Connection",
            "SAM":"SAM",
            "SMART":"SMART",
            "WASH_FLEX":"SPOT",
            "WAPARK":"Washington Park",
        }
        if tm_only:
            agency_map = tm_map
        else:
            agency_map = tm_map | rtp_map

        # filter banned agencies from the above list
        for b in utils.get_banned_agencies(qs):
            if b in agency_map:
                agency_map.pop(b)
            elif b.split(":")[0] in agency_map:
                agency_map.pop(b.split(":")[0])

        # convert the filtered list to a comma separated string
        self.agencies = ",".join(agency_map.values())

    def parse_modes(self, modes):
        """
        BUS, TRAIN, (GONDOLA, BOAT, etc...), ala transit modes
        [BIKE or BIKE_SHARE] [CAR or CAR_SHARE] [SCOOTER or SCOOTER_SHARE] [RIDE_SHARE]
        or WALK_ONLY or BIKE_ONLY or BIKE_SHARE_ONLY
        """

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

        # step 2: bike - "mode":"BICYCLE","qualifier":"RENT"
        if 'RENT' in modes and 'BICYCLE' in modes:
            self.modes = utils.append_string(self.modes, "BIKE_SHARE")
        elif "BICYCLE_RENT" in modes:
            self.modes = utils.append_string(self.modes, "BIKE_SHARE")
        elif "BICYCLE" in modes:
            self.modes = utils.append_string(self.modes, "BIKE")

        # step 3: shared car
        if "CAR_HAIL" in modes:
            self.modes = utils.append_string(self.modes, "CAR_SHARE")

        # step 4: shared car
        if utils.is_match_any(["MICROMOBILITY_RENT", "SCOOTER_RENT"], modes):
            self.modes = utils.append_string(self.modes, "SCOOTER_SHARE")
        elif utils.is_match_any(["MICROMOBILITY", "SCOOTER"], modes):
            self.modes = utils.append_string(self.modes, "SCOOTER")

        # step 5: walk / bike / etc... only
        if self.modes is None: self.modes = "WALK_ONLY"
        elif self.modes == "BIKE": self.modes = "BIKE_ONLY"
        elif self.modes == "BIKE_SHARE": self.modes = "BIKE_SHARE_ONLY"
        elif self.modes == "BICYCLE_RENT": self.modes = "BIKE_SHARE_ONLY"
        elif self.modes == "SCOOTER": self.modes = "SCOOTER_ONLY"
        elif self.modes == "SCOOTER_SHARE": self.modes = "SCOOTER_SHARE_ONLY"
        #print(modes)

    def parse_companies(self, qs):
        """
        "allowedVehicleRentalNetworks":["lyft_pdx"]
        """
        c = qs.get('companies', [None])[0]
        if c is None:
            c = qs.get("allowedVehicleRentalNetworks", None)
        if c == "NaN":
            c = None
        if c and isinstance(c, list):
            c = ','.join(str(x) for x in c)
        if c and 'lyft_pdx' in c:
            c = c.replace('lyft_pdx', 'BIKETOWN')
        self.companies = c

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
        url = utils.to_url(self.log)

        ret_val = {
            'ip_hash': self.ip_hash,
            'app_name': self.app_name,
            'date': self.log.date,
            'url': url,
            'modes': self.modes,
            'agencies': self.agencies,
            'companies': self.companies,
            'from_lat': self.from_lat,
            'from_lon': self.from_lon,
            'to_lat': self.to_lat,
            'to_lon': self.to_lon,
            'ft_stop': self.ft_stop,
            'ft_pr': self.ft_pr,
            'ft_map': self.ft_map,
            'ft_gps': self.ft_gps,
        }
        ret_val.update(browser)
        return ret_val

    @classmethod
    def process(cls, chunk_size=10000):
        """
        process logs from log file(s)
        """
        session = utils.make_session(False)
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

            session.commit()
        except Exception as e:
            log.exception(e)

    @classmethod
    def post_process(cls):
        """
        post process log junk
        """
        session = utils.make_session(False)
        cls.dedupe(session)
        cls.filter_repeated_bot_requests(session)

    @classmethod
    def dedupe(cls, session):
        try:
            # step 1: dedup requests -- batch into buck of requests by user, then compare URLs for 'sameness'
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
                            if l and l.filter_request is None:
                                #import pdb; pdb.set_trace()
                                if len(l.log.payload) > 10:
                                    if l.log.payload == r.log.payload:
                                        l.filter_request = r.log_id
                                elif l.log.url == r.log.url:
                                    l.filter_request = r.log_id
                            z += 1
                    session.commit()
        except Exception as e:
            log.exception(e)

    @classmethod
    def filter_repeated_bot_requests(cls, session, threshold=30, filter_val=-400):
        """
        OLD planner gets hit hard by random indexing and other bot queries
        """
        cache = {}

        def append_cache(req, qs, param_name="fromPlace"):
            # utils.just_name_of_ncoord(qs.get(param_name)[0])
            pv = qs.get(param_name)[0]
            if pv not in cache: 
                cache[pv] = []
            cache[pv].append(req)

        def cache_hits(req):
            try:
                qs = utils.get_url_qs(req.log.url)
                append_cache(req, qs, 'fromPlace')
                append_cache(req, qs, 'toPlace')
            except Exception as e:
                log.debug(e)

        def set_filters(indx):
            try:
                if len(cache[indx]) >= threshold:
                    #print("{} = {}".format(c, len(cache[indx])))
                    for i, r in enumerate(cache[indx]):
                        if i == 1: continue # don't mark first record
                        r.filter_request = filter_val
                        pass
            except Exception as e:
                log.debug(e)

        try:
            requests = session.query(ProcessedRequests).filter(ProcessedRequests.app_name.like('%OLD%')).filter(ProcessedRequests.filter_request == None).all()
            for r in requests:
                cache_hits(r)

            for c in cache:
                set_filters(c)

            session.commit()
        except Exception as e:
            log.debug(e)


def main():
    from .raw_log import main as raw_load
    raw_load()
    ProcessedRequests.process()
    ProcessedRequests.post_process()


if __name__ == "__main__":
    main()
