from unittest import TestCase, main
from unittest.mock import Mock

from MySQLdb import DatabaseError

from db_ops import abbreviation_db, db_cursor, load_from_db, tweet_db


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


if __name__ == '__main__':
    main()