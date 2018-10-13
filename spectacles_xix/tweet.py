"""
Spectacles_XIX - Twitter bot to tweet announcements for performances in Paris
theaters from 200 years ago
"""
from argparse import ArgumentParser
from datetime import datetime
import json
from locale import LC_TIME, setlocale
from logging import basicConfig, getLogger
from pathlib import Path
from re import finditer

from dateutil import relativedelta
from pytz import timezone
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
INPUT_DATE_FORMAT = "%d-%m-%Y"
setlocale(LC_TIME, "fr_FR")

basicConfig(level="DEBUG")
LOG = getLogger(__name__)

def parse_command_args():
    """
    Create argument parser and parse the command line arguments
    """
    parser = ArgumentParser(
        description='Compose and send a tweet about a play from the Parisian Stage'
        )
    parser.add_argument('-n', '--no_tweet', action='store_true')
    parser.add_argument('-d', '--date', type=str)
    parser.add_argument('-w', '--wicks', type=str)
    parser.add_argument('-b', '--book', action='store_true')
    parser.add_argument('-t', '--tweeted', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')
    return parser.parse_args()


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


def get_date_object(date_string):
    """
    Convert a date string into a date object, or
    """
    return datetime.strptime(date_string, INPUT_DATE_FORMAT).date()


def get_200_years_ago(local_now):
    """
    Generate a date object in the nineteenth century
    """
    return local_now.date() + relativedelta.relativedelta(years=-200)


def time_to_tweet(local_now, play_count):
    """
    Determine whether this is a good time to tweet
    """
    if not play_count:
        LOG.info("No plays: %s", play_count)
        return False

    this_hour = local_now.hour
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


def upload_image(config, title_image):
    """
    Given a config and an image object, connect to the Twitter upload service,
    upload the image and return the image ID if successful
    """
    image_id = None

    twupload = Twitter(
    domain='upload.twitter.com',
    auth=OAuth(
        config['token'],
        config['token_secret'],
        config['consumer_key'],
        config['consumer_secret']
        )
    )

    image_response = twupload.media.upload(media=title_image)
    if image_response:
        image_id = image_response['media_id_string']
    return image_id


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
        image_id = upload_image(config, title_image)

    status = twapi.statuses.update(status=message, media_ids=image_id)
    return status


def expand_abbreviation(cursor, phrase):
    """
    Look up abbreviation expansion in the database
    """
    # Find abbreviated words and iterate through them
    abbrev_match = finditer(r'(\w+)\.', phrase)
    if not abbrev_match:
        return phrase

    replacements = set()

    for match_object in abbrev_match:
        abbreviation = match_object.group(1)

        expansion = abbreviation_db(cursor, abbreviation)
        if expansion:
            replacements.add((abbreviation, expansion))

    for (abbreviation, expansion) in replacements:
        phrase = phrase.replace(abbreviation + '.', expansion)

    return phrase


def check_by_date(config, local_now, args_date, tweeted):
    """
    Given a config dict, a date and whether to search already tweeted plays,
    check for plays with the given date.  If there are non, check from the first
    of the month.
    """
    if args_date:
        today_date = get_date_object(args_date)
    else:
        today_date = get_200_years_ago(local_now)

    play_list = query_by_date(config, today_date, tweeted)

    if not play_list:
        # Look for one play from the first of the month
        first_of_the_month = today_date.replace(day=1)
        LOG.info("Checking for plays on %s", first_of_the_month)
        play_list = query_by_date(config, first_of_the_month, tweeted, limit=1)

    return play_list


def get_play(cursor, local_now, play_dict):
    """
    Given a database cursor, the current time and a dict of play info, return
    a play object
    """
    old_date = get_200_years_ago(local_now)
    expanded_genre = expand_abbreviation(cursor, play_dict['genre'])

    play = Play.from_dict(play_dict)
    play.set_today(old_date)
    play.set_expanded_genre(expanded_genre)

    LOG.info(play)
    return play


def main():
    """
    Parse arguments, load config, get current date, get play list, get play,
    check for book link, tweet
    """
    args = parse_command_args()
    config = load_config()

    local_now = timezone(TIMEZONE).localize(datetime.now())

    if args.wicks:
        play_list = query_by_wicks_id(config['db'], args.wicks, args.tweeted)
    else:
        play_list = check_by_date(
            config['db'], local_now, args.date, args.tweeted
            )

    if not play_list:
        exit(0)

    if not args.no_tweet and not args.force and not time_to_tweet(
        local_now, len(play_list),
        ):
        exit(0)

    with db_cursor(config['db']) as cursor:
        play = get_play(cursor, local_now, play_list[0])

        book_result = BookResult()
        if args.book:
            book_result = check_books_api(
                config['path']['google_service_account'], play
                )

        if args.no_tweet:
            exit(0)

        status = send_tweet(
            config['twitter'],
            str(play) + ' ' + book_result.get_better_book_url(),
            book_result.get_image_file()
            )
        if 'id' in status:
            LOG.info("Sent tweet ID# %s", status['id'])
            tweet_db(cursor, play_list[0]['id'])
        else:
            LOG.error(status)

if __name__ == '__main__':
    main()