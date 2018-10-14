from unittest import TestCase, main
from unittest.mock import Mock, call, patch

from tweet import(
    INPUT_DATE_FORMAT,
    get_200_years_ago,
    get_date_object,
    get_hours_per_tweet,
    is_time_to_tweet,
    get_oauth,
    upload_image,
    send_tweet,
    get_replacements,
    expand_abbreviation,
    check_by_date,
    get_play,
    get_play_list,
    main as tweet_main
    )


class TestTime(TestCase):

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

    @patch('tweet.get_hours_per_tweet')
    def test_is_time_to_tweet(self, mock_get):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 9000
        test_play_count = 1

        test_hours_per_tweet = 1
        mock_get.return_value = test_hours_per_tweet

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_play_count)

        self.assertEqual(test_time, target_time)
        mock_get.assert_called_once_with(test_hour, test_play_count)

    @patch('tweet.get_hours_per_tweet')
    def test_is_time_to_tweet_pm(self, mock_get):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 13
        test_play_count = 7

        test_hours_per_tweet = 2
        mock_get.return_value = test_hours_per_tweet

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_play_count)

        self.assertEqual(test_time, target_time)
        mock_get.assert_called_once_with(test_hour, test_play_count)

    @patch('tweet.get_hours_per_tweet')
    def test_is_time_to_tweet_pm_false(self, mock_get):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 13
        test_play_count = 5

        test_hours_per_tweet = 3
        mock_get.return_value = test_hours_per_tweet

        target_time = False
        test_time = is_time_to_tweet(mock_args, test_hour, test_play_count)

        self.assertEqual(test_time, target_time)
        mock_get.assert_called_once_with(test_hour, test_play_count)

    @patch('tweet.get_hours_per_tweet')
    def test_is_time_to_tweet_evening(self, mock_get):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 19
        test_play_count = 9

        test_hours_per_tweet = 2
        mock_get.return_value = test_hours_per_tweet

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_play_count)

        self.assertEqual(test_time, target_time)
        mock_get.assert_called_once_with(test_hour, test_play_count)

    @patch('tweet.get_hours_per_tweet')
    def test_is_time_to_tweet_evening_false(self, mock_get):
        mock_args = Mock(no_tweet=False, force=False)
        test_hour = 19
        test_play_count = 4

        test_hours_per_tweet = 5
        mock_get.return_value = test_hours_per_tweet

        target_time = False
        test_time = is_time_to_tweet(mock_args, test_hour, test_play_count)

        self.assertEqual(test_time, target_time)
        mock_get.assert_called_once_with(test_hour, test_play_count)

    @patch('tweet.get_hours_per_tweet')
    def test_is_time_to_tweet_false_no_tweet(self, mock_get):
        mock_args = Mock(no_tweet=True, force=False)
        test_hour = 13
        test_play_count = 6

        test_hours_per_tweet = 3
        mock_get.return_value = test_hours_per_tweet

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_play_count)

        self.assertEqual(test_time, target_time)
        mock_get.assert_called_once_with(test_hour, test_play_count)

    @patch('tweet.get_hours_per_tweet')
    def test_is_time_to_tweet_false_force(self, mock_get):
        mock_args = Mock(no_tweet=False, force=True)
        test_hour = 13
        test_play_count = 4

        test_hours_per_tweet = 3
        mock_get.return_value = test_hours_per_tweet

        target_time = True
        test_time = is_time_to_tweet(mock_args, test_hour, test_play_count)

        self.assertEqual(test_time, target_time)
        mock_get.assert_called_once_with(test_hour, test_play_count)


class TestTweet(TestCase):

    def setUp(self):
        self.test_token = 'test token'
        self.test_token_secret = 'test token secret'
        self.test_consumer_key = 'test consumer key'
        self.test_consumer_secret = 'test consumer secret'
        self.test_config = {
            'token': self.test_token,
            'token_secret': self.test_token_secret,
            'consumer_key': self.test_consumer_key,
            'consumer_secret': self.test_consumer_secret
            }

        self.mock_image_id = 'a4i5u8;'
        self.test_message = 'test message'

    @patch('tweet.OAuth')
    def test_get_oauth(self, mock_oauth):

        mock_auth = Mock()
        mock_oauth.return_value = mock_auth

        test_auth = get_oauth(self.test_config)
        self.assertEqual(test_auth, mock_auth)

        mock_oauth.assert_called_once_with(
            self.test_token,
            self.test_token_secret,
            self.test_consumer_key,
            self.test_consumer_secret
            )

    @patch('tweet.Twitter')
    def test_upload_image(self, mock_twitter):
        mock_oauth = Mock()
        mock_image = Mock()

        mock_twupload = Mock()
        mock_twupload.media.upload.return_value = {
            'media_id_string': self.mock_image_id
            }

        mock_twitter.return_value = mock_twupload

        test_image_id = upload_image(mock_oauth, mock_image)
        self.assertEqual(test_image_id, self.mock_image_id)

        mock_twitter.assert_called_once_with(
            domain='upload.twitter.com', auth=mock_oauth
            )
        mock_twupload.media.upload.assert_called_once_with(
            media=mock_image
            )

    @patch('tweet.Twitter')
    def test_upload_image_none(self, mock_twitter):
        mock_oauth = Mock()
        mock_image = Mock()
        target_image_id = None

        mock_twupload = Mock()
        mock_twupload.media.upload.return_value = None

        mock_twitter.return_value = mock_twupload

        test_image_id = upload_image(mock_oauth, mock_image)
        self.assertEqual(test_image_id, target_image_id)

        mock_twitter.assert_called_once_with(
            domain='upload.twitter.com', auth=mock_oauth
            )
        mock_twupload.media.upload.assert_called_once_with(
            media=mock_image
            )

    @patch('tweet.Twitter')
    def test_upload_image_no_id(self, mock_twitter):
        mock_oauth = Mock()
        mock_image = Mock()
        target_image_id = None

        mock_twupload = Mock()
        mock_twupload.media.upload.return_value = {
            'media_id_foo': 'bleah'
            }

        mock_twitter.return_value = mock_twupload

        test_image_id = upload_image(mock_oauth, mock_image)
        self.assertEqual(test_image_id, target_image_id)

        mock_twitter.assert_called_once_with(
            domain='upload.twitter.com', auth=mock_oauth
            )
        mock_twupload.media.upload.assert_called_once_with(
            media=mock_image
            )

    @patch('tweet.tweet_db')
    @patch('tweet.upload_image')
    @patch('tweet.Twitter')
    @patch('tweet.get_oauth')
    def test_send_tweet(self, mock_get, mock_twitter, mock_upload, mock_db):
        mock_cursor = Mock()
        test_play_id = 888

        mock_oauth = Mock()
        mock_get.return_value = mock_oauth

        mock_twapi = Mock()
        mock_status = {'id' : 'xyz'}
        mock_twapi.statuses.update.return_value = mock_status
        mock_twitter.return_value = mock_twapi

        mock_image = Mock()
        mock_upload.return_value = self.mock_image_id

        with self.assertLogs(level="INFO"):
            test_status = send_tweet(
                mock_cursor,
                self.test_config,
                test_play_id,
                self.test_message,
                mock_image
                )
        self.assertDictEqual(test_status, mock_status)

        mock_get.assert_called_once_with(self.test_config)
        mock_twitter.assert_called_once_with(auth=mock_oauth)

        mock_upload.asert_called_once_with(mock_oauth, mock_image)
        mock_twapi.statuses.update.assert_called_once_with(
            status=self.test_message, media_ids=self.mock_image_id
            )
        mock_db.assert_called_once_with(mock_cursor, test_play_id)

    @patch('tweet.tweet_db')
    @patch('tweet.upload_image')
    @patch('tweet.Twitter')
    @patch('tweet.get_oauth')
    def test_send_tweet_no_id(self, mock_get, mock_twitter, mock_upload, mock_db):
        mock_cursor = Mock()
        test_play_id = 888

        mock_oauth = Mock()
        mock_get.return_value = mock_oauth

        mock_twapi = Mock()
        mock_status = {'zid' : 'xyz'}
        mock_twapi.statuses.update.return_value = mock_status
        mock_twitter.return_value = mock_twapi

        mock_image = Mock()
        mock_upload.return_value = self.mock_image_id

        with self.assertLogs(level="ERROR"):
            test_status = send_tweet(
                mock_cursor,
                self.test_config,
                test_play_id,
                self.test_message,
                mock_image
                )
        self.assertDictEqual(test_status, mock_status)

        mock_get.assert_called_once_with(self.test_config)
        mock_twitter.assert_called_once_with(auth=mock_oauth)

        mock_upload.asert_called_once_with(mock_oauth, mock_image)
        mock_twapi.statuses.update.assert_called_once_with(
            status=self.test_message, media_ids=self.mock_image_id
            )
        mock_db.assert_not_called()

    @patch('tweet.tweet_db')
    @patch('tweet.upload_image')
    @patch('tweet.Twitter')
    @patch('tweet.get_oauth')
    def test_send_tweet_no_image(self, m_get, m_twitter, m_upload, m_db):
        mock_cursor = Mock()
        test_play_id = 888

        mock_oauth = Mock()
        m_get.return_value = mock_oauth

        mock_twapi = Mock()
        mock_status = {'id' : 'xyz'}
        mock_twapi.statuses.update.return_value = mock_status
        m_twitter.return_value = mock_twapi

        mock_image = None

        with self.assertLogs(level="INFO"):
            test_status = send_tweet(
                mock_cursor,
                self.test_config,
                test_play_id,
                self.test_message,
                mock_image
                )
        self.assertDictEqual(test_status, mock_status)

        m_get.assert_called_once_with(self.test_config)
        m_twitter.assert_called_once_with(auth=mock_oauth)

        m_upload.asert_not_called()
        mock_twapi.statuses.update.assert_called_once_with(
            status=self.test_message, media_ids=None
            )
        m_db.assert_called_once_with(mock_cursor, test_play_id)


class TestDb(TestCase):

    def setUp(self):
        self.abbrev_match_list = [
            ('op', 'opéra'),
            ('com', 'comique')
            ]

    @patch('tweet.abbreviation_db')
    def test_get_replacements(self, mock_abbreviation_db):
        mock_cursor = Mock()

        match_list = []
        call_list = []
        expansion_list = []
        for match_tuple in self.abbrev_match_list:
            mock_match = Mock()
            mock_match.group.return_value = match_tuple[0]
            match_list.append(mock_match)

            call_list.append(call(mock_cursor, match_tuple[0]))
            expansion_list.append(match_tuple[1])

        mock_abbreviation_db.side_effect = expansion_list

        test_abbrev_match = get_replacements(mock_cursor, match_list)
        self.assertEqual(test_abbrev_match, set(self.abbrev_match_list))

        mock_abbreviation_db.assert_has_calls(call_list)

    @patch('tweet.get_replacements')
    @patch('tweet.finditer')
    def test_expand_abbreviation(self, mock_finditer, mock_get):
        mock_cursor = Mock()
        mock_phrase = 'op.-com.'
        target_expansion = 'opéra-comique'

        mock_abbrev_match = ['op', 'com']
        mock_finditer.return_value = mock_abbrev_match

        mock_replacements = set(self.abbrev_match_list)
        mock_get.return_value = mock_replacements

        test_expansion = expand_abbreviation(mock_cursor, mock_phrase)
        self.assertEqual(test_expansion, target_expansion)

        mock_finditer.assert_called_once_with(r'(\w+)\.', mock_phrase)
        mock_get.assert_called_once_with(mock_cursor, mock_abbrev_match)

    @patch('tweet.get_replacements')
    @patch('tweet.finditer')
    def test_expand_abbreviation_no_match(self, mock_finditer, mock_get):
        mock_cursor = Mock()
        mock_phrase = 'op.-com.'

        mock_abbrev_match = []
        mock_finditer.return_value = mock_abbrev_match

        test_expansion = expand_abbreviation(mock_cursor, mock_phrase)
        self.assertEqual(test_expansion, mock_phrase)

        mock_finditer.assert_called_once_with(r'(\w+)\.', mock_phrase)
        mock_get.assert_not_called()

    @patch('tweet.query_by_date')
    @patch('tweet.get_200_years_ago')
    @patch('tweet.get_date_object')
    def test_check_by_date(self, mock_get_date, mock_get_200, mock_query):
        test_date = '12-10-1818'
        test_now = Mock()

        test_config = {'test': 'config'}
        test_tweeted = True

        mock_date_object = Mock()
        mock_get_date.return_value = mock_date_object

        mock_list = ['play 1', 'play 2']
        mock_query.return_value = mock_list

        test_list = check_by_date(
            test_config, test_now, test_date, test_tweeted
            )
        self.assertEqual(test_list, mock_list)

        mock_get_date.assert_called_once_with(test_date)
        mock_query.assert_called_once_with(
            test_config, mock_date_object, test_tweeted
            )
        mock_get_200.assert_not_called()

    @patch('tweet.query_by_date')
    @patch('tweet.get_200_years_ago')
    @patch('tweet.get_date_object')
    def test_check_by_date_200(self, mock_get_date, mock_get_200, mock_query):
        test_date = None
        test_now = Mock()

        test_config = {'test': 'config'}
        test_tweeted = True

        mock_date_object = Mock()
        mock_get_200.return_value = mock_date_object

        mock_list = ['play 1', 'play 2']
        mock_query.return_value = mock_list

        test_list = check_by_date(
            test_config, test_now, test_date, test_tweeted
            )
        self.assertEqual(test_list, mock_list)

        mock_get_200.assert_called_once_with(test_now)
        mock_query.assert_called_once_with(
            test_config, mock_date_object, test_tweeted
            )
        mock_get_date.assert_not_called()

    @patch('tweet.query_by_date')
    @patch('tweet.get_200_years_ago')
    @patch('tweet.get_date_object')
    def test_check_by_date_first(self, mock_get_date, mock_get_200, mock_query):
        test_date = '12-10-1818'
        test_now = Mock()

        test_config = {'test': 'config'}
        test_tweeted = True

        mock_date_object = Mock()
        mock_first_object = Mock()
        mock_date_object.replace.return_value = mock_first_object
        mock_get_date.return_value = mock_date_object

        get_date_calls = [
            call(test_config, mock_date_object, test_tweeted),
            call(test_config, mock_first_object, test_tweeted, limit=1)
            ]

        mock_list = ['play 1', 'play 2']
        mock_query.side_effect = [[], mock_list]

        with self.assertLogs(level="INFO"):
            test_list = check_by_date(
                test_config, test_now, test_date, test_tweeted
                )
        self.assertEqual(test_list, mock_list)

        mock_get_date.assert_called_once_with(test_date)
        mock_query.assert_has_calls(get_date_calls)
        mock_get_200.assert_not_called()

    @patch('tweet.Play')
    @patch('tweet.expand_abbreviation')
    @patch('tweet.get_200_years_ago')
    def test_get_play(self, mock_get_200, mock_expand, mock_play_class):
        mock_cursor = Mock()
        mock_now = Mock()

        test_genre = 'test genre'
        test_dict = {'test': 'dict', 'genre': test_genre}

        mock_old_date = Mock()
        mock_get_200.return_value = mock_old_date

        test_expanded_genre = 'test expanded genre'
        mock_expand.return_value = test_expanded_genre

        mock_play = Mock()
        mock_play_class.from_dict.return_value = mock_play

        with self.assertLogs(level="INFO"):
            test_play = get_play(mock_cursor, mock_now, test_dict)

        self.assertEqual(test_play, mock_play)

        mock_get_200.assert_called_once_with(mock_now)
        mock_expand.assert_called_once_with(mock_cursor, test_genre)

        print(mock_play_class.mock_calls)

        mock_play.from_dict.assert_called_once_with(test_dict)
        mock_play.set_today.assert_called_once_with(mock_old_date)
        mock_play.set_expanded_genre.assert_called_once_with(
            test_expanded_genre
            )

    @patch('tweet.check_by_date')
    @patch('tweet.query_by_wicks_id')
    def test_get_play_list(self, mock_query, mock_check):
        test_config = {'test': 'config'}
        test_wicks = True

        mock_now = Mock()
        test_date = 'test date'
        test_tweeted = False

        mock_list = ['play1', 'play2']
        mock_query.return_value = mock_list

        test_list = get_play_list(
            test_config, test_wicks, mock_now, test_date, test_tweeted)
        self.assertListEqual(mock_list, test_list)


    @patch('tweet.send_tweet')
    @patch('tweet.check_books_api')
    @patch('tweet.get_play')
    @patch('tweet.is_time_to_tweet')
    @patch('tweet.get_play_list')
    def test_main(self, mock_list, mock_time, mock_play, mock_check, mock_send):
        self.assertTrue(False)



if __name__ == '__main__':
    main()
