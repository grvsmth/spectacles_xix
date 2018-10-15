"""
Main module for spectacles_xix
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

from check_books import check_books_api
from db_ops import abbreviation_db, db_cursor, query_by_date, query_by_wicks_id
from play import Play
from tweet import is_time_to_tweet, send_tweet

CONFIG_PATH = 'spectacles_xix/config'
TIMEZONE = 'Europe/Paris'
INPUT_DATE_FORMAT = "%d-%m-%Y"

setlocale(LC_TIME, "fr_FR")

basicConfig(level="DEBUG")
LOG = getLogger(__name__)

# TODO config ini
# TODO package
# TODO unit tests


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


def get_replacements(cursor, abbrev_match):
    """
    Given a db cursor and a set of possible abbreviations, return any matches
    found in the database
    """
    replacements = set()

    for match_object in abbrev_match:
        abbreviation = match_object.group(1)

        expansion = abbreviation_db(cursor, abbreviation)
        if expansion:
            replacements.add((abbreviation, expansion))

    return replacements


def expand_abbreviation(cursor, phrase):
    """
    Look up abbreviation expansion in the database
    """
    # Find abbreviated words and iterate through them
    abbrev_match = finditer(r'(\w+)\.', phrase)
    if not abbrev_match:
        return phrase

    replacements = get_replacements(cursor, abbrev_match)

    for (abbreviation, expansion) in replacements:
        phrase = phrase.replace(abbreviation + '.', expansion)

    return phrase


def get_play_list(config, wicks, local_now, args_date, tweeted):
    """
    Depending on the arguments, check by Wicks ID or date
    """
    if wicks:
        play_list = query_by_wicks_id(config, wicks, tweeted)
    else:
        play_list = check_by_date(config, local_now, args_date, tweeted)

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


def get_and_tweet(args_book, no_tweet, config, local_now, play_dict):
    """
    Get a cursor, get the play, check for books, send the tweet
    """
    with db_cursor(config['db']) as cursor:
        play = get_play(cursor, local_now, play_dict)

        book_result = check_books_api(
            args_book, config['path']['google_service_account'], play
            )

        if no_tweet:
            return

        send_tweet(
            cursor,
            config['twitter'],
            play_dict,
            str(play) + ' ' + book_result.get_better_book_url(),
            book_result.get_image_file()
            )


def main():
    """
    Parse arguments, load config, get current date, get play list, get play,
    check for book link, tweet
    """
    args = parse_command_args()
    config = load_config()

    local_now = timezone(TIMEZONE).localize(datetime.now())
    play_list = get_play_list(
        config['db'], args.wicks, local_now, args.date, args.tweeted
        )

    if not play_list:
        return

    if not is_time_to_tweet(args, local_now.hour, len(play_list)):
        return

    get_and_tweet(args.book, args.no_tweet, config, local_now, play_list[0])


if __name__ == '__main__':
    main()