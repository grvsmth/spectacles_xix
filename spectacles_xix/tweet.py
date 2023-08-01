"""
Spectacles_XIX - Twitter bot to tweet announcements for performances in Paris
theaters from 200 years ago
"""
from logging import basicConfig, getLogger
from time import sleep

from mastodon import Mastodon, MastodonAPIError
from twitter import Twitter, OAuth

from .db_ops import toot_db, tweet_db

basicConfig(level="DEBUG")
LOG = getLogger(__name__)


MEDIA_WAIT_TIME = 5
ATTACHMENT_ERROR = 'Impossible de joindre les fichiers en cours de traitement. Réessayez dans un instant\xa0!'

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

    # if it's after 3PM (9AM New York time) and we have a play every three
    # hours
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


def mastodon_image(mastodon, title_image):
    mime_type = "image/png"
    media_res = mastodon.media_post(title_image, mime_type)

    if (media_res.get("type") != "image"):
        return None

    return str(media_res.get("id", None))


def send_toot(cursor, config, play_id, message, title_image):
    media_id = None

    mastodon = Mastodon(client_id = config['client_id'],
        client_secret = config['client_secret'],
        access_token = config['access_token'],
        api_base_url = config['base_uri'])

    if title_image:
        media_id = mastodon_image(mastodon, title_image)
        if media_id:
            LOG.info("media_id=" + media_id)
            # Give the server a little time to process our pic
            sleep(MEDIA_WAIT_TIME)

    try:
        status = mastodon.status_post(message, media_ids=[media_id])
    except MastodonAPIError as err:
        LOG.error("Unable to post status!  Trying without media... %s",
            err)

        if err.args[3] == ATTACHMENT_ERROR:
            mastodon.status_post(message)

    if 'id' in status:
        LOG.info("Sent toot ID# %s", status['id'])
        toot_db(cursor, play_id)
    else:
        LOG.error(status)


def send_tweet(cursor, config, play_id, message, title_image):
    """
    Send the tweet
    """
    oauth = get_oauth(config)
    twapi = Twitter(auth=oauth)

    image_id = ''
    if title_image:
        image_id = upload_image(oauth, title_image)

    status = twapi.statuses.update(status=message, media_ids=image_id)
    if 'id' in status:
        LOG.info("Sent tweet ID# %s", status['id'])
        tweet_db(cursor, play_id)
    else:
        LOG.error(status)

    return status
