import random
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar
from lib.platform.datamanager import get_data_manager
from lib.ui.add_to_playlist_dialog import AddToPlaylistDialog
from kivymd.app import MDApp
from lib.localization import localization
from datetime import date
from lib.util import show_snackbar, truncate_text
from kivy.clock import Clock
from kivy.logger import Logger
from lib.playlist import Playlist

from kivy.utils import platform

random.seed(date.today().month*100 + date.today().day)

class PlaylistBar(MDBoxLayout):
    '''
    Class for the bar that play a playlist.
    It show the title, artist and an image of the current playing song.
    

    Attributes
    ----------
    song_name : MDLabel
        Label for the playing song
    song_field : MDLabel
        Label for the subtitle of the song(eg. the album)
    image : FitImage
        Image of the album
    next_song : MDIconButton
        Button the reproduce the next song
    pause_song : MDIconButton
        Button that pause the song
    shuffle_playlist : MDIconButton
        Button that shuffle the playlist. It iterrupt the current song
    add_song_to : MDIconButton
        Button that open the dialog for adding the song to a playlist

    Methods
    -------
    select_playlist(list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]])
        Select the playlist to play. It creates a copy of it in order to shuffle it without side effects and close the previous song.
.   play()
        Run the playlist
    play_pause(state=None) -> None
        Pause or resume the current song. If state is None the state is reversed.
    '''
    song_name = ObjectProperty(None)
    '''Label for the playing song'''

    song_field = ObjectProperty(None)
    '''Label for the subtitle of the song(eg. the album)'''

    image = ObjectProperty(None)
    '''Image of the album'''

    next_song = ObjectProperty(None)
    '''Button the reproduce the next song'''

    pause_song = ObjectProperty(None)
    '''Button that pause the song'''

    shuffle_playlist = ObjectProperty(None)
    '''Button that shuffle the playlist. It iterrupt the current song'''

    add_song_to = ObjectProperty(None)
    '''Button that open the dialog for adding the song to a playlist'''

    playlist: Playlist = None
    '''List the contains the song to play.  '''

    def __init__(self):
        super().__init__()
        self.pause_song.bind(on_press=lambda _: self.play_pause())
        self.next_song.bind(on_press=self.on_next_pressed)
        self.shuffle_playlist.bind(on_press=self.__on_shuffle)
        self.add_song_to.bind(on_press=self.__on_added_to_playlist)
    
    def update_labels(self):
        '''Update the labels to the current playing song. Must be called in the kivy thread'''
        data_manager = get_data_manager()
        self.image.source = data_manager.get_image([self.playlist.current_song["file"]])
        self.song_name.text = truncate_text(self.playlist.current_song["title"], 2, 15, self.song_name.size[0])
        self.song_field.text = truncate_text(self.playlist.current_song["album"], 1, 15, self.song_field.size[0])

    def select_playlist(self, data: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]) -> None: 
        '''Select the playlist to play. It creates a copy of it in order to shuffle it without side effects and close the previous song.

        Parameters
        ----------
        data : list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]
            The songs of the playlist
        '''
        if self.playlist is not None:
            self.playlist.close()
        self.playlist = Playlist(data, on_song_changed=lambda: self.update_labels(), on_state_changed=self.set_icon)

        if get_data_manager().store["config"]["shuffle"]:
            self.playlist.shuffle()
        self.pause_song.icon = "pause"

    def play(self):
        '''Run the playlist'''
        self.playlist.start()

    def play_pause(self, state=None) -> None:
        '''Pause or resume the current song. If state is None the state is reversed.

        Arguments
        ---------
        state : bool
            The desired state of the player. True if play, False for pause        
        '''
        self.playlist.play_pause(state)
        self.set_icon(self.playlist.player.state)

    def on_next_pressed(self, _):
        self.playlist.next()
        self.set_icon(self.playlist.player.state)
        

    def set_icon(self, state) -> None:
        if state:
            self.pause_song.icon = "pause"
        else:
            self.pause_song.icon = "play"

    def __on_shuffle(self, _):
        self.playlist.shuffle()
        self.playlist.next()

    def __on_added_to_playlist(self, _):
        data_manager = get_data_manager()
        def update_view():
            if data_manager.store["config"]["last_category"] == "playlist":
                MDApp.get_running_app().front.set_category("playlist", force_reload=True)

        AddToPlaylistDialog(self.playlist.current_song["id"], on_dialog_ended=update_view).show_dialog()
