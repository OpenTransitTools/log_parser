from collections import Counter
from ott.utils.parse.cmdline.base_cmdline import file_cmdline
from ott.utils import file_utils

import logging
log = logging.getLogger(__file__)


def modes_plus_agencies(prog_name='poetry run view_csv', file_name='trip_requests.csv'):
    cmdline = file_cmdline(prog_name, file_name)
    print(f"{cmdline.file}")

    data = []
    for r in file_utils.read_csv(cmdline.file):
        companies = r.get('agencies').strip()
        sep = " -> " if len(companies) > 1 else "(COULDN'T PLAN TRIP) "
        data.append(f"{companies}{sep}{r.get('modes')}")
    counts = Counter(data)
    for s in sorted(counts.items()):
        print(f"{s[1]:8} {s[0]}")

    return 0
