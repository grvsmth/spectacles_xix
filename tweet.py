"""
Spectacles_XIX - Twitter bot to tweet announcements for performances in Paris
theaters from 200 years ago
"""

import argparse
from datetime import datetime
import json
import locale
from pathlib import Path
import re

import MySQLdb
import MySQLdb.cursors
from dateutil import relativedelta
import pytz
from twitter import Twitter, OAuth

from play import Play
import check_books

# TODO package

# TODO convert check_books to a class

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
            cursor.execute(playq, [lookup_term])
            play_res = cursor.fetchall()
        except MySQLdb.DatabaseError as err:
            print("Error retrieving plays for {}: {}".format(lookup_term, err))
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

    # Find abbreviated words and iterate through them
    abbrev_match = re.finditer('(\w+)\.', abbrev)
    if not abbrev_match:
        return abbrev

    replacements = set()

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

        for mo in abbrev_match:
            this_abbrev = mo.group(1)

            try:
                cursor.execute(abbrevq, [this_abbrev])

            except MySQLdb.DatabaseError as err:
                print("Error retrieving expansion for abbreviation {}: {}".format(
                    abbrev,
                    err
                    ))
            res = cursor.fetchone()

            if res:
                replacements.add((this_abbrev, res[0]))

    for (this_abbrev, this_exp) in replacements:
        abbrev = abbrev.replace(this_abbrev + '.', this_exp)

    return abbrev

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
    GREG_DATE = get_date(ARGS.date)

    CONFIG = load_config()
    if ARGS.wicks:
        PLAY_LIST = load_from_db(
            CONFIG['db'],
            wicks=ARGS.wicks,
            tweeted=ARGS.tweeted
            )
        LOOKUP_TERM = ARGS.wicks
        if PLAY_LIST:
            GREG_DATE = PLAY_LIST[0].get('greg_date', GREG_DATE)
    else:
        PLAY_LIST = load_from_db(
            CONFIG['db'],
            greg_date=GREG_DATE,
            tweeted=ARGS.tweeted
            )
        LOOKUP_TERM = GREG_DATE.strftime(DATE_FORMAT)

    if not PLAY_LIST:
        print("No plays for {}".format(LOOKUP_TERM))

        if ARGS.wicks:
            exit(0)

        # Look for one play from the first of the month
        FIRST_OF_MONTH = GREG_DATE.replace(day=1)
        print("Checking for plays on {}".format(FIRST_OF_MONTH))
        PLAY_LIST = load_from_db(
            CONFIG['db'],
            greg_date=FIRST_OF_MONTH,
            tweeted=ARGS.tweeted,
            limit=1
            )
        if not PLAY_LIST:
            print("No plays for {}".format(FIRST_OF_MONTH))
            exit(0)

    if not ARGS.no_tweet and not ARGS.force and not time_to_tweet(len(PLAY_LIST)):
        exit(0)

    GENRE = expand_abbreviation(CONFIG['db'], PLAY_LIST[0]['genre'])
    PLAY = Play()
    PLAY.from_dict(PLAY_LIST[0], GREG_DATE.strftime(DATE_FORMAT), GENRE)
    print(PLAY)

    BOOK_IMAGE = None
    BOOK_LINK = ''
    if ARGS.book:
        print("Checking Google books API for {}".format(PLAY.title))
        books_api = check_books.get_api(CONFIG['path']['google_service_account'])
        book_result = check_books.search_api(
            books_api,
            "intitle:{} inauthor:{}".format(PLAY.title, PLAY.author)
            )
        if book_result:
            thumbnail_url = book_result['volumeInfo']['imageLinks'].get('thumbnail')
            BOOK_IMAGE = check_books.fetch_file(thumbnail_url)
            BOOK_LINK = check_books.munge_book_link(
                book_result['volumeInfo']['previewLink']
                )

    if ARGS.no_tweet:
        exit(0)

    STATUS = send_tweet(CONFIG['twitter'], str(PLAY) + ' ' + BOOK_LINK, BOOK_IMAGE)
    if 'id' in STATUS:
        print("Sent tweet ID# {}".format(STATUS['id']))
        tweet_db(CONFIG['db'], PLAY_LIST[0]['id'])
