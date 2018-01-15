"""
Play - class for storing information about plays
"""

TEMPLATE = {
    'basic': '{0.title},{0.author_string} {0.gaf},{0.music_string} a débuté {0.date} {0.theater_string}. Wicks {0.wicks}.',
    'short': '{0.title},{0.author_string} {0.gaf},{0.music_string} a débuté {0.date} {0.theater_string}. Wicks {0.wicks}.'
    }

EXPAND_FORMAT = {
    'singulier': {'a': 'acte', 'tabl': 'tableau'},
    'pluriel': {'a': 'actes', 'tabl': 'tableaux'}
}

def au_theater(name):
    """
    Add a preposition and article to a theater name to make it locative
    """
    loc = {
        'Théâtre': 'au ',
        'Académie': "à l'",
        'Cirque': 'au ',
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
    def __init__(self, row=None, date=None, genre=None):
        if row:
            self.id = row['id']
            self.wicks = row['wicks']
            self.title = row.get('title')
            self.author = row.get('author')
            self.genre = row.get('genre')
            self.acts = row.get('acts')
            self.format = row.get('format')
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

    def genre_phrase(self):
        """
        Generate genre and number of acts
        """
        gaf = self.genre
        if self.format:
            format = EXPAND_FORMAT['pluriel'][self.format]
            if self.acts == 1:
                format = EXPAND_FORMAT['singulier'][self.format]
            gaf = "{} en {} {}".format(self.genre, self.acts, format)

        return gaf

    def short_genre_phrase(self):
        """
        Generate short genre phrase
        """
        sgaf = self.abbrev_genre
        if self.format:
            sgaf = "{} en {} {}".format(
                self.abbrev_genre,
                self.acts,
                self.format
                )

        return sgaf

    def __repr__(self):
        """
        Generate description for tweet
        """
        self.description = TEMPLATE['basic'].format(self)
        if len(self.description) > 280:
            print("Description for play {} is too long ({} characters)".format(
                self.id,
                len(self.description)
                ))
            self.sgaf = self.short_genre_phrase()
            self.description = TEMPLATE['short'].format(self)
        if len(self.description) > 280:
            print("Description for play {} is STILL too long ({} characters)".format(
                self.id,
                len(self.description)
                ))
            self.description = self.title

        return self.description