from kivymd.uix.snackbar import Snackbar
from kivymd.uix.label import MDLabel
from kivy.uix.widget import Widget
import math
from kivy.metrics import dp

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