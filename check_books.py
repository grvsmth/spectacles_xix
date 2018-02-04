
from google.oauth2 import service_account
import googleapiclient.discovery
import googleapiclient.errors

from requests import get

SCOPES = ['https://www.googleapis.com/auth/books']

def get_api(config_fn):
    credentials = service_account.Credentials.from_service_account_file(
        config_fn,
        scopes=SCOPES
        )
    return googleapiclient.discovery.build('books', 'v1', credentials=credentials)

def search_api(api, term):
    try:
        vol_list = api.volumes().list(
            q=term,
            filter='free-ebooks',
            langRestrict='fr'
            ).execute()
    except googleapiclient.errors.HttpError as err:
        print("Error checking Books API: {}".format(err))
    if vol_list['totalItems'] > 0:
        return vol_list['items'][0]
    return None

def munge_image_link(in_link):
    """
    Transform book image link
    """
    if not in_link:
        return in_link

    out_link = in_link.replace('zoom=1', 'zoom=3')
    out_link = in_link.replace('&edge=curl', '')
    return out_link

def fetch_file(url):
    """
    Retrieve file and return contents
    """
    better_link = munge_image_link(url)
    file_res = get(better_link)
    return file_res.content