"""
Script to import HTML table of plays and write it to a database
"""

import json
from pathlib import Path

import MySQLdb
from _mysql_exceptions import DatabaseError

CONFIG_PATH = 'spectacles_xix/config'
CONFIG = {}


# load config
CONFIG_PATH = Path(Path.home(), CONFIG_PATH)
for cfile in CONFIG_PATH.glob('*.json'):
    config_name = cfile.stem
    with cfile.open() as cfh:
        CONFIG[config_name] = json.load(cfh)

# create tables
TABLE_SQL = {
    'theater': """CREATE TABLE spectacle_theater (
        theater_code varchar(10) NOT NULL,
        theater_name varchar(40) NOT NULL,
        notes text,
        PRIMARY KEY (theater_code)
    )""",
    'abbrev': """CREATE TABLE spectacle_abbrev (
        abbrev varchar(20) NOT NULL,
        expansion varchar(100) NOT NULL,
        notes text,
        PRIMARY KEY (abbrev)
    )""",
    'play': """CREATE TABLE spectacle_play (
        id int(10) NOT NULL,
        wicks varchar(10) NOT NULL,
        title varchar(100) NOT NULL,
        author varchar(100),
        genre varchar(40),
        acts int(3) NOT NULL,
        format varchar(10),
        music varchar(100),
        theater_code varchar(40),
        rev_date varchar(20),
        greg_date date NOT NULL,
        notes text,
        last_tweeted date,
        PRIMARY KEY (id),
        KEY greg_date (greg_date)
    )"""
}

with MySQLdb.connect(
        CONFIG['db']['host'],
        CONFIG['db']['user'],
        CONFIG['db']['password'],
        CONFIG['db']['db']
    ) as cursor:

    for name, tableq in TABLE_SQL.items():
        try:
            print("Creating table {}".format(name))
            cursor.execute(tableq)
        except DatabaseError as err:
            print("Error creating table {}: {}".format(name, err))
