from copy import deepcopy
from unittest import TestCase, main

from play import au_theater, par_auteur, musique_de, Play

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
    'greg_date': '01-01-1818',
    'rev_date': None
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

    def test_musique_de_blank(self):
        in_text = None
        target_text = ''
        out_text = musique_de(in_text)
        self.assertEqual(out_text, target_text)

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
        out_dict = deepcopy(TEST_DICT)
        out_dict['play_format'] = out_dict.pop('format')
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


if __name__ == '__main__':
    main()
