"""
Spectacles_XIX - Twitter bot to tweet announcements for performances in Paris
theaters from 200 years ago
"""

import argparse
from datetime import datetime
import json
import locale
from pathlib import Path

from dateutil import relativedelta
import pytz
from twitter import Twitter, OAuth

from play import Play
from check_books import check_books_api, BookResult
from db_ops import db_cursor, load_from_db, expand_abbreviation, tweet_db

# TODO package
# TODO logging in db_ops and tweet.py
# TODO config ini

# TODO unit tests

CONFIG_PATH = 'spectacles_xix/config'
TIMEZONE = 'Europe/Paris'
DATE_FORMAT = "%A le %d %B %Y"
locale.setlocale(locale.LC_TIME, "fr_FR")

LOCAL_NOW = pytz.timezone(TIMEZONE).localize(datetime.now())

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
        print("No plays: {}".format(play_count))
        return False

    this_hour = LOCAL_NOW.hour
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
        PLAY_LIST = load_from_db(
            CONFIG['db'],
            wicks=ARGS.wicks,
            tweeted=ARGS.tweeted
            )
        LOOKUP_TERM = ARGS.wicks
    else:
        PLAY_LIST = load_from_db(
            CONFIG['db'],
            greg_date=TODAY_DATE,
            tweeted=ARGS.tweeted
            )
        LOOKUP_TERM = TODAY_DATE.strftime(DATE_FORMAT)

    if not PLAY_LIST:
        print("No plays for {}".format(LOOKUP_TERM))

        if ARGS.wicks:
            exit(0)

        # Look for one play from the first of the month
        PLAY_DATE = TODAY_DATE.replace(day=1)
        print("Checking for plays on {}".format(PLAY_DATE))
        PLAY_LIST = load_from_db(
            CONFIG['db'],
            greg_date=PLAY_DATE,
            tweeted=ARGS.tweeted,
            limit=1
            )
        if not PLAY_LIST:
            print("No plays for {}".format(PLAY_DATE))
            exit(0)

    with db_cursor(CONFIG['db']) as CURSOR:
        if not ARGS.no_tweet and not ARGS.force and not time_to_tweet(len(PLAY_LIST)):
            exit(0)

        EXPANDED_GENRE = expand_abbreviation(CURSOR, PLAY_LIST[0]['genre'])
        PLAY = Play.from_dict(PLAY_LIST[0])
        PLAY.set_today(get_date())
        PLAY.set_expanded_genre(EXPANDED_GENRE)
        PLAY.build_phrases()
        print(PLAY)

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
            print("Sent tweet ID# {}".format(STATUS['id']))
            tweet_db(CURSOR, PLAY_LIST[0]['id'])
