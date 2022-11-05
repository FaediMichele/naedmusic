import os
from lib.platform.audioplayer import AudioPlayer
from lib.platform.datamanager import DataManager
from kivy.clock import Clock
from typing import Callable
from android.storage import primary_external_storage_path
from android.permissions import request_permissions, Permission, check_permission
from jnius import autoclass, PythonJavaClass, java_method

perms = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]

class AndroidDataManager(DataManager):
    '''DataManager for Android. Should use check_permissions and ask_permissions before actually creating an instance'''
    def __init__(self, data_file_name="playlist.json", ):
        '''Create a new LinuxDataManager

        Arguments
        ---------
        data_file_name : str
            path to the configuration file. Default "~/playlist.json"
        '''
        super().__init__(os.path.join(primary_external_storage_path(), "Music"), data_file_name)

    @staticmethod
    def ask_permissions(callback: Callable[[], bool]):
        '''Ask to the user the permission to read and write the memory file
        
        Arguments
        ---------
        callback : (bool) -> None
            Called when the permission is granted. Pass the result of asking the permissions
        '''
        global perms
        Clock.schedule_once(lambda _: request_permissions(perms, lambda _, results: callback(False not in results)))

    @staticmethod
    def check_permissions() -> bool:
        '''Check if the application have the required permissions
        
        Returns
        -------
        True if all the permission are granted. False otherwise
        '''
        global perms
        for p in perms:
            if not check_permission(p):
                return False
        return True


class AndroidAudioPlayer(AudioPlayer):
    '''AudioPlayer for Android. Use android.media.MediaPlayer'''

    def __init__(self, on_song_end=lambda:None, **kwargs):
        '''Create a new AndroidAudioPlayer
        
        Arguments
        ---------
        on_song_end : () -> None
            Callback called when the song ends
        '''
        super().__init__(on_song_end, **kwargs)
        self.MediaPlayer = autoclass('android.media.MediaPlayer')
        self.mplayer = self.MediaPlayer()
        self.length = 0
        self.state = False

    

    def close_sound(self):
        '''Stop the sound'''
        if self.mplayer is not None:
            self.state = False
            # self.mplayer.setOnCompletionListener(self.__on_song_end)
            self.mplayer.stop()
            self.mplayer.reset()
            self.mplayer = None

    def open_sound(self, path:str):
        '''Load the song and start to play it
        
        Arguments
        ---------
        path : str
            path to the song
        '''
        self.close_sound()
        self.__load(path)
        self.mplayer.start()
        self.state = True

        class AudioCompletionCallback(PythonJavaClass):
            # http://developer.android.com/reference/android/media/MediaPlayer.OnCompletionListener.html
            __javainterfaces__ = (
                'android.media.MediaPlayer$OnCompletionListener', )

            def __init__(self, callback):
                super(AudioCompletionCallback, self).__init__()
                self.callback = callback

            @ java_method('(Landroid/media/MediaPlayer;)V')
            def onCompletion(self, mp):
                self.callback(mp)

        self._complete_callback = AudioCompletionCallback(self.__on_song_end)
        self.mplayer.setOnCompletionListener(self._complete_callback)

    def playpause_sound(self):
        '''Change the status of the reprodution between play and pause'''
        if self.state:
            self.mplayer.pause()
        else:
            self.mplayer.start()
        self.state = not self.state

    def __on_song_end(self, _):
        self.state = False
        self.dispatch("on_song_end", self)

    def __load(self, filename):
        if self.mplayer is None:
            self.mplayer = self.MediaPlayer()
            self.mplayer.setDataSource(filename)
            self.mplayer.prepare()
            self.length = self.mplayer.getDuration() / 1000