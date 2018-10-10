"""
Tests for check_books, functions and class to retrieve and process Google Books
data
"""
from unittest import TestCase, main
from unittest.mock import Mock, patch

from spectacles_xix.check_books import(
    SCOPES, check_books_api, get_api, search_api, BookResult, HttpError
    )


class TestApi(TestCase):

    @patch('spectacles_xix.check_books.build')
    @patch('spectacles_xix.check_books.Credentials')
    def test_get_api(self, mock_cred_class, mock_build):
        test_file_name = '/path/to/test_file.ini'
        mock_credentials = Mock()
        mock_api = Mock()

        mock_cred_class.from_service_account_file.return_value = mock_credentials
        mock_build.return_value = mock_api

        test_api = get_api(test_file_name)
        self.assertEqual(test_api, mock_api)

        mock_cred_class.from_service_account_file.assert_called_once_with(
            test_file_name, scopes=SCOPES
            )
        mock_build.assert_called_once_with(
            'books', 'v1', credentials=mock_credentials, cache_discovery=False
            )

    def test_search_api(self):
        mock_api = Mock()
        test_term = 'test term'

        test_volume = {'test': 'foo'}
        test_other_volume = {'bar': 'baz'}
        test_vol_list = {
            'totalItems': 2,
            'items': [test_volume, test_other_volume]
            }

        mock_volumes = Mock()
        mock_volumes.list.return_value.execute.return_value = test_vol_list

        mock_api.volumes.return_value = mock_volumes

        test_output = search_api(mock_api, test_term)

        self.assertEqual(test_output, test_volume)

        mock_api.volumes.assert_called_once_with()
        mock_volumes.list.assert_called_once_with(
            q=test_term,
            filter='free-ebooks',
            langRestrict='fr'
            )
        mock_volumes.list.return_value.execute.assert_called_once_with()

    def test_search_api_error(self):
        test_term = 'test term'

        mock_resp = Mock(reason="I don't like you")

        mock_list = Mock()
        mock_list.execute.side_effect = HttpError(
            resp=mock_resp, content=b'bar'
            )

        mock_volumes = Mock()
        mock_volumes.list.return_value = mock_list

        mock_api = Mock()
        mock_api.volumes.return_value = mock_volumes

        target_output = None

        with self.assertLogs(level="ERROR"):
            test_output = search_api(mock_api, test_term)

        self.assertEqual(test_output, target_output)

        mock_api.volumes.assert_called_once_with()
        mock_volumes.list.assert_called_once_with(
            q=test_term,
            filter='free-ebooks',
            langRestrict='fr'
            )
        mock_volumes.list.return_value.execute.assert_called_once_with()

    def test_search_api_empty(self):
        mock_api = Mock()
        test_term = 'test term'

        test_vol_list = {
            'totalItems': 0,
            'items': []
            }

        mock_volumes = Mock()
        mock_volumes.list.return_value.execute.return_value = test_vol_list

        mock_api.volumes.return_value = mock_volumes
        target_output = None

        test_output = search_api(mock_api, test_term)

        self.assertEqual(test_output, target_output)

        mock_api.volumes.assert_called_once_with()
        mock_volumes.list.assert_called_once_with(
            q=test_term,
            filter='free-ebooks',
            langRestrict='fr'
            )
        mock_volumes.list.return_value.execute.assert_called_once_with()

    @patch('spectacles_xix.check_books.BookResult')
    @patch('spectacles_xix.check_books.search_api')
    @patch('spectacles_xix.check_books.get_api')
    def test_check_books_api(self, mock_get, mock_search, mock_result):
        test_config_path = '/path/to/config/file.json'

        test_title = 'test title'
        test_author = 'test author'
        mock_play = Mock(title=test_title, author=test_author)

        mock_api = Mock()
        mock_get.return_value = mock_api

        test_response = {'volumeInfo': 'foo'}
        mock_search.return_value = test_response

        mock_result_object = Mock()
        mock_result.from_api_response.return_value = mock_result_object

        test_result = check_books_api(test_config_path, mock_play)
        self.assertEqual(test_result, mock_result_object)


class TestBookResult(TestCase):

    def setUp(self):
        self.book_url = 'https://test.url/book?foo=bar&dq=search+term&baz=oos'
        self.image_url = 'https://example.com/image_url?zoom=1&edge=curl'

        self.target_image_url = 'https://example.com/image_url?zoom=3'

        self.result = BookResult(
            book_url=self.book_url,
            image_url=self.image_url
            )

    def test_from_api_response(self):
        test_response = {
            'volumeInfo': {
                'previewLink': self.book_url,
                'imageLinks': {'thumbnail': self.image_url}
                }
            }

        with self.assertLogs(level="INFO"):
            test_result = BookResult.from_api_response(test_response)
        self.assertEqual(test_result.book_url, self.book_url)
        self.assertEqual(test_result.image_url, self.image_url)

    def test_from_api_response_empty(self):
        target_book_url = ''
        target_image_url = ''
        test_response = {}

        test_result = BookResult.from_api_response(test_response)
        self.assertEqual(test_result.book_url, target_book_url)
        self.assertEqual(test_result.image_url, target_image_url)

    def test_get_better_image_url(self):
        test_url = self.result.get_better_image_url()
        self.assertEqual(test_url, self.target_image_url)

    def test_get_better_image_url_blank(self):
        target_url = ''
        self.result.image_url = ''
        test_url = self.result.get_better_image_url()
        self.assertEqual(test_url, target_url)

    def test_get_better_book_url(self):
        target_url = 'https://test.url/book?foo=bar&baz=oos'
        test_url = self.result.get_better_book_url()
        self.assertEqual(test_url, target_url)

    def test_get_better_book_url_blank(self):
        target_url = ''
        self.result.book_url = ''
        test_url = self.result.get_better_book_url()
        self.assertEqual(test_url, target_url)

    @patch('spectacles_xix.check_books.get')
    @patch('spectacles_xix.check_books.BookResult.get_better_image_url')
    def test_get_image_file(self, mock_image, mock_get):
        mock_image.return_value = self.target_image_url
        mock_content = 'test content'

        mock_result = Mock(content=mock_content)
        mock_get.return_value = mock_result

        test_content = self.result.get_image_file()
        self.assertEqual(test_content, mock_content)

        mock_image.assert_called_once_with()
        mock_get.assert_called_once_with(self.target_image_url)

    @patch('spectacles_xix.check_books.get')
    @patch('spectacles_xix.check_books.BookResult.get_better_image_url')
    def test_get_image_file_empty(self, mock_image, mock_get):
        mock_image.return_value = ''

        test_content = self.result.get_image_file()
        self.assertIsNone(test_content)

        mock_image.assert_called_once_with()
        mock_get.assert_not_called()


if __name__ == '__main__':
    main()