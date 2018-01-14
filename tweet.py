"""
Spectacles_XIX - Twitter bot to tweet announcements for performances in Paris
theaters from 200 years ago
"""

import argparse
from datetime import datetime
import json
import locale
from pathlib import Path

import MySQLdb
import MySQLdb.cursors
from dateutil import relativedelta
import pytz
from twitter import Twitter, OAuth

from play import Play

# TODO look up book image

# TODO deal with extra plays that were dumped on the first of the month/year

CONFIG_PATH = 'spectacles_xix/config'
TIMEZONE = 'Europe/Paris'
DATE_FORMAT = "%A le %d %B %Y"
locale.setlocale(locale.LC_TIME, "fr_FR")

def load_config():
    """
    Load config
    """
    config = {}
    config_path = Path(Path.home(), CONFIG_PATH)
    for cfile in config_path.glob('*.json'):
        config_name = cfile.stem
        with cfile.open() as cfh:
            config[config_name] = json.load(cfh)

    return config

def load_from_db(config, play_date):
    """
    Load data from db
    """

    playq = """SELECT id, wicks, title, author, genre, acts, format,
    music, spectacle_play.theater_code, theater_name, rev_date
    FROM spectacle_play RIGHT JOIN spectacle_theater USING (theater_code)
    WHERE last_tweeted IS NULL
    AND greg_date = %s
    """

    play_list = []

    with MySQLdb.connect(
        config['host'],
        config['user'],
        config['password'],
        config['db'],
        charset='utf8',
        cursorclass=MySQLdb.cursors.DictCursor
        ) as cursor:

        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        try:
            cursor.execute(playq, [play_date.isoformat()])
            play_res = cursor.fetchall()
        except MySQLdb.DatabaseError as err:
            print("Error retrieving plays for {}: {}".format(play_date, err))
            return play_list

        for row in play_res:
            play_list.append(row)

    return play_list

def expand_abbreviation(config, abbrev):
    """
    Look up abbreviation expansion in the database
    """
    abbrevq = """SELECT expansion FROM spectacle_abbrev
    WHERE abbrev = %s
    """
    if not abbrev:
        return None

    expansion = abbrev

    with MySQLdb.connect(
        config['host'],
        config['user'],
        config['password'],
        config['db'],
        charset='utf8'
        ) as cursor:

        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')

        # TODO find abbreviated words and iterate through them


        try:
            cursor.execute(abbrevq, [abbrev])

        except MySQLdb.DatabaseError as err:
            print("Error retrieving expansion for abbreviation {}: {}".format(
                abbrev,
                err
                ))
        res = cursor.fetchone()
        if res:
            expansion = res

    return expansion

def tweet_db(config, play_id):
    """
    Save data to db
    """

    tweetq = """UPDATE spectacle_play
    SET last_tweeted = %s
    WHERE id = %s
    """

    with MySQLdb.connect(
        config['host'],
        config['user'],
        config['password'],
        config['db'],
        charset='utf8'
        ) as cursor:

        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        try:
            cursor.execute(tweetq, [datetime.now().strftime("%Y-%m-%d"), play_id])
        except MySQLdb.DatabaseError as err:
            print("Error updating tweeted timestamp for {}: {}".format(
                play_id,
                err
                ))

def get_date(date_string=None):
    """
    Convert a date string into a date object, or generate a date object in the
    nineteenth century
    """
    if date_string:
        our_date = datetime.strptime(date_string, "%d-%m-%Y").date()
    else:
        local_now = pytz.timezone(TIMEZONE).localize(datetime.now())
        our_date = local_now.date() + relativedelta.relativedelta(years=-200)

    return our_date

def get_hour():
    """
    Get the hour in our timezone
    """
    local_now = pytz.timezone(TIMEZONE).localize(datetime.now())
    return local_now.hour

def time_to_tweet(play_count):
    """
    Determine whether this is a good time to tweet
    """
    this_hour = get_hour()
    hours_remaining = 23 - this_hour
    hours_per_tweet = hours_remaining / play_count
    print("{} hours remaining / {} plays = {}".format(
        hours_remaining,
        play_count,
        hours_per_tweet
        ))

    # if we have 1 or less hours per tweet, then just tweet
    if hours_per_tweet <= 1:
        return True

    # if it's after noon (6AM New York time) and we have a play every two hours
    if this_hour > 12 and hours_per_tweet <= 2:
        return True

    # if it's after 3PM (9AM New York time) and we have a play every three hours
    if this_hour > 7 and hours_per_tweet <= 3:
        return True

    return False

def send_tweet(config, message):
    """
    Send the tweet
    """
    twapi = Twitter(auth=OAuth(
        config['token'],
        config['token_secret'],
        config['consumer_key'],
        config['consumer_secret']
        ))
    status = twapi.statuses.update(status=message)
    return status

if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(
        description='Compose and send a tweet about a play from the Parisian Stage'
        )
    PARSER.add_argument('--no_tweet', action='store_true')
    PARSER.add_argument('-d', '--date', type=str)
    ARGS = PARSER.parse_args()
    OUR_DATE = get_date(ARGS.date)

    CONFIG = load_config()
    PLAY_LIST = load_from_db(CONFIG['db'], OUR_DATE)
    if not PLAY_LIST:
        print("No plays for {}".format(OUR_DATE.strftime(DATE_FORMAT)))
        exit(0)

    if not time_to_tweet(len(PLAY_LIST)):
        exit(0)

    GENRE = expand_abbreviation(CONFIG['db'], PLAY_LIST[0]['genre'])
    MESSAGE = str(Play(PLAY_LIST[0], OUR_DATE.strftime(DATE_FORMAT), GENRE))
    print(MESSAGE)

    if ARGS.no_tweet:
        exit(0)

    STATUS = send_tweet(CONFIG['twitter'], MESSAGE)
    if 'id' in STATUS:
        print("Sent tweet ID# {}".format(STATUS['id']))
        tweet_db(CONFIG['db'], PLAY_LIST[0]['id'])
