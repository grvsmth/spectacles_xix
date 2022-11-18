"""
Main module for spectacles_xix
"""
from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime
from locale import LC_TIME, setlocale
from logging import basicConfig, getLogger

from pytz import timezone

from .find_play import get_play_list, get_and_tweet
from .tweet import is_time_to_tweet

CONFIG_PATH = 'spectacles_xix/config'
TIMEZONE = 'Europe/Paris'

setlocale(LC_TIME, "fr_FR")

basicConfig(level="DEBUG")
LOG = getLogger(__name__)


def parse_command_args():
    """
    Create argument parser and parse the command line arguments
    """
    parser = ArgumentParser(
        description='Compose and send a tweet about a play from the Parisian\
 Stage'
        )
    parser.add_argument('-n', '--no_tweet', action='store_true')
    parser.add_argument('-m', '--no_toot', action='store_true')
    parser.add_argument('-d', '--date', type=str)
    parser.add_argument('-w', '--wicks', type=str)
    parser.add_argument('-b', '--book', action='store_true')
    parser.add_argument('-t', '--tweeted', action='store_true')
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('-c', '--config_file', type=str, required=True)
    return parser.parse_args()


def parse_config(input_path):
    """
    Load config from ini file using ConfigParser
    """
    parser = ConfigParser()
    parser.read(input_path)
    return parser


def main():
    """
    Parse arguments, load config, get current date, get play list, get play,
    check for book link, tweet
    """
    args = parse_command_args()
    config = parse_config(args.config_file)

    local_now = timezone(TIMEZONE).localize(datetime.now())
    play_list = get_play_list(
        config['db'], args.wicks, local_now, args.date, args.tweeted
        )

    if not play_list:
        return

    if not is_time_to_tweet(args, local_now.hour, len(play_list)):
        return

    get_and_tweet(args.book, args.no_tweet, args.no_toot, config, local_now, play_list[0])


if __name__ == '__main__':
    main()
