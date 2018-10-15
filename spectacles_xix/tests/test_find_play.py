from unittest import TestCase, main
from unittest.mock import MagicMock, Mock, call, patch

from find_play import(
    INPUT_DATE_FORMAT,
    get_date_object,
    get_200_years_ago,
    check_by_date,
    get_replacements,
    expand_abbreviation,
    get_play_list,
    get_play,
    get_and_tweet
    )


class TestTime(TestCase):

    @patch('find_play.datetime')
    def test_get_date_object(self, mock_datetime):
        test_string = 'foo'

        mock_date_object = Mock()
        mock_datetime.strptime.return_value.date.return_value = mock_date_object

        test_date_object = get_date_object(test_string)
        self.assertEqual(test_date_object, mock_date_object)
        mock_datetime.strptime.assert_called_once_with(
            test_string, INPUT_DATE_FORMAT
            )

    @patch('find_play.relativedelta')
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


class TestDb(TestCase):

    def setUp(self):
        self.abbrev_match_list = [
            ('op', 'opéra'),
            ('com', 'comique')
            ]

    @patch('find_play.abbreviation_db')
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

    @patch('find_play.get_replacements')
    @patch('find_play.finditer')
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

    @patch('find_play.get_replacements')
    @patch('find_play.finditer')
    def test_expand_abbreviation_no_match(self, mock_finditer, mock_get):
        mock_cursor = Mock()
        mock_phrase = 'op.-com.'

        mock_abbrev_match = []
        mock_finditer.return_value = mock_abbrev_match

        test_expansion = expand_abbreviation(mock_cursor, mock_phrase)
        self.assertEqual(test_expansion, mock_phrase)

        mock_finditer.assert_called_once_with(r'(\w+)\.', mock_phrase)
        mock_get.assert_not_called()

    @patch('find_play.query_by_date')
    @patch('find_play.get_200_years_ago')
    @patch('find_play.get_date_object')
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

    @patch('find_play.query_by_date')
    @patch('find_play.get_200_years_ago')
    @patch('find_play.get_date_object')
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

    @patch('find_play.query_by_date')
    @patch('find_play.get_200_years_ago')
    @patch('find_play.get_date_object')
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

    @patch('find_play.Play')
    @patch('find_play.expand_abbreviation')
    @patch('find_play.get_200_years_ago')
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

        mock_play_class.from_dict.assert_called_once_with(test_dict)
        mock_play.set_today.assert_called_once_with(mock_old_date)
        mock_play.set_expanded_genre.assert_called_once_with(
            test_expanded_genre
            )

    @patch('find_play.check_by_date')
    @patch('find_play.query_by_wicks_id')
    def test_get_play_list(self, mock_query, mock_check):
        test_config = {'test': 'config'}
        test_wicks = True

        mock_now = Mock()
        test_date = 'test date'
        test_tweeted = False

        mock_list = ['play1', 'play2']
        mock_query.return_value = mock_list

        test_list = get_play_list(
            test_config, test_wicks, mock_now, test_date, test_tweeted
            )
        self.assertListEqual(mock_list, test_list)

        mock_query.assert_called_once_with(
            test_config, test_wicks, test_tweeted
            )
        mock_check.assert_not_called()

    @patch('find_play.check_by_date')
    @patch('find_play.query_by_wicks_id')
    def test_get_play_list_by_date(self, mock_query, mock_check):
        test_config = {'test': 'config'}
        test_wicks = False

        mock_now = Mock()
        test_date = 'test date'
        test_tweeted = False

        mock_list = ['play1', 'play2']
        mock_check.return_value = mock_list

        test_list = get_play_list(
            test_config, test_wicks, mock_now, test_date, test_tweeted
            )
        self.assertListEqual(mock_list, test_list)
        mock_query.assert_not_called()
        mock_check.assert_called_once_with(
            test_config, mock_now, test_date, test_tweeted
            )

    @patch('find_play.check_by_date')
    @patch('find_play.query_by_wicks_id')
    def test_get_play_list_empty(self, mock_query, mock_check):
        test_config = {'test': 'config'}
        test_wicks = False

        mock_now = Mock()
        test_date = 'test date'
        test_tweeted = False

        mock_list = []
        mock_check.return_value = mock_list

        test_list = get_play_list(
            test_config, test_wicks, mock_now, test_date, test_tweeted
            )
        self.assertEqual(test_list, mock_list)
        mock_query.assert_not_called()
        mock_check.assert_called_once_with(
            test_config, mock_now, test_date, test_tweeted
            )

    @patch('find_play.send_tweet')
    @patch('find_play.check_books_api')
    @patch('find_play.get_play')
    @patch('find_play.db_cursor')
    def test_get_and_tweet(self, mock_db, mock_get, mock_check, mock_send):
        test_book = True
        test_no_tweet = False

        test_config_db = {'config db': True}
        test_config_twitter = {'config_twitter': False}
        test_path = '/path/to/service/account'
        test_config = {
            'db': test_config_db,
            'path': {'google_service_account': test_path},
            'twitter': test_config_twitter
            }

        mock_now = Mock()
        test_play_dict = {'test play': True}

        mock_play = MagicMock()
        mock_description = 'Description'
        mock_play.__str__.return_value = mock_description
        mock_get.return_value = mock_play

        mock_result = Mock()
        mock_book_url = 'http://example.com/book/url'
        mock_result.get_better_book_url.return_value = mock_book_url

        mock_image = Mock()
        mock_result.get_image_file.return_value = mock_image

        mock_check.return_value = mock_result
        target_tweet = mock_description + ' ' + mock_book_url

        mock_cursor = Mock()
        mock_db.return_value.__enter__.return_value = mock_cursor

        get_and_tweet(
            test_book, test_no_tweet, test_config, mock_now, test_play_dict
            )

        mock_db.assert_called_with(test_config_db)
        mock_get.assert_called_once_with(
            mock_cursor, mock_now, test_play_dict
            )
        mock_check.assert_called_once_with(test_book, test_path, mock_play)
        mock_result.get_better_book_url.assert_called_once_with()
        mock_result.get_image_file.assert_called_once_with()

        mock_send.assert_called_once_with(
            mock_cursor,
            test_config_twitter,
            test_play_dict,
            target_tweet,
            mock_image
            )

    @patch('find_play.send_tweet')
    @patch('find_play.check_books_api')
    @patch('find_play.get_play')
    @patch('find_play.db_cursor')
    def test_get_and_tweet_no(self, mock_db, mock_get, mock_check, mock_send):
        test_book = True
        test_no_tweet = True

        test_config_db = {'config db': True}
        test_config_twitter = {'config_twitter': False}
        test_path = '/path/to/service/account'
        test_config = {
            'db': test_config_db,
            'path': {'google_service_account': test_path},
            'twitter': test_config_twitter
            }

        mock_now = Mock()
        test_play_dict = {'test play': True}

        mock_play = MagicMock()
        mock_description = 'Description'
        mock_play.__str__.return_value = mock_description
        mock_get.return_value = mock_play

        mock_result = Mock()
        mock_book_url = 'http://example.com/book/url'
        mock_result.get_better_book_url.return_value = mock_book_url

        mock_image = Mock()
        mock_result.get_image_file.return_value = mock_image

        mock_check.return_value = mock_result

        mock_cursor = Mock()
        mock_db.return_value.__enter__.return_value = mock_cursor

        get_and_tweet(
            test_book, test_no_tweet, test_config, mock_now, test_play_dict
            )

        mock_db.assert_called_with(test_config_db)
        mock_get.assert_called_once_with(
            mock_cursor, mock_now, test_play_dict
            )
        mock_check.assert_called_once_with(test_book, test_path, mock_play)
        mock_result.get_better_book_url.assert_not_called()
        mock_result.get_image_file.assert_not_called()

        mock_send.assert_not_called()


if __name__ == '__main__':
    main()
