"""
Functions for retrieving information from the Google Books API
"""
import re

from google.oauth2 import service_account
import googleapiclient.discovery
import googleapiclient.errors

from requests import get

SCOPES = ['https://www.googleapis.com/auth/books']
QUERY_RE = re.compile(r'&dq=.+?(?=&)')


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
    def from_api_response(cls, api_result):
        if not api_result:
            return cls

        book_url = api_result['volumeInfo']['previewLink']
        image_url = api_result['volumeInfo']['imageLinks'].get('thumbnail')
        print("Found book url: " + book_url)

        return cls(book_url, image_url)

    def get_better_image_url(self):
        """
        Transform book image link, increasing size and removing curled edge
        """
        if not self.image_url:
            return self.image_url

        out_link = self.image_url.replace('zoom=1', 'zoom=3')
        out_link = out_link.replace('&edge=curl', '')
        return out_link

    def get_better_book_url(self):
        """
        Transform book image link, removing query terms
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