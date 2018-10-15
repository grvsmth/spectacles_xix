from unittest import TestCase, main
from unittest.mock import Mock, patch

from spectacles_xix.tweet import(
    get_hours_per_tweet,
    is_time_to_tweet,
    get_oauth,
    upload_image,
    send_tweet
    )


class TestTime(TestCase):

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

    @patch('spectacles_xix.tweet.get_hours_per_tweet')
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

    @patch('spectacles_xix.tweet.get_hours_per_tweet')
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

    @patch('spectacles_xix.tweet.get_hours_per_tweet')
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

    @patch('spectacles_xix.tweet.get_hours_per_tweet')
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

    @patch('spectacles_xix.tweet.get_hours_per_tweet')
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

    @patch('spectacles_xix.tweet.get_hours_per_tweet')
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

    @patch('spectacles_xix.tweet.get_hours_per_tweet')
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

    @patch('spectacles_xix.tweet.OAuth')
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

    @patch('spectacles_xix.tweet.Twitter')
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

    @patch('spectacles_xix.tweet.Twitter')
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

    @patch('spectacles_xix.tweet.Twitter')
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

    @patch('spectacles_xix.tweet.tweet_db')
    @patch('spectacles_xix.tweet.upload_image')
    @patch('spectacles_xix.tweet.Twitter')
    @patch('spectacles_xix.tweet.get_oauth')
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

    @patch('spectacles_xix.tweet.tweet_db')
    @patch('spectacles_xix.tweet.upload_image')
    @patch('spectacles_xix.tweet.Twitter')
    @patch('spectacles_xix.tweet.get_oauth')
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

    @patch('spectacles_xix.tweet.tweet_db')
    @patch('spectacles_xix.tweet.upload_image')
    @patch('spectacles_xix.tweet.Twitter')
    @patch('spectacles_xix.tweet.get_oauth')
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


if __name__ == '__main__':
    main()
