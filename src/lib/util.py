from kivymd.uix.snackbar import Snackbar
from kivymd.uix.label import MDLabel
from kivy.uix.widget import Widget
import math
from kivy.metrics import dp
from nltk.metrics.distance import jaro_winkler_similarity

def show_snackbar(text: str, lines=2, font_size=15):
    '''Create and open a Snackbar. The text is autotruncated on the selected lines. Since the correct cut is not a linear function sometimes it may leave some character in a new line
    
    Arguments
    ---------
    text : str
        Text to show in the Snackbar
    lines : int
        The number of lines to show. If the text is longer, it's truncated and "..." is added in the end
    font_size : int
        The font size in dp to print the text
    '''
    from kivy.core.window import Window
    snack = Snackbar(text=truncate_text(text, lines, font_size, Window.size[0]), font_size=f"{font_size}dp")
    label: MDLabel =  snack.children[0]
    label.shorten = False
    snack.open()

def truncate_text(text: str, lines: int, font_size: int, widget_size: int) -> str:
    '''Truncate the text to match a space.
    
    Arguments
    ---------
    text : int
        The text to truncate if necessary
    lines : int
        Number of lines to leaves
    font_size : int
        The font size of the text
    widget_size : int
        The size of the widget in pixel that contains the string.

    Returns
    -------
    Return the truncated string
    '''
    
    character_for_line = (widget_size / dp(1)) / __calc_character_size_for_dp(font_size)
    if character_for_line > 0:
        num_lines = len(text) // character_for_line + 1
        if num_lines > lines:
            text = text[:round(lines*character_for_line)-3] + "..."
        return text
    return ""

def __calc_character_size_for_dp(font_size):
    # test with print(Window.size[0] / len(text), __calc_character_size_for_dp(font_size))
    # Manual regression that seems to work
    return  -17.991364 + 10.1636541 *math.log2(font_size)/math.log2(math.e) # 0.5105*font_size + 0.3321

def search(input: str, songs: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]], field="title", top=5, accepted_precentage=1):
    '''Search an input in a list of possible search text
    
    Arguments
    ---------
    input : str
        The value to search
    songs : list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]
        The list of songs to search the value
    field : str
        The attribute of song to search. Default "title"
    top : int
        Get only the first top results. Default 5
    accepted_percentage : float
        Accepted similarity for word. Default 0.3

    Returns
    -------
    Top songs ordered by rank
    
    '''
    words = input.lower().split(" ")
    def get_rank(other):
        rank = 0.0
        for w in words:
            val = 1-max([jaro_winkler_similarity(w ,o[: len(w)], max_l=2) for o in other])
            
            rank += val if val < accepted_precentage else 1
        return rank

    ranks = [(s, get_rank(s[field].lower().split(" "))) for s in songs]
    ranks = sorted(ranks, key=lambda x: x[1])
    return [r[0] for r in ranks][:top]
