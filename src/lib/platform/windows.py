import os
from kivy.core.audio import SoundLoader
from lib.platform.audioplayer import AudioPlayer
from lib.platform.datamanager import DataManager
from kivy.clock import Clock
from functools import partial

class WindowsDataManager(DataManager):
    '''DataManager for Windows OS'''
    def __init__(self, data_file_name=os.path.expanduser("~/playlist.json")):
        '''Create a new WindowsDataManager

        Arguments
        ---------
        data_file_name : str
            path to the configuration file. Default "~/playlist.json"
        '''
        super().__init__(os.path.join(os.path.expanduser("~"), "Music"), data_file_name)


class WindowsAudioPlayer(AudioPlayer):
    '''AudioPlayer for Windows OS. Wrapper of kivy.core.audio.SoundLoader'''
    
    def __init__(self, on_song_end=lambda:None, **kwargs):
        '''Create new WindowsAudioPlayer
        
        Arguments
        ---------
        on_song_end : () -> None
            Callback called when the song ends
        '''
        super().__init__(on_song_end, **kwargs)
        self.sound = None
        self.state = False

    def close_sound(self):
        '''Stop the sound'''
        if self.sound is not None:
            self.sound.unbind(on_stop=self.on_song_end)
            self.sound.stop()
            # self.sound.unload()
            self.sound = None
        self.state = False

    def open_sound(self, path: str):
        '''Load the song and start to play it
        
        Arguments
        ---------
        path : str
            path to the song
        '''
        self.close_sound()
        self.sound = SoundLoader.load(path)
        self.sound.play()
        self.sound.bind(on_stop=self.on_song_end)
        self.state = True

    def playpause_sound(self):
        '''Change the status of the reprodution between play and pause'''
        if self.state:
            self.seektime = self.sound.get_pos()
            self.sound.unbind(on_stop=self.on_song_end)
            self.sound.stop()
        else:
            self.sound.play()
            Clock.schedule_once(lambda _: self.sound.seek(self.seektime), 0.1)
            self.sound.bind(on_stop=self.on_song_end)
        self.state = not self.state


    def on_song_end(self):
        '''Callback called when the song ends. It trigger the on_song_end events'''
        self.close_sound()
        self.on_song_end()
