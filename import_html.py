"""
Script to import HTML table of plays and write it to a database
"""

from datetime import datetime
import json
import sys
from pathlib import Path

import MySQLdb
from bs4 import BeautifulSoup

CONFIG_PATH = 'spectacles_xix/config'
DATE_REGEX = '\d{4}-\d{1-2}-\d{1-2}'

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

def save_to_db(config, list_data):
    """
    Save data to db
    """

    tableq = """INSERT INTO spectacle_play (
        id, wicks, title, author, genre, acts, format, music, theater_code,
        greg_date, notes
        ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s
        )
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
        except MySQLdb.DatabaseError as err:
            print("Error inserting: {}".format(err))


def load_html(filename):
    """
    Load HTML from file
    """
    return Path(filename).read_text()


def datify(in_string):
    out_data = in_string
    if in_string:
        try:
            out_data = datetime.strptime(in_string, "%d-%m-%Y")
        except ValueError as err:
            print("Invalid date ({}): {}".format(in_string, err))
        except TypeError as err:
            print("Invalid date ({}): {}".format(in_string, err))
    return out_data

def parse_row(in_row):
    """
    Iterate through the columns in a row and return a list
    """
    row_data = []
    for idx, col in enumerate(in_row.children):
        if col.name == 'td':
            if idx in (5, 21):
                continue
            if idx in (1, 13):
                try:
                    col_data = int(col.string)
                except TypeError as err:
                    col_data = 0
                except ValueError as err:
                    print("Not a number {}: {}".format(col.string, err))
                    print(in_row)
                    exit()
            elif idx == 23:
                col_data = datify(col.string)
                if not col_data:
                    return []
            else:
                col_data = ''.join(col.stripped_strings)
            row_data.append(col_data)
    return row_data

def parse_table(in_html):
    """
    Parse table
    """
    table_data = []
    soup = BeautifulSoup(in_html, "html.parser")
    tr_count = 0
    for row in soup.table.children:
        if row.name == 'tr':
            tr_count += 1
            row_data = parse_row(row)
            if row_data:
                table_data.append(row_data)
    print("Processed {} rows; returning {} items".format(tr_count, len(table_data)))
    return table_data


if __name__ == '__main__':
    IN_HTML = load_html(sys.argv[1])
    CONFIG = load_config()
    OUT_DATA = parse_table(IN_HTML)
    # print(OUT_DATA[-5:])
    save_to_db(CONFIG, OUT_DATA)
