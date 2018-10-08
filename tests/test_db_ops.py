from unittest import TestCase, main

from db_ops import abbrev_db, db_cursor, load_from_db, tweet_db


class TestDB(TestCase):

    def test_tweet_db(self):
        mock_cursor = Mock()

        self.assertTrue(False)


if __name__ == '__main__':
    main()