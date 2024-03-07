from abc import ABC, abstractmethod
from kivy.event import EventDispatcher
from kivy.utils import platform as operative_system

implemented_platoforms = ["Windows", "Android", "Linux"]

class AudioPlayer(ABC):
    '''AudioPlayer abstract class

    Attributes
    ----------
    state : bool
        True if playing a sound, False otherwise
    
    Methods
    -------
    close_sound() -> None
        Release the resources for the file
    open_sound() -> None
        Load the sound and start to play it
    playpayse_sound() -> None
        Change the status of the reprodution between play and pause
    '''
    on_song_end = None
    state = False

    def __init__(self, on_song_end=lambda x: None, on_state_changed=lambda state:None, **kwargs):
        super(AudioPlayer, self).__init__()
        self.on_song_end = on_song_end
        self.on_state_changed = on_state_changed
        self.kwargs = kwargs

    @abstractmethod
    def close_sound(self):
        pass

    @abstractmethod
    def open_sound(self, path: str, song: dict):
        pass

    @abstractmethod
    def playpause_sound(self):
        pass

def get_audio_player() -> AudioPlayer:
    '''Get the AudioPlayer based on the platform the program is running on. Use lazy approach
    
    Raises
    ----------
    Exception
        if the platform is not recognized or implemented

    Returns
    -------
    audio_player : AudioPlayer
        instance of AudioPlayer for the current platform
    '''
    if operative_system == "win":
        from lib.platform.windows.audio_player import WindowsAudioPlayer
        return WindowsAudioPlayer()
    elif operative_system == "android":
        from lib.platform.android.audio_player import AndroidAudioPlayer
        return AndroidAudioPlayer()
    elif operative_system == "linux":
        from lib.platform.linux.audio_player import LinuxAudioPlayer
        return LinuxAudioPlayer()
    else:
        raise Exception(f"Platoform not recognized({operative_system}). Implemented platforms: {implemented_platoforms}")