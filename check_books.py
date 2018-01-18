from pathlib import Path

from google.oauth2 import service_account
import googleapiclient.discovery

CONFIG_PATH_STRING = 'spectacles_xix/config'
CONFIG_PATH = Path(
    Path.home(),
    CONFIG_PATH_STRING,
    'google_service_account.json'
    )


SCOPES = ['https://www.googleapis.com/auth/books']
SERVICE_ACCOUNT_FILE = str(CONFIG_PATH)

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
        )

books = googleapiclient.discovery.build('books', 'v1', credentials=credentials)

response = books.volumes().list(q='karabi', filter='free-ebooks').execute()
print(response)