"""
Database-related functions for spectacles_xix twitter bot
"""
from contextlib import contextmanager
from datetime import datetime
from logging import basicConfig, getLogger

from MySQLdb import connect
from MySQLdb.cursors import Cursor, DictCursor
from _mysql_exceptions import DatabaseError

basicConfig(level="DEBUG")
LOG = getLogger(__name__)

PLAY_SELECT = """SELECT id, wicks, title, author, genre, acts, format,
        music, spectacle_play.theater_code, theater_name, greg_date, rev_date
    FROM spectacle_play LEFT JOIN spectacle_theater USING (theater_code)
    """

NOT_TWEETED_CONDITION = 'AND last_tweeted IS NULL'
NOT_TOOTED_CONDITION = 'AND last_tooted IS NULL'


@contextmanager
def db_cursor(config, cursorclass=Cursor):
    """
    Create db cursor and yield it
    """
    with connect(
            config['host'],
            config['user'],
            config['password'],
            config['db'],
            charset='utf8',
            cursorclass=cursorclass
            ) as cursor:

        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        yield cursor


def query_by_wicks_id(config, wicks, tweeted=False, tooted=False):
    """
    Search for a play based on the Wicks ID
    """
    wicks_condition = "WHERE wicks = %s"
    tweeted_condition = ''
    if not tweeted:
        tweeted_condition = NOT_TWEETED_CONDITION

    tooted_condition = ''
    if not tooted:
        tooted_condition = NOT_TOOTED_CONDITION

    query_string = '\n'.join((PLAY_SELECT, wicks_condition, tweeted_condition,
        tooted_condition))

    return query_play(config, query_string, wicks)


def query_by_date(config, greg_date, tweeted=False, tooted=False, limit=None):
    """
    Search for a play based on the Gregorian date
    """
    date_condition = "WHERE greg_date = %s"

    tweeted_condition = ''
    if not tweeted:
        tweeted_condition = NOT_TWEETED_CONDITION

    tooted_condition = ''
    if not tooted:
        tooted_condition = NOT_TOOTED_CONDITION

    limit_string = ''
    if limit:
        limit_string = "LIMIT 1"

    query_string = '\n'.join(
        (PLAY_SELECT, date_condition, tweeted_condition, tooted_condition,
        limit_string)
        )
    return query_play(config, query_string, greg_date.isoformat())


def query_play(config, query_string, lookup_term):
    """
    Given a database configuration, a query string and a lookup term, search
    for plays and return a list
    """
    with db_cursor(config, cursorclass=DictCursor) as cursor:
        play_list = play_db(cursor, query_string, lookup_term)

    return play_list


def play_db(cursor, query_string, lookup_term):
    """
    Given a query string and a term, retrieve the list of plays associated with
    that term
    """
    play_list = []

    try:
        cursor.execute(query_string, [lookup_term])
        play_res = cursor.fetchall()
    except DatabaseError as err:
        LOG.error(
            "Error retrieving plays for %s: %s", lookup_term, err
            )
        return play_list

    for row in play_res:
        play_list.append(row)

    if not play_list:
        LOG.info("No plays for %s", lookup_term)
    return play_list


def abbreviation_db(cursor, word):
    """
    Look up abbreviation expansion in the database
    """
    abbrevq = "SELECT expansion FROM spectacle_abbrev WHERE abbrev = %s"

    if word:
        try:
            cursor.execute(abbrevq, [word])

        except DatabaseError as err:
            LOG.error(
                "Error retrieving expansion for word %s: %s",
                word,
                err
                )
            return word

        res = cursor.fetchone()

        if res:
            word = res[0]

    return word


def tweet_db(cursor, play_id):
    """
    Save data to db
    """
    tweetq = """UPDATE spectacle_play
    SET last_tweeted = %s
    WHERE id = %s
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute(tweetq, [timestamp, play_id])
        LOG.debug("Marked play %s as tweeted on %s", play_id, timestamp)
    except DatabaseError as err:
        LOG.error(
            "Error updating tweeted timestamp for %s: %s",
            play_id,
            err
            )


def toot_db(cursor, play_id):
    """
    Save data to db
    """
    tootq = """UPDATE spectacle_play
    SET last_tooted = %s
    WHERE id = %s
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute(tootq, [timestamp, play_id])
        LOG.debug("Marked play %s as tooted on %s", play_id, timestamp)
    except DatabaseError as err:
        LOG.error(
            "Error updating tooted timestamp for %s: %s",
            play_id,
            err
            )

