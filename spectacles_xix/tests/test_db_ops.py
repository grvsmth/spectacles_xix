from datetime import datetime
from unittest import TestCase, main
from unittest.mock import Mock, patch

from dateutil import relativedelta
from MySQLdb import DatabaseError

from db_ops import(
    NOT_TWEETED_CONDITION,
    PLAY_SELECT,
    abbreviation_db,
    play_db,
    query_by_wicks_id,
    query_by_date,
    query_play,
    tweet_db
    )

class TestQuery(TestCase):

    def setUp(self):
        self.mock_result = [
            ('test 1', 'test 2', 'test 3', 4),
            ('test 1a', 'test 2a', 'test 3a', 5)
            ]
        self.config = {'test 1': 'test 2'}
        self.date = datetime.now().date() + relativedelta.relativedelta(
            years=-200
            )


    def test_tweet_db(self):
        mock_cursor = Mock()

        test_play_id = 56768

        tweet_db(mock_cursor, test_play_id)
        self.assertEqual(mock_cursor.mock_calls[0][1][1][1], test_play_id)

    def test_tweet_db_error(self):
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = DatabaseError

        test_play_id = 56768

        with self.assertLogs(level="ERROR"):
            tweet_db(mock_cursor, test_play_id)

        self.assertEqual(mock_cursor.mock_calls[0][1][1][1], test_play_id)

    def test_abbreviation_db(self):
        test_abbreviation = 'tst'
        mock_expansion = 'test'

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (mock_expansion,)

        test_expansion = abbreviation_db(mock_cursor, test_abbreviation)

        self.assertEqual(test_expansion, mock_expansion)
        self.assertEqual(
            mock_cursor.execute.mock_calls[0][1][1], [test_abbreviation]
            )
        mock_cursor.fetchone.assert_called_once()

    def test_abbreviation_db_empty(self):
        test_abbreviation = ''
        mock_expansion = ''

        mock_cursor = Mock()

        test_expansion = abbreviation_db(mock_cursor, test_abbreviation)

        self.assertEqual(test_expansion, mock_expansion)
        mock_cursor.execute.assert_not_called()
        mock_cursor.fetchone.assert_not_called()

    def test_abbreviation_db_no_result(self):
        test_abbreviation = 'tst'

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = []

        test_expansion = abbreviation_db(mock_cursor, test_abbreviation)

        self.assertEqual(test_expansion, test_abbreviation)
        self.assertEqual(
            mock_cursor.execute.mock_calls[0][1][1], [test_abbreviation]
            )
        mock_cursor.fetchone.assert_called_once()

    def test_abbreviation_db_error(self):
        test_abbreviation = 'tst'

        mock_cursor = Mock()
        mock_cursor.execute.side_effect = DatabaseError()

        with self.assertLogs(level="ERROR"):
            test_expansion = abbreviation_db(mock_cursor, test_abbreviation)

        self.assertEqual(test_expansion, test_abbreviation)
        self.assertEqual(
            mock_cursor.execute.mock_calls[0][1][1], [test_abbreviation]
            )
        mock_cursor.fetchone.assert_not_called()

    def test_play_db(self):
        test_query_string = 'query string'
        test_lookup_term = 'lookup term'

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = self.mock_result

        test_result = play_db(mock_cursor, test_query_string, test_lookup_term)

        self.assertEqual(self.mock_result, test_result)
        mock_cursor.execute.assert_called_once_with(
            test_query_string, [test_lookup_term]
            )
        mock_cursor.fetchall.assert_called_once_with()

    def test_play_db_empty(self):
        test_query_string = 'query string'
        test_lookup_term = 'lookup term'

        mock_result = []
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_result

        with self.assertLogs(level="INFO"):
            test_result = play_db(
                mock_cursor, test_query_string, test_lookup_term
                )

        self.assertEqual(mock_result, test_result)
        mock_cursor.execute.assert_called_once_with(
            test_query_string, [test_lookup_term]
            )
        mock_cursor.fetchall.assert_called_once_with()

    def test_play_db_error(self):
        test_query_string = 'query string'
        test_lookup_term = 'lookup term'

        mock_result = []
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = DatabaseError()

        with self.assertLogs(level="ERROR"):
            test_result = play_db(
                mock_cursor, test_query_string, test_lookup_term
                )

        self.assertEqual(mock_result, test_result)
        mock_cursor.execute.assert_called_once_with(
            test_query_string, [test_lookup_term]
            )
        mock_cursor.fetchall.assert_not_called()

    @patch('db_ops.DictCursor')
    @patch('db_ops.play_db')
    @patch('db_ops.db_cursor')
    def test_query_play(self, mock_db_cursor, mock_play, mock_dict_cursor):
        test_query_string = 'test query string'
        test_lookup_term = 'test term'

        mock_play.return_value = self.mock_result

        mock_cursor = Mock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor

        test_result = query_play(
            self.config, test_query_string, test_lookup_term
            )
        self.assertEqual(test_result, self.mock_result)

        mock_db_cursor.assert_called_once_with(
            self.config, cursorclass=mock_dict_cursor
            )
        mock_play.assert_called_once_with(
            mock_cursor, test_query_string, test_lookup_term
            )

    @patch('db_ops.query_play')
    def test_query_by_wicks_id(self, mock_query):
        test_wicks_id = 9999
        target_query_string = '{}\nWHERE wicks = %s\n{}'.format(
            PLAY_SELECT, NOT_TWEETED_CONDITION
            )

        mock_query.return_value = self.mock_result

        test_result = query_by_wicks_id(self.config, test_wicks_id)

        self.assertEqual(test_result, self.mock_result)
        mock_query.assert_called_once_with(
            self.config, target_query_string, test_wicks_id
            )

    @patch('db_ops.query_play')
    def test_query_by_wicks_id_tweeted(self, mock_query):
        test_wicks_id = 9999
        target_query_string = '{}\nWHERE wicks = %s\n'.format(
            PLAY_SELECT
            )

        mock_query.return_value = self.mock_result

        test_result = query_by_wicks_id(
            self.config, test_wicks_id, tweeted=True
            )

        self.assertEqual(test_result, self.mock_result)
        mock_query.assert_called_once_with(
            self.config, target_query_string, test_wicks_id
            )

    @patch('db_ops.query_play')
    def test_query_by_date(self, mock_query):
        test_date = self.date
        target_query_string = '{}\nWHERE greg_date = %s\n{}\n'.format(
            PLAY_SELECT, NOT_TWEETED_CONDITION
            )

        mock_query.return_value = self.mock_result

        test_result = query_by_date(self.config, test_date)

        self.assertEqual(test_result, self.mock_result)
        mock_query.assert_called_once_with(
            self.config, target_query_string, test_date.isoformat()
            )

    @patch('db_ops.query_play')
    def test_query_by_date_limit(self, mock_query):
        test_date = self.date
        target_query_string = '{}\nWHERE greg_date = %s\n{}\nLIMIT 1'.format(
            PLAY_SELECT, NOT_TWEETED_CONDITION
            )

        mock_query.return_value = self.mock_result

        test_result = query_by_date(self.config, test_date, limit=500)

        self.assertEqual(test_result, self.mock_result)
        mock_query.assert_called_once_with(
            self.config, target_query_string, test_date.isoformat()
            )

    @patch('db_ops.query_play')
    def test_query_by_date_tweeted(self, mock_query):
        target_query_string = '{}\nWHERE greg_date = %s\n\n'.format(
            PLAY_SELECT
            )
        test_date = self.date

        mock_query.return_value = self.mock_result

        test_result = query_by_date(
            self.config, test_date, tweeted=True
            )

        self.assertEqual(test_result, self.mock_result)
        mock_query.assert_called_once_with(
            self.config, target_query_string, test_date.isoformat()
            )


if __name__ == '__main__':
    main()