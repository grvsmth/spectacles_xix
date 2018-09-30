"""
Play - class for storing information about plays
"""
import locale

TEMPLATE = {
    'basic': '{0.title},{0.author_string}{0.genre_phrase}{0.music_string} a débuté{0.ce_jour_la} {0.date_string} {0.theater_string}. Wicks nº. {0.wicks}.',
    'shorter': '{0.title},{0.author}{0.ce_jour_la} {0.date_string} {0.theater_code}. Wicks nº. {0.wicks}.'
    }

EXPAND_FORMAT = {
    'singular': {'a': 'acte', 'tabl': 'tableau'},
    'plural': {'a': 'actes', 'tabl': 'tableaux'}
}

GENRE_TEMPLATE = " {},"
GENRE_ACT_FORMAT_TEMPLATE = " {} en {} {},"

TIMEZONE = 'Europe/Paris'
DATE_FORMAT = "%A le %d %B %Y"
locale.setlocale(locale.LC_TIME, "fr_FR")


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
        music_phrase = " musique de {},".format(name)

    return music_phrase

def expand_format(acts, play_format):
    if acts == 1:
        return EXPAND_FORMAT['singular'][play_format]

    return EXPAND_FORMAT['plural'][play_format]


class Play:
    """
    Store information about a play in the corpus
    """
    def __init__(self, id, wicks):
        self.id = id
        self.wicks = wicks
        self.title = ''
        self.author = ''
        self.acts = ''
        self.play_format = ''
        self.genre = ''
        self.expanded_genre = ''
        self.genre_phrase = ''
        self.music = ''
        self.rev_date = ''
        self.theater_name = ''
        self.theater_code = ''
        self.greg_date = None

    @classmethod
    def from_dict(cls, row):
        play = cls(row['id'], row['wicks'])

        play.title = row.get('title')
        play.author = row.get('author')
        play.acts = row.get('acts')
        play.play_format = row.get('format')
        play.genre = row.get('genre')
        play.music = row.get('music')
        play.rev_date = row.get('rev_date')
        play.theater_name = row.get('theater_name')
        play.theater_code = row.get('theater_code')
        play.greg_date = row.get('greg_date')

        return play

    def set_expanded_genre(self, expanded_genre):
        """
        Set the genre
        """
        self.expanded_genre = expanded_genre


    def set_today(self, today):
        """
        Tell the object what today is, so it can determine whether to tweet
        #CeJourLà
        """
        self.ce_jour_la = ''
        if self.greg_date == today:
            self.ce_jour_la = ' #CeJourLà'

    def build_expanded_genre_phrase(self):
        """
        Generate genre and number of acts
        """
        genre = self.genre
        if self.expanded_genre:
            genre = self.expanded_genre

        self.build_genre_phrase(genre)

    def build_genre_phrase(self, genre=None):
        """
        Generate short genre phrase
        """
        if not genre:
            genre = self.genre

        if not genre:
            return

        if self.play_format:
            expanded_format = expand_format(self.play_format)
            self.genre_phrase = GENRE_ACT_FORMAT_TEMPLATE.format(
                genre, self.acts, expanded_format
                )
        else:
            self.genre_phrase = GENRE_TEMPLATE.format(genre)

    def build_phrases(self):
        """
        Expand theater, music and author into tweet-friendly strings
        """
        self.date_string = self.greg_date.strftime(DATE_FORMAT)
        self.theater_string = au_theater(self.theater_name)
        self.music_string = musique_de(self.music)
        self.author_string = par_auteur(self.author)
        self.build_expanded_genre_phrase()

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
            self.build_genre_phrase()
            self.description = TEMPLATE['basic'].format(self)
        if len(self.description) > 280:
            print("Description for play {} is STILL too long ({} characters)".format(
                self.id,
                len(self.description)
                ))
            self.description = TEMPLATE['shorter'].format(self)

        return self.description