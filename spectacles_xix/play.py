"""
Play - class for storing information about plays
"""
from locale import LC_TIME, setlocale
from logging import basicConfig, getLogger

EXPAND_FORMAT = {
    'singular': {'a': 'acte', 'tabl': 'tableau'},
    'plural': {'a': 'actes', 'tabl': 'tableaux'}
}

BASIC_TEMPLATE = '{title},{author_string}{genre_phrase}{music_string} a\
 débuté{ce_jour_la} {date_string} {theater_string}. Wicks nº. {wicks}.'
SHORTER_TEMPLATE = '{title}, {author}{ce_jour_la} {date_string} {theater_code}.\
 Wicks nº. {wicks}.'

GENRE_TEMPLATE = " {},"
GENRE_ACT_FORMAT_TEMPLATE = " {} en {} {},"

TIMEZONE = 'Europe/Paris'
DATE_FORMAT = "%A le %d %B %Y"
setlocale(LC_TIME, "fr_FR")

basicConfig(level="DEBUG")
LOG = getLogger(__name__)


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
    return loc.get(first_word, '') + name


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
    if name and name[0].lower() in 'aeiouy':
        music_phrase = " musique d'{},".format(name)
    elif name:
        music_phrase = " musique de {},".format(name)

    return music_phrase

def expand_format(acts, play_format):
    """
    Retrieve the expanded format, depending on whether the number of acts is
    singular or plural
    """
    if acts == 1:
        return EXPAND_FORMAT['singular'][play_format]

    return EXPAND_FORMAT['plural'][play_format]


class Play:
    """
    Store information about a play in the corpus
    """
    def __init__(self, play_id, wicks):
        self.play_id = play_id
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
        self.date_string = ''
        self.theater_name = ''
        self.theater_code = ''
        self.theater_string = ''
        self.ce_jour_la = ''
        self.greg_date = None

    @classmethod
    def from_dict(cls, row):
        """
        Given a dict input,
        """
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

    def get_expanded_genre_phrase(self):
        """
        Generate genre and number of acts
        """
        genre = self.genre
        if self.expanded_genre:
            genre = self.expanded_genre

        return self.get_genre_phrase(genre)

    def get_genre_phrase(self, genre=None):
        """
        Generate short genre phrase
        """
        genre_phrase = ''
        if not genre:
            genre = self.genre

        if not genre:
            return genre_phrase

        if self.play_format:
            expanded_format = expand_format(self.acts, self.play_format)
            genre_phrase = GENRE_ACT_FORMAT_TEMPLATE.format(
                genre, self.acts, expanded_format
                )
        else:
            genre_phrase = GENRE_TEMPLATE.format(genre)

        return genre_phrase

    def get_theater_string(self):
        """
        Run the theater name through au_theater(), or the code if there is no
        name found
        """
        if self.theater_name:
            return au_theater(self.theater_name)

        return au_theater(self.theater_code)

    def get_dict(self):
        """
        Generate a dictionary of values that can be used as input to a format
        string for __repr__()
        """
        play_dict = {
            'title': self.title,
            'author_string': par_auteur(self.author),
            'genre_phrase': self.get_expanded_genre_phrase(),
            'music_string': musique_de(self.music),
            'ce_jour_la': self.ce_jour_la,
            'date_string': self.greg_date.strftime(DATE_FORMAT),
            'theater_string': self.get_theater_string(),
            'wicks': self.wicks
            }
        return play_dict

    def __repr__(self):
        """
        Generate description for tweet
        """
        play_dict = self.get_dict()
        description = BASIC_TEMPLATE.format(**play_dict)
        if len(description) > 280:
            LOG.warning("Description for play {} is too long ({} characters)".format(
                self.play_id,
                len(description)
                ))
            play_dict['genre_phrase'] = self.get_genre_phrase()
            description = BASIC_TEMPLATE.format(**play_dict)

            if len(description) > 280:
                LOG.warning("Description for {} is STILL too long ({} characters)".format(
                    self.play_id,
                    len(description)
                    ))

                play_dict['theater_code'] = self.theater_code
                description = SHORTER_TEMPLATE.format(**play_dict)

        return description
