"""
Given lookup information (a date or a Wicks ID, whether it's already been
tweeted), find a play.
"""
from datetime import datetime
from logging import basicConfig, getLogger
from re import finditer

from dateutil import relativedelta

from .check_books import check_books_api
from .db_ops import (
    abbreviation_db, db_cursor, query_by_date, query_by_wicks_id
    )
from .play import Play
from .tweet import send_tweet, send_toot

basicConfig(level="DEBUG")
LOG = getLogger(__name__)

INPUT_DATE_FORMAT = "%d-%m-%Y"


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
    check for plays with the given date.  If there are non, check from the
    first of the month.
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


def get_and_tweet(args_book, no_tweet, no_toot, config, local_now, play_dict):
    """
    Get a cursor, get the play, check for books, send the tweet
    """
    with db_cursor(config['db']) as cursor:
        play = get_play(cursor, local_now, play_dict)
        play_id = play_dict['id']

        book_result = check_books_api(
            args_book, config['path']['google_service_account'], play
            )

        message = str(play) + ' ' + book_result.get_better_book_url()
        book_image = book_result.get_image_file()

        if not no_toot:
            send_toot(cursor, config['mastodon'], play_id, message, book_image)

        if no_tweet:
            return

        send_tweet(
            cursor,
            config['twitter'],
            play_id,
            message,
            book_image
            )
