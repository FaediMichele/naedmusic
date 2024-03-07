import os
import random
from typing import Callable

from lib.platform.android.util import mplayer_controller_container
from lib.platform.android.audio_player import AndroidAudioPlayer
from lib.platform.playlist_manager import Playlist
from lib.platform.datamanager import get_data_manager

from lib.localization import localization
from kivy.logger import Logger
from kivy.clock import Clock
from lib.util import show_snackbar


from android.runnable import run_on_ui_thread # type:ignore
from jnius import autoclass # type:ignore

Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
TelephonyManager = autoclass('android.telephony.TelephonyManager')
Player = autoclass('androidx.media3.common.Player')
MyBroadcastReceiver = autoclass('org.test.naedmusic.MyBroadcastReceiver')
MyListener = autoclass('org.test.naedmusic.MyListener')


class SongLoader:
    def __init__(self, songs, add_song_func, interval=0.2) -> None:
        self.songs = songs
        self.add_song_func = add_song_func
        self.interval = interval
        self.state = False
    
    def start(self):
        self.state = True
        def add_song(_):
            if len(self.songs) > 0 and self.state:
                song = self.songs[0]
                self.songs = self.songs[1:]
                self.add_song_func(song)
                Clock.schedule_once(add_song, self.interval)
        Clock.schedule_once(add_song, self.interval)

    def stop(self):
        self.state = False


class AndroidPlaylist(Playlist):
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

    songs: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]] = []
    '''List of songs in the queue'''

    playlist = []


    @run_on_ui_thread
    def __init__(self):
        self.br = MyBroadcastReceiver(PythonActivity.mActivity.getApplicationContext(),
                                      ['android.intent.action.HEADSET_PLUG', 'android.intent.action.PHONE_STATE'],
                                      lambda c,i: self.__on_broadcast(c,i))
        
        self.player = mplayer_controller_container.getController()
        self._complete_callback = MyListener(lambda event, state: self._on_event(event, state))
        self.player.addListener(self._complete_callback)
        self.song_loader = None
        self.songs_loaded = []

    @run_on_ui_thread
    def new_playlist(self,
                     songs: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]],
                     on_song_changed: Callable[[],None],
                     on_state_changed: Callable[[bool],None],
                     songs_to_load: int = 5):
        self.songs_to_load = songs_to_load
        self.on_state_changed = on_state_changed 
        self.on_song_changed = on_song_changed

        self.headset_plug_state = -1
        self.stopped_by_call = False
        self.stopped_by_plug = False
        
        if self.player is None:
            self.player = mplayer_controller_container.getController()
        if self.player is None:
            raise Exception('controller still none')
        
        self.br.Start()
        
        self.player.setPlayWhenReady(False)
        self.playlist = songs
        self.shuffle()
        
        
    def load_songs(self, songs):
        self.player.clearMediaItems()

        self.add_song_to_playlist(songs[0], prepare=True)

        if self.song_loader is not None:
            self.song_loader.stop()
            self.songs_loaded = [songs[0]]
        self.song_loader = SongLoader(songs[1:], self.add_song_to_playlist, 0.2)
        self.song_loader.start()


    def start(self):
        '''Start the playlist'''
        self.play_pause(True)
        


    def _on_event(self, event, state):
        self.get_current_song(lambda song: self.on_song_changed(song))        
        if event == 'onPlaybackStateChanged':
            pass

        if event == 'onIsPlayingChanged':
            self.on_state_changed(state)
    
    @run_on_ui_thread
    def get_current_song(self, callback):
        mediaitem = self.player.getCurrentMediaItem()
        if mediaitem is None:
            Logger.error(f'Get current song is None')
            id = 0
        else:
            id = int(mediaitem.mediaId)
        data_manager = get_data_manager()
        song = data_manager.store['data']['songs'][id]
        assert song['id'] == id

        Clock.schedule_once(lambda _: callback(song))


    def __on_broadcast(self, context, intent):
        Logger.info(f"Action: {intent.getAction()}")

        if intent.getAction() == 'android.intent.action.HEADSET_PLUG':
            self.__on_headset_plug(context, intent)
        elif intent.getAction() == 'android.intent.action.PHONE_STATE':
            self.__on_phone_state(context, intent)

    @run_on_ui_thread
    def __on_phone_state(self, context, intent):
        state = intent.getStringExtra(TelephonyManager.EXTRA_STATE)
        Logger.info(f"phone state changed: {state}")

        if (state == TelephonyManager.EXTRA_STATE_RINGING or state == TelephonyManager.CALL_STATE_OFFHOOK) and self.player.isPlaying():
            self.play_pause(False)
            self.stopped_by_call = True
            self.on_state_changed(False)
            Logger.info(f"Sound stopped by call")

        if state == TelephonyManager.EXTRA_STATE_IDLE and self.stopped_by_call:
            self.play_pause(True)
            self.stopped_by_call = False
            self.on_state_changed(True)
            Logger.info(f"Sound reasumed after call")


    @run_on_ui_thread
    def __on_headset_plug(self, context, intent):
        state = int(intent.getIntExtra("state", -1))
        
        if self.headset_plug_state == 1 and state == 0:
            self.play_pause(False)
            self.stopped_by_plug = True 

        if self.headset_plug_state == 0 and state == 1 and self.stopped_by_plug:
            self.play_pause(True)
            self.stopped_by_plug = False
        self.headset_plug_state = state
        
    @run_on_ui_thread
    def add_song_to_playlist(self, song: dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int], prepare=False):
        '''Add a song to the playlist
        
        Arguments
        ---------
        song : dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]
            The data of the song
        '''
        if song not in self.songs_loaded:
            data_manager = get_data_manager()
            image_path = data_manager.get_image([os.path.join(data_manager.base_path, song["file"])])
            mediaItem = mplayer_controller_container.createMediaItem(
                song['file'], song['artist'], song['title'], song['album'], song['track'], song['id'], image_path)
            self.player.addMediaItem(mediaItem)
            self.songs_loaded.append(song)
            if prepare:
                self.player.prepare()

    @run_on_ui_thread
    def next(self) -> None:
        '''Play the next song. If the playlist reached the end it shuffle tha playlist and set index to 0.'''
        if self.player.getCurrentMediaItemIndex() == self.player.getMediaItemCount() - 1:
            self.shuffle()
        self.player.seekToNext()
        self.play_pause(True)

    @run_on_ui_thread
    def get_state(self, callback):
        callback(self.player.isPlaying())

    @run_on_ui_thread
    def shuffle(self) -> None:
        '''Shuffle tha playlist without resetting the current song or index'''
        for _ in range(19):
            self.playlist = [*self.playlist[1::2], *self.playlist[0::2]]
            random.shuffle(self.playlist, lambda: random.random())
        
        self.load_songs(self.playlist)

    @run_on_ui_thread 
    def close(self) -> None:
        '''Close the player. It does not reset index'''
        self.br.Stop()
        self.player.stop()
        self.stopped_by_call = False

    @run_on_ui_thread
    def play_pause(self, state=None) -> None:
        '''Pause or resume the current song. If state is None the state is reversed.

        Arguments
        ---------
        state : bool
            The desired state of the player. True if play, False for pause        
        '''
        
        if state is None and self.player.isPlaying():
            self.player.pause()
            self.stopped_by_call = False
        elif state is None and not self.player.isPlaying():
            self.player.prepare()
            self.player.play()
        elif state and not self.player.isPlaying():
            self.player.prepare()
            self.player.play()
        elif not state and self.player.isPlaying():
            self.player.pause()
            self.stopped_by_call = False

