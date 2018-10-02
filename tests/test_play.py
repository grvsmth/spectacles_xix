from copy import deepcopy
from datetime import datetime
from unittest import TestCase, main
from unittest.mock import call, patch

from play import(
    EXPAND_FORMAT, GENRE_TEMPLATE, GENRE_ACT_FORMAT_TEMPLATE, TEMPLATE,
    au_theater, expand_format, par_auteur, musique_de, Play
    )

TEST_DICT = {
    'id': 999,
    'wicks': 9999,
    'author': 'Foo & Bar',
    'title': 'Arlequin le Baz',
    'acts': '3',
    'format': 'tabl',
    'music': None,
    'genre': 'op.-com',
    'theater_code': 'TMA',
    'theater_name': '',
    'greg_date': datetime.strptime('01-01-1818', "%d-%m-%Y").date(),
    'rev_date': None,
    'ce_jour_la': ''
    }


class TestMunge(TestCase):

    def test_au_theater(self):
        in_theater = 'Cirque du Soleil'
        target_theater = 'au Cirque du Soleil'
        out_theater = au_theater(in_theater)
        self.assertEqual(out_theater, target_theater)

    def test_au_theater_blank(self):
        in_theater = None
        target_theater = ''
        out_theater = au_theater(in_theater)
        self.assertEqual(out_theater, target_theater)

    def test_par_auteur(self):
        in_text = 'Cirque du Soleil'
        target_text = ' par Cirque du Soleil,'
        out_text = par_auteur(in_text)
        self.assertEqual(out_text, target_text)

    def test_par_auteur_blank(self):
        in_text = None
        target_text = ''
        out_text = par_auteur(in_text)
        self.assertEqual(out_text, target_text)

    def test_musique_de(self):
        in_text = 'Soleil'
        target_text = ' musique de Soleil,'
        out_text = musique_de(in_text)
        self.assertEqual(out_text, target_text)

    def test_musique_de_vowel(self):
        in_text = 'oleil'
        target_text = " musique d'oleil,"
        out_text = musique_de(in_text)
        self.assertEqual(out_text, target_text)

    def test_musique_de_blank(self):
        in_text = None
        target_text = ''
        out_text = musique_de(in_text)
        self.assertEqual(out_text, target_text)

    def test_expand_format_singular(self):
        test_acts = 1
        test_format = 'a'
        target_text = EXPAND_FORMAT['singular'][test_format]
        test_text = expand_format(test_acts, test_format)
        self.assertEqual(test_text, target_text)

    def test_expand_format_plural(self):
        test_acts = 5
        test_format = 'tabl'
        target_text = EXPAND_FORMAT['plural'][test_format]
        test_text = expand_format(test_acts, test_format)
        self.assertEqual(test_text, target_text)


class TestPlay(TestCase):

    def setUp(self):
        self.test_id = 555
        self.test_wicks = '7777a'
        self.test_day = TEST_DICT['greg_date']
        self.play = Play(self.test_id, self.test_wicks)

    def test_init(self):
        test_play = Play(self.test_id, self.test_wicks)
        self.assertEqual(self.test_id, test_play.id)
        self.assertEqual(self.test_wicks, test_play.wicks)

    def test_from_dict(self):
        in_dict = TEST_DICT
        additional_fields = {
            'expanded_genre': '',
            'genre_phrase': ''
            }
        out_dict = deepcopy(TEST_DICT)
        out_dict['play_format'] = out_dict.pop('format')
        out_dict.update(additional_fields)
        play = Play.from_dict(in_dict)
        self.assertDictEqual(play.__dict__, out_dict)

    def test_set_expanded_genre(self):
        test_genre = "Geeenre"
        self.play.set_expanded_genre(test_genre)
        self.assertEqual(self.play.expanded_genre, test_genre)

    def test_set_today_true(self):
        test_today = self.test_day
        target_ce_jour_la = ' #CeJourLà'

        self.play.greg_date = self.test_day
        self.play.set_today(test_today)

        self.assertEqual(self.play.ce_jour_la, target_ce_jour_la)

    def test_set_today_false(self):
        test_today = '09-30-1818'
        target_ce_jour_la = ''

        self.play.greg_date = self.test_day
        self.play.set_today(test_today)

        self.assertEqual(self.play.ce_jour_la, target_ce_jour_la)

    def test_build_genre_phrase_blank(self):
        self.play.play_format = ''
        target_genre_phrase = ''

        self.play.build_genre_phrase()
        self.assertEqual(self.play.genre_phrase, target_genre_phrase)

    def test_build_genre_phrase_provided(self):
        self.play.play_format = ''
        test_genre = 'foo'

        target_genre_phrase = GENRE_TEMPLATE.format(test_genre)
        self.play.build_genre_phrase(test_genre)

        self.assertEqual(self.play.genre_phrase, target_genre_phrase)

    @patch('play.au_theater')
    def test_build_theater_string_from_name(self, mock_au_theater):
        test_name = 'test name'
        test_code = 'test code'

        self.play.theater_name = test_name
        self.play.theater_code = test_code

        test_theater_string = 'test string'
        mock_au_theater.return_value = test_theater_string

        self.play.build_theater_string()

        self.assertEqual(self.play.theater_string, test_theater_string)
        mock_au_theater.assert_called_once_with(test_name)

    @patch('play.au_theater')
    def test_build_theater_string_from_code(self, mock_au_theater):
        test_name = ''
        test_code = 'test code'

        self.play.theater_name = test_name
        self.play.theater_code = test_code

        test_theater_string = 'test string'
        mock_au_theater.return_value = test_theater_string

        self.play.build_theater_string()

        self.assertEqual(self.play.theater_string, test_theater_string)
        mock_au_theater.assert_called_once_with(test_code)

    @patch('play.Play.build_genre_phrase')
    def test_build_expanded_genre_phrase_not_really(self, mock_build):
        test_genre = 'op'
        test_expanded_genre = ''
        self.play.genre = test_genre
        self.play.expanded_genre = test_expanded_genre

        self.play.build_expanded_genre_phrase()

        mock_build.assert_called_once_with(test_genre)

    @patch('play.Play.build_genre_phrase')
    def test_build_expanded_genre_phrase(self, mock_build):
        test_genre = 'op'
        test_expanded_genre = 'opéraa'
        self.play.genre = test_genre
        self.play.expanded_genre = test_expanded_genre

        self.play.build_expanded_genre_phrase()

        mock_build.assert_called_once_with(test_expanded_genre)

    @patch('play.expand_format')
    def test_build_genre_phrase_with_format(self, mock_expand):
        test_genre = 'foo'
        test_format = 'a'
        test_acts = 5
        test_expanded_format = 'acts'

        self.play.play_format = test_format
        self.play.acts = test_acts
        self.play.genre = test_genre
        mock_expand.return_value = test_expanded_format

        target_genre_phrase = GENRE_ACT_FORMAT_TEMPLATE.format(
            test_genre, test_acts, test_expanded_format
            )

        self.play.build_genre_phrase()

        self.assertEqual(self.play.genre_phrase, target_genre_phrase)
        mock_expand.assert_called_once_with(test_acts, test_format)

    @patch('play.expand_format')
    def test_build_genre_phrase_provided_with_format(self, mock_expand):
        test_genre = 'foo'
        test_format = 'tabl'
        test_acts = 3
        test_expanded_format = 'tablooo'

        self.play.play_format = test_format
        self.play.acts = test_acts
        mock_expand.return_value = test_expanded_format

        target_genre_phrase = GENRE_ACT_FORMAT_TEMPLATE.format(
            test_genre, test_acts, test_expanded_format
            )
        self.play.build_genre_phrase(test_genre)

        self.assertEqual(self.play.genre_phrase, target_genre_phrase)
        mock_expand.assert_called_once_with(test_acts, test_format)

    @patch('play.Play.build_expanded_genre_phrase')
    @patch('play.par_auteur')
    @patch('play.musique_de')
    @patch('play.au_theater')
    def test_build_phrases(self, m_au, m_musique, m_par, m_build):
        target_date_string = 'samedi le 03 octobre 1818'

        test_theater_name = 'Théâtre des Maréchaux'
        target_theater_string = 'au Théâtre des Maréchaux'

        test_music = 'Aznavour'
        target_music_string = "musique d'Aznavour"
        target_author_string = 'par Foo & Bar'

        m_au.return_value = target_theater_string
        m_musique.return_value = target_music_string
        m_par.return_value = target_author_string

        test_play = Play.from_dict(TEST_DICT)
        test_play.music = test_music
        test_play.greg_date = datetime.strptime('03-10-1818', "%d-%m-%Y").date()
        test_play.theater_name = test_theater_name

        test_play.build_phrases()

        self.assertEqual(test_play.date_string, target_date_string)
        self.assertEqual(test_play.theater_string, target_theater_string)
        self.assertEqual(test_play.music_string, target_music_string)
        self.assertEqual(test_play.author_string, target_author_string)

        m_au.assert_called_once_with(test_theater_name)
        m_musique.assert_called_once_with(test_music)
        m_par.assert_called_once_with(TEST_DICT['author'])
        m_build.assert_called_once_with()


class TestRepr(TestCase):

    def setUp(self):
        self.test_play = Play.from_dict(TEST_DICT)
        self.test_play.build_phrases()

    @patch('play.Play.build_genre_phrase')
    def test_repr(self, mock_build):
        target_description = TEMPLATE['basic'].format(self.test_play)
        test_description = str(self.test_play)
        self.assertEqual(test_description, target_description)
        mock_build.assert_not_called()

    @patch('play.Play.build_genre_phrase')
    def test_repr_greater_than_280(self, mock_build):
        self.test_play.title = 'La pièce avec le très très très très très très très long titre'
        self.test_play.build_phrases()
        target_description = TEMPLATE['basic'].format(self.test_play)
        test_description = str(self.test_play)
        self.assertEqual(test_description, target_description)
        mock_build.assert_called_once_with(TEST_DICT['genre'])

    @patch('play.Play.build_genre_phrase')
    def test_repr_greater_than_280_with_short_genre(self, mock_build):
        self.test_play.title = 'La pièce avec le très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très très long titre'
        self.test_play.build_phrases()
        target_description = TEMPLATE['shorter'].format(self.test_play)
        test_description = str(self.test_play)
        self.assertEqual(test_description, target_description)
        mock_build.assert_has_calls([call(TEST_DICT['genre']), call()])


if __name__ == '__main__':
    main()
