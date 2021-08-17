import enum
from sqlalchemy import Column, String, func
from .base import Base

import logging
log = logging.getLogger(__file__)


class RawLog(Base):
    __tablename__ = 'raw_log'

    url = Column(String(2084))
    modes = Column(String(255), default="")

    def __init__(self, session, log_entry):
        super(RawLog, self).__init__()
        #self.direction = geo_utils.compass(self.bearing)

        if hasattr(self, 'geom'):
            self.make_shapes(session)

    @classmethod
    def load(cls, session, do_trip_segments=True, chunk_size=10000, do_print=True):
        """
        will find all stop-stop pairs from stop_times/trip data, and create stop-stop segments in the database
        """
        # import pdb; pdb.set_trace()
        try:
            segment_cache = {}
            trip_cache = {} if do_trip_segments else None

            if segment_cache is None:
                cls.clear_tables(session)

                printer("There are {:,} stop to stop segments".format(len(segment_cache)), do_print=do_print)
                session.add_all(segment_cache.values())
                session.flush()
                session.commit()
                session.flush()

                # step 3: write the stop_segment_trip data to db
                if trip_cache and len(trip_cache) > 0:
                    segment_trip_cache = list(trip_cache.values())
                    printer("and {:,} trips cross these segments".format(len(segment_trip_cache)), do_print=do_print)
                    for i in range(0, len(segment_trip_cache), chunk_size):
                        chunk = segment_trip_cache[i:i + chunk_size]
                        printer('.', end='', flush=True, do_print=do_print)
                        session.bulk_save_objects(chunk)

        except Exception as e:
            log.exception(e)

    @classmethod
    def query_segments(cls, session, limit=None):
        q = session.query(StopSegment).order_by(StopSegment.id)
        if limit and type(limit) is int:
            segments = q.limit(limit)
        else:
            segments = q.all()
        return segments

    @classmethod
    def to_geojson(cls, session):
        """
        override the default to_geojson
        {
          "type": "FeatureCollection",
          "features": [
            {"type":"Feature", "properties":{"id":"1-2"}, "geometry":{"type":"LineString","coordinates":[[-122.677388,45.522879],[-122.677396,45.522913]]}},
            {"type":"Feature", "properties":{"id":"2-3"}, "geometry":{"type":"LineString","coordinates":[[-122.675715,45.522215],[-122.67573,45.522184]]}},
          ]
        }
        """
        feature_tmpl = '    {{"type": "Feature", "properties": {{' \
                       '"id": "{}", ' \
                       '"code": "{}", ' \
                       '"info": "{}", ' \
                       '"layer": "{}" ' \
                       '}}, "geometry": {}}}{}'

        stop_cache ={}
        stops = session.query(Stop.stop_id, Stop.geom.ST_AsGeoJSON()).all()
        for s in stops:
            stop_cache[s[0]] = s[1]

        # import pdb; pdb.set_trace()
        features = session.query(StopSegment).all()
        ln = len(features) - 1
        featgeo = ""
        last_stop = "xxx"
        for i, f in enumerate(features):
            geom = session.scalar(func.ST_AsGeoJSON(f.geom))
            if last_stop != f.begin_stop_id:
                featgeo += feature_tmpl.format(f.begin_stop_id, f.begin_stop_code, "", "stop", stop_cache[f.begin_stop_id], ",\n")
            featgeo += feature_tmpl.format(f.id, f.code_id, f.direction, "stop", geom, ",\n")
            for t in f.traffic_segment:
                tgeo = session.scalar(func.ST_AsGeoJSON(t.geom))
                featgeo += feature_tmpl.format(t.traffic_segment_id, t.traffic_segment_id + " (" + f.code_id + ")", t.direction, "traffic", tgeo, ",\n")
            comma = ",\n" if i < ln else "\n"  # don't add a comma to last feature
            featgeo += feature_tmpl.format(f.end_stop_id, f.end_stop_code, "", "stop", stop_cache[f.end_stop_id], comma)
            last_stop = f.end_stop_id

        geojson = '{{\n  "type": "FeatureCollection",\n  "features": [\n{}  ]\n}}'.format(featgeo)
        return geojson


# todo: make util ... py2 and py3
def printer(content, end='\n', flush=False, do_print=True):
   if do_print:
       #pass #print(content, end=end, flush=flush)
       print(content)


def main():
    from ott.log_parser.control import parser
    from .. import utils

    file="docs/test2.log"
    recs = parser.parse_log_file(file)
    print(recs)

    dt =  utils.convert_apache_dt(recs[0].get('apache_dt'))
    print(dt.timestamp())

    qs = utils.get_url_qs(recs[0]['url'])
    m = parser.parse_modes(qs)
    print(m)


if __name__ == "__main__":
    main()

