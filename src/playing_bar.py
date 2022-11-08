import random
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar
from lib.platform.audioplayer import get_audio_player, AudioPlayer
from lib.platform.datamanager import get_data_manager
from lib.ui.add_to_playlist_dialog import AddToPlaylistDialog
from kivymd.app import MDApp
from mutagen.easyid3 import EasyID3
import os
from datetime import date
from util import show_snackbar, truncate_text
from kivy.clock import Clock

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
    index : int
        Index of the current song in the playlist
    player : lib.platform.audioplayer.AudioPlayer
        Player for the songs
    song : list[str]
        List the contains the song to play.        

    Methods
    -------
    select_playlist(dict["name":str, "image": str, "songs": list[str]]])
        Select the playlist to play. It creates a copy of it in order to shuffle it without side effects and close the previous song.
.   play() -> bool
        Play the song at index position stopping if necessary the current song. It loads the ID3 infos. If they are not avaliable try to reproduce the song without image and without title.
    next() -> None
        Play the next song. If the playlist reached the end it shuffle tha playlist and set index to 0.
    shuffle() -> None
        Shuffle tha playlist without resetting the current song or index
    close() -> None
        Close the player. It does not reset index
    pause(state=None) -> None
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

    index = 0
    '''Index of the current song in the playlist'''

    player: AudioPlayer = None
    '''Player for the songs'''

    songs: list[str] = []
    '''List the contains the song to play.  '''

    def __init__(self):
        super().__init__()
        self.pause_song.bind(on_press=lambda _: self.play_pause())
        self.next_song.bind(on_press=lambda _: self.next())
        self.shuffle_playlist.bind(on_press=lambda _: self.__on_shuffle())
        self.add_song_to.bind(on_press=lambda _: self.__on_added_to_playlist())
        self.song_name.bind(on_size=self.on_size)
        self.player = get_audio_player()
        self.player.on_song_end = lambda _: self.__on_song_end()

    def select_playlist(self, data:dict["name":str, "image": str, "songs": list[str]]) -> None: 
        '''Select the playlist to play. It creates a copy of it in order to shuffle it without side effects and close the previous song.

        Parameters
        ----------
        data : dict[name: str, image: str, songs: list[str]]
            The data for the playlist that is about to be played
        '''
        self.songs = data["songs"].copy()
        self.index = 0
        self.close()
        Clock.schedule_once(lambda _: self.__update_text_field_text(), 0.1)

        if get_data_manager().store["config"]["shuffle"]:
            self.shuffle()

    
    def on_size(self,_, _1):
        '''Callback called when the size of the window change'''
        self.__update_text_field_text()


    def play(self) -> bool:
        '''Play the song at index position stopping if necessary the current song. It loads the ID3 infos. If they are not avaliable try to reproduce the song without image and without title.

        Returns
        -------
        True if the song is correctly loaded, False otherwise
        '''
        data_manager = get_data_manager()
        song = os.path.join(data_manager.base_path, self.songs[self.index])
        try:
            self.player.open_sound(song)
            self.song_name.not_truncated_text = ""
            self.song_field.not_truncated_text = ""
            self.__update_labels(song)
        except TypeError as e:
            # Changing the ui outside its thread(When the player send the end callback on other thread)
            if str(e) == "Cannot create graphics instruction outside the main Kivy thread":
                def update_asyc_ui(_):
                    self.__update_labels(song)
                    self.__update_text_field_text()
                Clock.schedule_once(update_asyc_ui)
                return True
            
            raise e
        except Exception as e:
            show_snackbar(f"Error reading {song} and cannot be played.\nMessage={str(e)}.")
            self.pause_song.icon = "play"
            return False
        self.__update_text_field_text()
        return True


    def next(self) -> None:
        '''Play the next song. If the playlist reached the end it shuffle tha playlist and set index to 0.'''
        if self.index == len(self.songs) - 1:
            self.shuffle()
        self.index = (self.index + 1) % len(self.songs)

        # Sometimes does no load songs
        if not self.play():
            self.next()

    def shuffle(self) -> None:
        '''Shuffle tha playlist without resetting the current song or index'''
        for _ in range(19):
            self.songs = [*self.songs[1::2], *self.songs[0::2]]
            random.shuffle(self.songs, lambda: random.random())
        
    def close(self) -> None:
        '''Close the player. It does not reset index'''
        self.player.close_sound()

    def play_pause(self, state=None) -> None:
        '''Pause or resume the current song. If state is None the state is reversed.

        Arguments
        ---------
        state : bool
            The desired state of the player. True if play, False for pause        
        '''
        if state is None or (state and not self.player.state) or (not state and self.player.state):
            self.player.playpause_sound()
            if self.player.state:
                self.pause_song.icon = "pause"
            else:
                self.pause_song.icon = "play"

    def __update_labels(self, song):
        try:
            self.image.source = get_data_manager().get_image([song])
            id3 = EasyID3(song)
            self.song_name.not_truncated_text = id3["title"][0]
            self.song_field.not_truncated_text = id3["album"][0]
        except Exception as e:
            show_snackbar(f"Error reading {song} infos.\nMessage={str(e)}.")
            self.song_name.not_truncated_text = os.path.basename(song)
            self.song_field.not_truncated_text = ""
        self.pause_song.icon = "pause"

    def __on_shuffle(self):
        self.shuffle()
        self.index = -1
        self.next()
    
    def __on_song_end(self):
        self.next()

    def __on_added_to_playlist(self):
        data_manager = get_data_manager()
        def update_view():
            if data_manager.store["config"]["last_category"] == "playlist":
                MDApp.get_running_app().root.set_category("playlist", force_reload=True)

        AddToPlaylistDialog(self.songs[self.index], self.song_name.not_truncated_text, on_dialog_ended=update_view).show_dialog()

    def __update_text_field_text(self):
            if self.song_name is not None and self.song_field is not None:
                self.song_name.text = truncate_text(self.song_name.not_truncated_text, 2, 15, self.song_name.size[0])
                self.song_field.text = truncate_text(self.song_field.not_truncated_text, 1, 15, self.song_field.size[0])

    
        