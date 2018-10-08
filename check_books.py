"""
Functions for retrieving information from the Google Books API
"""
from logging import basicConfig, getLogger
import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from requests import get

SCOPES = ['https://www.googleapis.com/auth/books']
QUERY_RE = re.compile(r'&dq=.+?(?=&)')

basicConfig(level='DEBUG')
LOG = getLogger()

def get_api(config_fn):
    """
    Given a Google API service account file, build a Google Books API client and
    return it
    """
    credentials = Credentials.from_service_account_file(
        config_fn,
        scopes=SCOPES
        )
    return build(
        'books', 'v1', credentials=credentials, cache_discovery=False
        )


def search_api(api, term):
    """
    Given a Google Books API client and a term, search the API for that term and
    return the first result
    """
    try:
        volumes = api.volumes()
        vol_list_object = volumes.list(
            q=term,
            filter='free-ebooks',
            langRestrict='fr'
            )
        vol_list = vol_list_object.execute()
    except HttpError as err:
        LOG.error("Error checking Books API: %s", err)
        return None

    if vol_list['totalItems'] > 0:
        return vol_list['items'][0]
    return None


def check_books_api(config_path, play):
    """
    Given the path to a config file and a Play object, generate an API object
    and search it for the play title and author
    """
    LOG.info("Checking Google books API for %s", play.title)
    books_api = get_api(config_path)
    book_response = search_api(
        books_api,
        "intitle:{} inauthor:{}".format(play.title, play.author)
        )
    return BookResult.from_api_response(book_response)


class BookResult:
    """
    Class for organizing results of a book API search
    """

    def __init__(self, book_url='', image_url=''):
        """
        Initialize BookResult class
        """
        self.book_url = book_url
        self.image_url = image_url

    @classmethod
    def from_api_response(cls, api_response):
        """
        Extract the book and image URLs from the API response and return a
        BookResult object
        """
        if not api_response:
            return cls()

        book_url = api_response['volumeInfo']['previewLink']
        image_url = api_response['volumeInfo']['imageLinks'].get('thumbnail')
        LOG.info("Found book url: %s", book_url)

        return cls(book_url, image_url)

    def get_better_image_url(self):
        """
        Transform and return book image url, increasing size and removing curled
        edge
        """
        if not self.image_url:
            return self.image_url

        out_link = self.image_url.replace('zoom=1', 'zoom=3')
        out_link = out_link.replace('&edge=curl', '')
        return out_link

    def get_better_book_url(self):
        """
        Transform and return book url, removing query terms
        """
        if not self.book_url:
            return self.book_url

        out_link = QUERY_RE.sub('', self.book_url)
        return out_link

    def get_image_file(self):
        """
        Retrieve file and return contents
        """
        better_link = self.get_better_image_url()
        if not better_link:
            return None

        file_res = get(better_link)
        return file_res.content