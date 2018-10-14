from unittest import TestCase, main
from unittest.mock import Mock, patch

from tweet import(
    INPUT_DATE_FORMAT,
    get_200_years_ago,
    get_date_object,
    get_hours_per_tweet,
    is_time_to_tweet,
    check_by_date
    )


class TestTweet(TestCase):

    @patch('tweet.datetime')
    def test_get_date_object(self, mock_datetime):
        test_string = 'foo'

        mock_date_object = Mock()
        mock_datetime.strptime.return_value.date.return_value = mock_date_object

        test_date_object = get_date_object(test_string)
        self.assertEqual(test_date_object, mock_date_object)
        mock_datetime.strptime.assert_called_once_with(
            test_string, INPUT_DATE_FORMAT
            )

    @patch('tweet.relativedelta')
    def test_get_200_years_ago(self, mock_relativedelta):
        mock_date = 2018
        mock_local_now = Mock()
        mock_local_now.date.return_value = mock_date

        mock_delta = -200
        mock_relativedelta.relativedelta.return_value = mock_delta

        target_date = mock_date + mock_delta
        test_date = get_200_years_ago(mock_local_now)

        self.assertEqual(test_date, target_date)

        mock_local_now.date.assert_called_once_with()
        mock_relativedelta.relativedelta.assert_called_once_with(
            years=mock_delta
            )

    def test_get_hours_per_tweet(self):
        test_hour = 22
        test_play_count = 1
        target_hours = 1

        with self.assertLogs(level="INFO"):
            test_hours = get_hours_per_tweet(test_hour, test_play_count)
        self.assertEqual(test_hours, target_hours)

    def test_get_hours_per_tweet_1_5(self):
        test_hour = 20
        test_play_count = 2
        target_hours = 1.5

        with self.assertLogs(level="INFO"):
            test_hours = get_hours_per_tweet(test_hour, test_play_count)
        self.assertEqual(test_hours, target_hours)

    def test_is_time_to_tweet(self):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 9000
        test_hours_per_tweet = 1

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_hours_per_tweet)
        self.assertEqual(test_time, target_time)

    def test_is_time_to_tweet_pm(self):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 13
        test_hours_per_tweet = 2

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_hours_per_tweet)
        self.assertEqual(test_time, target_time)

    def test_is_time_to_tweet_pm_false(self):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 13
        test_hours_per_tweet = 3

        target_time = False
        test_time = is_time_to_tweet(mock_args, test_hour, test_hours_per_tweet)
        self.assertEqual(test_time, target_time)

    def test_is_time_to_tweet_evening(self):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 19
        test_hours_per_tweet = 2

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_hours_per_tweet)
        self.assertEqual(test_time, target_time)

    def test_is_time_to_tweet_evening_false(self):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 19
        test_hours_per_tweet = 5

        target_time = False
        test_time = is_time_to_tweet(mock_args, test_hour, test_hours_per_tweet)
        self.assertEqual(test_time, target_time)

    def test_is_time_to_tweet_false_no_tweet(self):
        mock_args = Mock(no_tweet=True, force=False)
        test_hour = 13
        test_hours_per_tweet = 3

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_hours_per_tweet)
        self.assertEqual(test_time, target_time)

    def test_is_time_to_tweet_false_force(self):
        mock_args = Mock(no_tweet=False, force=True)
        test_hour = 13
        test_hours_per_tweet = 3

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_hours_per_tweet)
        self.assertEqual(test_time, target_time)

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
