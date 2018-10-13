from unittest import TestCase, main
from unittest.mock import Mock, patch

from tweet import(
    INPUT_DATE_FORMAT, get_date_object,check_by_date
    )


class TestTweet(TestCase):

    @patch('tweet.datetime')
    def test_get_date_object(self, mock_datetime):
        test_string = 'foo'

        mock_date_object = Mock()
        mock_datetime.strptime.return_value.date.return_value = mock_date_object

        test_date_object = get_date_object(test_string)
        self.assertEqual(test_date_object, mock_date_object)
        mock_datetime.strptime.assert_called_once_with(test_string, INPUT_DATE_FORMAT)

    @patch('tweet.query_by_date')
    @patch('tweet.get_date_object')
    def test_check_by_date(self, mock_get, mock_query):
        test_date = '12-10-1818'
        test_now = Mock()

        test_config = {'test': 'config'}
        test_tweeted = True

        mock_date_object = Mock()
        mock_get.return_value = mock_date_object

        mock_list = ['play 1', 'play 2']
        mock_query.return_value = mock_list

        test_list = check_by_date(
            test_config, test_now, test_date, test_tweeted
            )
        self.assertEqual(test_list, mock_list)


if __name__ == '__main__':
    main()
