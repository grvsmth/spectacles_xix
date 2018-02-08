"""
Play - class for storing information about plays
"""

TEMPLATE = {
    'basic': '{0.title},{0.author_string}{0.gaf}{0.music_string} a débuté{0.ce_jour_la} {0.date} {0.theater_string}. Wicks nº. {0.wicks}.',
    'shorter': '{0.title},{0.author}{0.ce_jour_la} {0.date} {0.theater_code}. Wicks nº. {0.wicks}.'
    }

EXPAND_FORMAT = {
    'singulier': {'a': 'acte', 'tabl': 'tableau'},
    'pluriel': {'a': 'actes', 'tabl': 'tableaux'}
}

def au_theater(name):
    """
    Add a preposition and article to a theater name to make it locative
    """
    if not name:
        return ''
    loc = {
        'Théâtre': 'au ',
        'Th.': 'au ',
        'Académie': "à l'",
        'Cirque': 'au ',
        'Fêtes': 'aux ',
        'Cour': 'à la ',
        'Opéra-Comique-Nationale': "à l'"
        }
    first_word = name.split(' ')[0]
    return loc[first_word] + name

def par_auteur(name):
    """
    Add 'par' to the author names
    """
    author_phrase = ''
    if name:
        author_phrase = " par {},".format(name)
    return author_phrase

def musique_de(name):
    """
    Generate music phrase
    """
    music_phrase = ''
    if name:
        music_phrase = " musique de {}".format(name)

    return music_phrase

class Play:
    """
    """
    def __init__(self, row=None, date=None, genre=''):
        if row:
            self.id = row['id']
            self.wicks = row['wicks']
            self.title = row.get('title')
            self.author = row.get('author')
            self.acts = row.get('acts')
            self.play_format = row.get('format')
            self.genre = genre
            self.abbrev_genre = row.get('genre')
            self.music = row.get('music')
            self.rev_date = row.get('rev_date')
            self.theater_name = row.get('theater_name')
            self.theater_code = row.get('theater_code')
            self.theater_string = au_theater(row.get('theater_name'))
            self.music_string = musique_de(row.get('music'))
            self.author_string = par_auteur(row.get('author'))
            self.gaf = self.genre_phrase()
            self.date = date
            self.ce_jour_la = ''

    def set_today(self, today):
        """
        Tell the object what today is, so it can determine whether to tweet
        #CeJourLà
        """
        if self.date == today:
            self.ce_jour_la = ' #CeJourLà'

    def genre_phrase(self):
        """
        Generate genre and number of acts
        """
        if self.play_format:
            play_format = EXPAND_FORMAT['pluriel'][self.play_format]
            if self.acts == 1:
                play_format = EXPAND_FORMAT['singulier'][self.play_format]
            return " {} en {} {},".format(self.genre, self.acts, play_format)
        elif self.genre:
            return " {},".format(self.genre)

        return ''

    def short_genre_phrase(self):
        """
        Generate short genre phrase
        """
        if self.play_format:
            return " {} en {} {},".format(
                self.abbrev_genre,
                self.acts,
                self.play_format
                )
        elif self.abbrev_genre:
            return " {},".format(self.abbrev_genre)

        return ''

    def __repr__(self):
        """
        Generate description for tweet
        """
        if not self.theater_name:
            self.theater_string = au_theater(self.theater_code)
        self.description = TEMPLATE['basic'].format(self)
        if len(self.description) > 280:
            print("Description for play {} is too long ({} characters)".format(
                self.id,
                len(self.description)
                ))
            self.sgaf = self.short_genre_phrase()
            self.description = TEMPLATE['basic'].format(self)
        if len(self.description) > 280:
            print("Description for play {} is STILL too long ({} characters)".format(
                self.id,
                len(self.description)
                ))
            self.description = TEMPLATE['shorter'].format(self)

        return self.description