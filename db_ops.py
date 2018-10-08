"""
Database-related functions for spectacles_xix twitter bot
"""
from contextlib import contextmanager
from datetime import datetime
from logging import basicConfig, getLogger
from re import finditer

from MySQLdb import connect, DatabaseError
from MySQLdb.cursors import DictCursor

basicConfig(level="DEBUG")
LOG=getLogger()

@contextmanager
def db_cursor(config):
    """
    Create db cursor and yield it
    """
    with connect(
        config['host'],
        config['user'],
        config['password'],
        config['db'],
        charset='utf8'
        ) as cursor:

        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        yield cursor


def load_from_db(config, greg_date=None, wicks=None, tweeted=False, limit=None):
    """
    Load data from db
    """
    play_list = []

    where_tweeted = {
        True: '',
        False: 'last_tweeted IS NULL\n    AND '
        }


    if not wicks and not greg_date:
        return play_list

    lookup_col = 'wicks'
    lookup_term = wicks
    if not wicks:
        lookup_col = 'greg_date'
        lookup_term = greg_date.isoformat()

    limit_string = ''
    if limit:
        limit_string = ' LIMIT {}'.format(limit)

    playq = """SELECT id, wicks, title, author, genre, acts, format,
    music, spectacle_play.theater_code, theater_name, greg_date, rev_date
    FROM spectacle_play LEFT JOIN spectacle_theater USING (theater_code)
    WHERE {}{} = %s{}
    """.format(where_tweeted[tweeted], lookup_col, limit_string)

    with connect(
        config['host'],
        config['user'],
        config['password'],
        config['db'],
        charset='utf8',
        cursorclass=DictCursor
        ) as cursor:

        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        try:
            cursor.execute(playq, [lookup_term])
            play_res = cursor.fetchall()
        except DatabaseError as err:
            LOG.error(
                "Error retrieving plays for %s: %s", lookup_term, err
                )
            return play_list

        for row in play_res:
            play_list.append(row)

    return play_list

def expand_abbreviation(cursor, abbrev):
    """
    Look up abbreviation expansion in the database
    """
    abbrevq = """SELECT expansion FROM spectacle_abbrev
    WHERE abbrev = %s
    """
    if not abbrev:
        return None

    # Find abbreviated words and iterate through them
    abbrev_match = finditer('(\w+)\.', abbrev)
    if not abbrev_match:
        return abbrev

    replacements = set()

    for mo in abbrev_match:
        this_abbrev = mo.group(1)

        try:
            cursor.execute(abbrevq, [this_abbrev])

        except DatabaseError as err:
            LOG.error(
                "Error retrieving expansion for abbreviation %s: %s",
                abbrev,
                err
                )
        res = cursor.fetchone()

        if res:
            replacements.add((this_abbrev, res[0]))

    for (this_abbrev, this_exp) in replacements:
        abbrev = abbrev.replace(this_abbrev + '.', this_exp)

    return abbrev

def tweet_db(cursor, play_id):
    """
    Save data to db
    """
    tweetq = """UPDATE spectacle_play
    SET last_tweeted = %s
    WHERE id = %s
    """

    try:
        cursor.execute(tweetq, [datetime.now().strftime("%Y-%m-%d"), play_id])
    except DatabaseError as err:
        LOG.error(
            "Error updating tweeted timestamp for %s: %s",
            play_id,
            err
            )
