"""
Script to import TSV tables and write them to a database
"""
import csv
import json
import sys
from pathlib import Path

import MySQLdb
from _mysql_exceptions import DatabaseError

CONFIG_PATH = 'spectacles_xix/config'
DATE_REGEX = r'\d{4}-\d{1-2}-\d{1-2}'

SQLQ = {
    'abbreviations.tsv': """INSERT INTO spectacle_abbrev
    ( abbrev, expansion, notes )
    VALUES ( %s, %s, %s )
    """,
    'theaters.tsv': """INSERT INTO spectacle_theater
    ( theater_code, theater_name, notes )
    VALUES ( %s, %s, %s )
    """
    }

def load_config():
    """
    load config
    """
    config = {}
    config_path = Path(Path.home(), CONFIG_PATH)
    for cfile in config_path.glob('*.json'):
        config_name = cfile.stem
        with cfile.open() as cfh:
            config[config_name] = json.load(cfh)

    return config

def save_to_db(config, tableq, list_data):
    """
    Save data to db
    """

    with MySQLdb.connect(
            config['db']['host'],
            config['db']['user'],
            config['db']['password'],
            config['db']['db'],
            charset='utf8'
        ) as cursor:

        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        try:
            print("Inserting {} rows".format(len(list_data)))
            cursor.executemany(tableq, list_data)
        except DatabaseError as err:
            print("Error inserting: {}".format(err))


def load_tsv(fname):
    """
    Load data from tsv file
    """
    list_out = []
    with Path(fname).open() as tsvin:
        tsv_reader = csv.reader(tsvin, delimiter="\t")
        for row in tsv_reader:
            row_list = list(row)
            if len(row_list) < 3:
                row_list.append(None)
            list_out.append(row_list)

    return list_out


if __name__ == '__main__':
    IN_DATA = load_tsv(sys.argv[1])
    CONFIG = load_config()
    # print(IN_DATA)
    save_to_db(CONFIG, SQLQ[sys.argv[1]], IN_DATA)
