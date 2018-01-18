#from pathlib import Path

from google.oauth2 import service_account
import googleapiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/books']



def get_api(config_fn):
    credentials = service_account.Credentials.from_service_account_file(
        config_fn,
        scopes=SCOPES
        )
    return googleapiclient.discovery.build('books', 'v1', credentials=credentials)

def search_api(api, term):
    vol_list = api.volumes().list(
        q=term,
        filter='free-ebooks',
        langRestrict='fr'
        ).execute()
    if vol_list['totalItems'] > 0:
        return vol_list['items'][0]
    return None
