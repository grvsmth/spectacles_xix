"""
Spectacles_XIX - Twitter bot to tweet announcements for performances in Paris
theaters from 200 years ago
"""

import argparse
from datetime import datetime
import json
import locale
from logging import basicConfig, getLogger
from pathlib import Path
from re import finditer

from dateutil import relativedelta
import pytz
from twitter import Twitter, OAuth

from play import Play
from check_books import check_books_api, BookResult
from db_ops import(
    db_cursor, query_by_wicks_id, query_by_date, abbreviation_db, tweet_db
    )

# TODO package
# TODO config ini

# TODO unit tests

CONFIG_PATH = 'spectacles_xix/config'
TIMEZONE = 'Europe/Paris'
DATE_FORMAT = "%A le %d %B %Y"
locale.setlocale(locale.LC_TIME, "fr_FR")

LOCAL_NOW = pytz.timezone(TIMEZONE).localize(datetime.now())

basicConfig(level="DEBUG")
LOG = getLogger(__name__)

def load_config():
    """
    Load config
    """
    config = {'path': {}}
    config_path = Path(Path.home(), CONFIG_PATH)
    for cfile in config_path.glob('*.json'):
        config_name = cfile.stem
        config['path'][config_name] = str(cfile)
        with cfile.open() as cfh:
            config[config_name] = json.load(cfh)

    return config


def get_date(date_string=None):
    """
    Convert a date string into a date object, or generate a date object in the
    nineteenth century
    """
    if date_string:
        our_date = datetime.strptime(date_string, "%d-%m-%Y").date()
    else:
        our_date = LOCAL_NOW.date() + relativedelta.relativedelta(years=-200)

    return our_date


def time_to_tweet(play_count):
    """
    Determine whether this is a good time to tweet
    """
    if not play_count:
        LOG.info("No plays: %s", play_count)
        return False

    this_hour = LOCAL_NOW.hour
    hours_remaining = 23 - this_hour
    hours_per_tweet = hours_remaining / play_count
    LOG.info(
        "%s hours remaining / %s plays = %s",
        hours_remaining,
        play_count,
        hours_per_tweet
        )

    # if we have 1 or less hours per tweet, then just tweet
    if hours_per_tweet <= 1:
        return True

    # if it's after noon (6AM New York time) and we have a play every two hours
    if this_hour > 12 and hours_per_tweet <= 2:
        return True

    # if it's after 3PM (9AM New York time) and we have a play every three hours
    if this_hour > 15 and hours_per_tweet <= 3:
        return True

    return False


def send_tweet(config, message, title_image):
    """
    Send the tweet
    """
    twapi = Twitter(auth=OAuth(
        config['token'],
        config['token_secret'],
        config['consumer_key'],
        config['consumer_secret']
        ))

    image_id = None
    if title_image:
        twupload = Twitter(
            domain='upload.twitter.com',
            auth=OAuth(
                config['token'],
                config['token_secret'],
                config['consumer_key'],
                config['consumer_secret']
                )
            )
        image_res = twupload.media.upload(media=title_image)
        if image_res:
            image_id = image_res['media_id_string']
            status = twapi.statuses.update(status=message, media_ids=image_id)
            return status

    status = twapi.statuses.update(status=message)
    return status


def expand_abbreviation(cursor, phrase):
    """
    Look up abbreviation expansion in the database
    """
    # Find abbreviated words and iterate through them
    abbrev_match = finditer('(\w+)\.', phrase)
    if not abbrev_match:
        return phrase

    replacements = set()

    for mo in abbrev_match:
        abbreviation = mo.group(1)

        expansion = abbreviation_db(cursor, abbreviation)
        if expansion:
            replacements.add((abbreviation, expansion))

    for (abbreviation, expansion) in replacements:
        phrase = phrase.replace(abbreviation + '.', expansion)

    return phrase


def check_by_date(config, today_date, tweeted):
    """
    Given a config dict, a date and whether to search already tweeted plays,
    check for plays with the given date.  If there are non, check from the first
    of the month.
    """
    play_list = query_by_date(config, today_date, tweeted)

    if not play_list:
        # Look for one play from the first of the month
        first_of_the_month = today_date.replace(day=1)
        LOG.info("Checking for plays on %s", first_of_the_month)
        play_list = query_by_date(config, first_of_the_month, tweeted, limit=1)

    return play_list


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(
        description='Compose and send a tweet about a play from the Parisian Stage'
        )
    PARSER.add_argument('-n', '--no_tweet', action='store_true')
    PARSER.add_argument('-d', '--date', type=str)
    PARSER.add_argument('-w', '--wicks', type=str)
    PARSER.add_argument('-b', '--book', action='store_true')
    PARSER.add_argument('-t', '--tweeted', action='store_true')
    PARSER.add_argument('-f', '--force', action='store_true')
    ARGS = PARSER.parse_args()
    TODAY_DATE = get_date(ARGS.date)

    CONFIG = load_config()

    if ARGS.wicks:
        PLAY_LIST = query_by_wicks_id(CONFIG['db'], ARGS.wicks, ARGS.tweeted)
    else:
        PLAY_LIST = check_by_date(CONFIG['db'], TODAY_DATE, ARGS.tweeted)

    if not PLAY_LIST:
        exit(0)

    with db_cursor(CONFIG['db']) as CURSOR:
        if not ARGS.no_tweet and not ARGS.force and not time_to_tweet(len(PLAY_LIST)):
            exit(0)

        EXPANDED_GENRE = expand_abbreviation(CURSOR, PLAY_LIST[0]['genre'])
        PLAY = Play.from_dict(PLAY_LIST[0])
        PLAY.set_today(get_date())
        PLAY.set_expanded_genre(EXPANDED_GENRE)
        PLAY.build_phrases()
        LOG.info(PLAY)

        BOOK_RESULT = BookResult()
        BOOK_LINK = ''
        if ARGS.book:
            BOOK_RESULT = check_books_api(
                CONFIG['path']['google_service_account'], PLAY
                )

        if ARGS.no_tweet:
            exit(0)

        STATUS = send_tweet(
            CONFIG['twitter'],
            str(PLAY) + ' ' + BOOK_RESULT.get_better_book_url(),
            BOOK_RESULT.get_image_file()
            )
        if 'id' in STATUS:
            LOG.info("Sent tweet ID# %s", STATUS['id'])
            tweet_db(CURSOR, PLAY_LIST[0]['id'])
