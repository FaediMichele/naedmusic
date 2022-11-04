import random
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar
from lib.platform.audioplayer import get_audio_player
from lib.platform.datamanager import get_data_manager
from lib.ui.add_to_playlist_dialog import AddToPlaylistDialog
from kivymd.app import MDApp
from mutagen.easyid3 import EasyID3
import os
from datetime import date

random.seed(date.today().month*100 + date.today().day)

class PlaylistBar(MDBoxLayout):
    song_name = ObjectProperty(None)
    song_field = ObjectProperty(None)
    image = ObjectProperty(None)
    next_song = ObjectProperty(None)
    pause_song = ObjectProperty(None)
    shuffle_playlist = ObjectProperty(None)
    add_song_to = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pause_song.bind(on_press=lambda _: self.pause())
        self.next_song.bind(on_press=lambda _: self.next())
        self.shuffle_playlist.bind(on_press=lambda _: self.on_shuffle())
        self.add_song_to.bind(on_press=lambda _: self.on_added_to_playlist())
        self.seektime = 0
        self.player = get_audio_player()
        self.player.on_song_end = self.on_song_end

    def select_playlist(self, data):
        self.songs = data["songs"].copy()
        self.index = 0
        self.player.close_sound()

        if get_data_manager().store["config"]["shuffle"]:
            self.shuffle()


    def play(self):
        data_manager = get_data_manager()
        song = os.path.join(data_manager.base_path, self.songs[self.index])
        try:
            self.player.open_sound(song)
            try:
                id3 = EasyID3(song)
                self.song_name.text = id3["title"][0]
                self.song_field.text = id3["album"][0]
                self.image.source = get_data_manager().get_image([song])
                return True
            except Exception as e:
                Snackbar(text=f"Error reading {song} infos.\nMessage={str(e)}.").open()
                self.song_name.text = os.path.basename(song)
                self.song_field.text = ""
                self.image.source.text = ""
                return True
        except Exception as e:
            Snackbar(text=f"Error reading {song} and cannot be played.\nMessage={str(e)}.").open()
            return False


    def next(self):
        if self.index == len(self.songs) - 1:
            self.shuffle()
        self.index = (self.index + 1) % len(self.songs)

        # Sometimes does no load songs
        if not self.play():
            self.next()

    def shuffle(self):
        for _ in range(19):
            self.songs = [*self.songs[1::2], *self.songs[0::2]]
            random.shuffle(self.songs, lambda: random.random())

    def on_shuffle(self):
        self.shuffle()
        self.index = -1
        self.next()

    def close(self):
        self.player.close_sound()
    
    def on_song_end(self):
        self.next()

    def on_added_to_playlist(self):
        data_manager = get_data_manager()
        def update_view():
            if data_manager.store["config"]["last_category"] == "playlist":
                MDApp.get_running_app().root.set_category("playlist", force_reload=True)

        AddToPlaylistDialog(self.songs[self.index], self.song_name.text, on_dialog_ended=update_view).show_dialog()

    def pause(self):
        self.player.playpause_sound()
        if self.player.state:
            self.pause_song.icon = "pause"
        else:
            self.pause_song.icon = "play"
        