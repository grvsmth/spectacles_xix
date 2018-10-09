from unittest import TestCase, main
from unittest.mock import Mock

from MySQLdb import DatabaseError

from db_ops import(
    abbreviation_db,
    db_cursor,
    play_db,
    query_by_wicks_id,
    query_by_date,
    query_play,
    tweet_db
    )

class TestDB(TestCase):

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

        mock_result = [
            ('test 1', 'test 2', 'test 3', 4),
            ('test 1a', 'test 2a', 'test 3a', 5)
            ]

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_result

        test_result = play_db(mock_cursor, test_query_string, test_lookup_term)

        self.assertEqual(mock_result, test_result)



if __name__ == '__main__':
    main()