import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'sqlalchemy',
    'geoalchemy2',
    'zope.sqlalchemy',
    'psycopg2-binary',
    'boltons',
    'parse',
    'python-dateutil',
    'ott.utils'
]

extras_require = dict(
    dev=[],
)


setup(
    name='ott.log_parser',
    version='0.1.0',
    description='Open Transit Tools - parse server log files / OTP trip plan urls',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
    ],
    author="Open Transit Tools",
    author_email="info@opentransittools.org",
    dependency_links=[
        'git+https://github.com/OpenTransitTools/utils.git#egg=ott.utils-0.1.0',
    ],
    license="Mozilla-derived (http://opentransittools.com)",
    url='http://opentransittools.com',
    keywords='ott, osm, otp, gtfs, vector, tiles, maps, transit',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require=extras_require,
    tests_require=requires,
    test_suite="ott.log_parser.tests",
    entry_points="""
        [console_scripts]
        test_load = ott.log_parser.db.raw_log:main
        test_process = ott.log_parser.db.processed_requests:main
        loader = ott.log_parser.control.loader:main
        load_and_post_process = ott.log_parser.control.loader:load_and_post_process
        publisher = ott.log_parser.control.publisher:main
        parser = ott.log_parser.control.parser:main
    """,
)
