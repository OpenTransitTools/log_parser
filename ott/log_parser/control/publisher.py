from ott.utils import file_utils
from .. import utils
from ott.log_parser.db.processed_requests import ProcessedRequests

import logging
log = logging.getLogger(__file__)


def csv(file_path, chunk_size=10000):
    session = utils.make_session(False)
    requests = session.query(ProcessedRequests).order_by(ProcessedRequests.ip_hash, ProcessedRequests.log_id).all()
    if requests and len(requests) > 0:
        fieldnames = requests[0].to_csv_dict().keys()
        with open(file_path, mode='w') as csv_file:
            csv = file_utils.make_csv_writer(csv_file, fieldnames)
            for r in requests:
                if not r.filter_request:
                    csv.writerow(r.to_csv_dict())


def main():
    csv("trip_requests.csv")


if __name__ == "__main__":
    main()
