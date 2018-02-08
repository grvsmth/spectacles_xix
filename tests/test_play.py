import unittest

from play import au_theater, par_auteur

class TestMunge(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()
