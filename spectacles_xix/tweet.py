"""
Spectacles_XIX - Twitter bot to tweet announcements for performances in Paris
theaters from 200 years ago
"""
from logging import basicConfig, getLogger

from twitter import Twitter, OAuth

from .db_ops import tweet_db

basicConfig(level="DEBUG")
LOG = getLogger(__name__)


def get_hours_per_tweet(this_hour, play_count):
    """
    Given the current hour and the number of plays left to tweet, determine the
    hours remaning
    """
    hours_remaining = 23 - this_hour
    hours_per_tweet = hours_remaining / play_count
    LOG.info(
        "%s hours remaining / %s plays = %s",
        hours_remaining,
        play_count,
        hours_per_tweet
        )
    return hours_per_tweet


def is_time_to_tweet(args, this_hour, play_count):
    """
    Determine whether this is a good time to tweet
    """
    hours_per_tweet = get_hours_per_tweet(this_hour, play_count)
    good_time = False
    # if we have 1 or less hours per tweet, then just tweet
    if hours_per_tweet <= 1:
        good_time = True

    # if it's after noon (6AM New York time) and we have a play every two hours
    if this_hour > 12 and hours_per_tweet <= 2:
        good_time = True

    # if it's after 3PM (9AM New York time) and we have a play every three hours
    if this_hour > 15 and hours_per_tweet <= 3:
        good_time = True

    if good_time or args.no_tweet or args.force:
        return True

    return False


def get_oauth(config):
    """
    Retrieve an OAuth object based on the token, key and secrets in the config
    """
    return OAuth(
        config['token'],
        config['token_secret'],
        config['consumer_key'],
        config['consumer_secret']
        )


def upload_image(oauth, title_image):
    """
    Given a config and an image object, connect to the Twitter upload service,
    upload the image and return the image ID if successful
    """
    image_id = None

    twupload = Twitter(domain='upload.twitter.com', auth=oauth)

    image_response = twupload.media.upload(media=title_image)
    if image_response:
        image_id = image_response.get('media_id_string')
    return image_id


def send_tweet(cursor, config, play_id, message, title_image):
    """
    Send the tweet
    """
    oauth = get_oauth(config)
    twapi = Twitter(auth=oauth)

    image_id = None
    if title_image:
        image_id = upload_image(oauth, title_image)

    status = twapi.statuses.update(status=message, media_ids=image_id)
    if 'id' in status:
        LOG.info("Sent tweet ID# %s", status['id'])
        tweet_db(cursor, play_id)
    else:
        LOG.error(status)
    return status
