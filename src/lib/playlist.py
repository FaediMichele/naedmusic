import random
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar
from lib.platform.audioplayer import get_audio_player, AudioPlayer
from lib.platform.datamanager import get_data_manager
from lib.ui.add_to_playlist_dialog import AddToPlaylistDialog
from lib.localization import localization
import os
from datetime import date
from lib.util import show_snackbar, truncate_text
from kivy.clock import Clock
from typing import Callable

random.seed(date.today().month*100 + date.today().day)

class Playlist():
    '''Class that manage a playlist. Allow to load and play a list of songs. Is possible to manually insert single songs that will be played only once
    
    Attributes
    ----------
    index : int
        Index of the song in the list that is currently running(not used if the played song is manually inserted)
    player : AudioPlayer
        Player of the song
    songs : list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]
        List of songs in the queue
    added_songs : list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]
        Manually added song to the playlist. The manually added songs to the playlist are not stored after being reproduced'
    '''

    index = 0
    '''Index of the current song in the playlist'''

    player: AudioPlayer = None
    '''Player for the songs'''

    songs: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]] = []
    '''List of songs in the queue'''

    added_songs: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]] = []
    '''Manually added song to the playlist. The manually added songs to the playlist are not stored after being reproduced'''

    next_song = None
    '''Next song to play. Can be a song of the songs list or of the added_song list'''

    def __init__(self, songs: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]], on_song_changed: Callable[[],None]):
        super().__init__()
        self.player = get_audio_player()
        self.player.on_song_end = lambda _: self.next()
        self.playlist = songs
        self.__play()
        self.on_song_changed = on_song_changed


    def __play(self) -> bool:
        '''Play the song at index position stopping if necessary the current song

        Returns
        -------
        (bool, str) Return a tuple. The first value is True if the song is correctly loaded, False otherwise. The second value is the error message in case the loading failed
        '''
        data_manager = get_data_manager()
        if self.next_song is not None:
            self.current_song = self.next_song
            self.next_song = None
        else:
            self.current_song = self.playlist[self.index]
        try:
            self.player.open_sound(os.path.join(data_manager.base_path, self.current_song["file"]))
            Clock.schedule_once(lambda _:self.on_song_changed())
            return True, ""
        except Exception as e:
            return False, str(e)
        
    def add_song_to_playlist(self, song: dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]):
        '''Add a song to the playlist
        
        Arguments
        ---------
        song : int
            The id of the song
        '''
        self.added_songs.append(song)

    def next(self) -> None:
        '''Play the next song. If the playlist reached the end it shuffle tha playlist and set index to 0.'''
        if len(self.added_songs) > 0:
            self.next_song = self.added_songs[0]
            self.added_songs = self.added_songs[1:]
            ok, err = self.__play()
            if not ok:
                show_snackbar(localization["errors"]["opening_sound"].format(self.current_song["title"], err))
                self.next()
        else:
            
            if self.index == len(self.playlist) - 1:
                self.shuffle()
            self.index = (self.index + 1) % len(self.playlist)
            ok, err = self.__play()
            # Sometimes does no load songs
            if not ok:
                show_snackbar(localization["errors"]["opening_sound"].format(self.current_song["title"], err))
                self.next()
    
    def start(self):
        '''Start the playlist'''
        self.index = -1
        self.next()

    def shuffle(self) -> None:
        '''Shuffle tha playlist without resetting the current song or index'''
        for _ in range(19):
            self.playlist = [*self.playlist[1::2], *self.playlist[0::2]]
            random.shuffle(self.playlist, lambda: random.random())
        
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