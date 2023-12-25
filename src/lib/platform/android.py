import os
from lib.platform.audioplayer import AudioPlayer
from lib.platform.datamanager import DataManager
from kivy.clock import Clock
from typing import Callable
from android.storage import primary_external_storage_path # type: ignore
from android.permissions import request_permissions, Permission, check_permission # type: ignore
from jnius import autoclass, PythonJavaClass, java_method
from kivy.logger import Logger
from android import activity as AndroidActivity

perms = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_PHONE_STATE]

Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Context = autoclass('android.content.Context')
IntentFilter = autoclass('android.content.IntentFilter')
MediaPlayer = autoclass('android.media.MediaPlayer')
PythonActivity = autoclass('org.kivy.android.PythonActivity')


def save_external_file(filename, content):
    currentActivity = PythonActivity.mActivity

    intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("application/json")
    intent.putExtra(Intent.EXTRA_TITLE, filename)
    my_request_code = 42

    def on_activity_result(request_code, result_code, intent):
        if request_code == my_request_code:
            if result_code == -1:
                uri = intent.getData()
                try:
                    parcelFileDescriptor = currentActivity.getContentResolver().openFileDescriptor(uri, "w")
                    fileOutputStream = parcelFileDescriptor.getFileDescriptor()
                    stream = autoclass('java.io.FileOutputStream')(fileOutputStream)
                    stream.write(content.encode('utf-8'))
                    stream.close()
                    parcelFileDescriptor.close()
                except Exception as e:
                    Logger.debug("Error writing file", e)
            else:
                Logger.debug("Error Activity ", result_code)

    AndroidActivity.bind(on_activity_result=on_activity_result)

    PythonActivity.onActivityResult = on_activity_result
    currentActivity.startActivityForResult(intent, my_request_code)

def load_external_file(callback=lambda uri, content: None):
    currentActivity = PythonActivity.mActivity

    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("application/json")
    my_request_code = 43

    # onActivityResult callback
    def on_activity_result(request_code, result_code, intent):
        if request_code == my_request_code:  # Arbitrary request code
            if result_code == -1:  # RESULT_OK
                uri = intent.getData()
                try:
                    parcelFileDescriptor = currentActivity.getContentResolver().openFileDescriptor(uri, "r")
                    fileInputStream = parcelFileDescriptor.getFileDescriptor()

                    # Read your file content here
                    stream = autoclass('java.io.FileInputStream')(fileInputStream)
                    InputStreamReader = autoclass('java.io.InputStreamReader')
                    BufferedReader = autoclass('java.io.BufferedReader')
                    StringBuilder = autoclass('java.lang.StringBuilder')
                    
                    reader = BufferedReader(InputStreamReader(stream))
                    sb = StringBuilder()
                    line = reader.readLine()

                    while line is not None:
                        sb.append(line).append("\n")
                        line = reader.readLine()

                    stream.close()
                    parcelFileDescriptor.close()

                    file_content = sb.toString()
                    callback(uri, file_content)
                except Exception as e:
                    print("Error reading file", e)

    AndroidActivity.bind(on_activity_result=on_activity_result)

    # Start the activity
    PythonActivity.onActivityResult = on_activity_result
    currentActivity.startActivityForResult(intent, my_request_code)  # Arbitrary request code

        


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
    
    # 



class AndroidAudioPlayer(AudioPlayer):
    '''AudioPlayer for Android. Use android.media.MediaPlayer'''

    mplayer = None
    def __init__(self, on_song_end=lambda:None, **kwargs):
        '''Create a new AndroidAudioPlayer
        
        Arguments
        ---------
        on_song_end : () -> None
            Callback called when the song ends
        '''
        super().__init__(on_song_end, **kwargs)

        self.length = 0
        self.state = False



    def close_sound(self):
        '''Stop the sound'''
        if self.mplayer is not None:
            self.state = False
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

    def __on_song_end(self, mp):
        self.state = False
        self.on_song_end(mp)
        
    def __load(self, filename):
        if self.mplayer is None:
            self.mplayer = MediaPlayer()
            self.mplayer.setDataSource(filename)
            self.mplayer.prepare()
            self.length = self.mplayer.getDuration() / 1000