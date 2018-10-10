from unittest import TestCase, main
from unittest.mock import patch

from tweet import check_by_date


class TestTweet(TestCase):

    @patch('tweet.query_by_date')
    def test_check_by_date(self, mock_query):
        self.assertTrue(False)


if __name__ == '__main__':
    main()
