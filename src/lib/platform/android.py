import os
from lib.platform.audioplayer import AudioPlayer
from lib.platform.datamanager import DataManager
from kivy.clock import Clock
from typing import Callable
from android.storage import primary_external_storage_path # type: ignore
from android.permissions import request_permissions, Permission, check_permission # type: ignore
from jnius import autoclass, PythonJavaClass, java_method, cast
from kivy.logger import Logger
from android import activity as AndroidActivity
import threading

from kivy.utils import platform

perms = [Permission.INTERNET, Permission.READ_PHONE_STATE, Permission.READ_MEDIA_AUDIO,  Permission.READ_MEDIA_IMAGES, ]

MediaPlayer = autoclass('android.media.MediaPlayer')
Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Application = autoclass('android.app.Application')
TelephonyManager = autoclass('android.telephony.TelephonyManager')
Consumer = autoclass('java.util.function.Consumer')

MyBroadcastReceiver = autoclass('org.test.naedmusic.MyBroadcastReceiver')


class MyBiFunction(PythonJavaClass):
    __javainterfaces__ = (
        'java.util.function.Consumer', )

    def __init__(self, callback):
        super(MyBiFunction, self).__init__()
        self.callback = callback

    @java_method('(Ljava/lang/Object;)V')
    def accept(self, container):

        self.callback(container.context, container.intent)

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
    def __init__(self, on_song_end=lambda:None, on_state_changed=lambda state:None, **kwargs):
        '''Create a new AndroidAudioPlayer
        
        Arguments
        ---------
        on_song_end : () -> None
            Callback called when the song ends
        '''
        super().__init__(on_song_end, on_state_changed=lambda state:None, **kwargs)

        self.length = 0
        self.state = False
        self.headset_plug_state = -1
        self.stopped_by_call = False
        self.stopped_by_plug = False



    def close_sound(self):
        '''Stop the sound'''
        if self.mplayer is not None:
            self.state = False
            self.mplayer.stop()
            self.mplayer.reset()
            self.mplayer = None
            self.br.Stop()
            self.br = None

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
        
        
        self.br = MyBroadcastReceiver(PythonActivity.mActivity.getApplicationContext(), ['android.intent.action.HEADSET_PLUG', 'android.intent.action.PHONE_STATE'], lambda c,i: self.__on_broadcast(c,i))
        self.br.Start()

    def playpause_sound(self):
        '''Change the status of the reprodution between play and pause'''
        if self.state:
            self.mplayer.pause()
            self.br.Stop()
        else:
            self.mplayer.start()
            self.br.Start()
        self.state = not self.state

    
    def __on_broadcast(self, context, intent):
        Logger.info(f"Action: {intent.getAction()}")

        if intent.getAction() == 'android.intent.action.HEADSET_PLUG':
            self.__on_headset_plug(context, intent)
        elif intent.getAction() == 'android.intent.action.PHONE_STATE':
            self.__on_phone_state(context, intent)

    def __on_phone_state(self, context, intent):
        state = intent.getStringExtra(TelephonyManager.EXTRA_STATE)
        Logger.info(f"phone state changed: {state}")

        if state == TelephonyManager.EXTRA_STATE_IDLE and self.stopped_by_call:
            self.mplayer.start()
            self.stopped_by_call = False
            self.on_state_changed(True)
            Logger.info(f"Sound reasumed after call")
        if (state == TelephonyManager.EXTRA_STATE_RINGING or state == TelephonyManager.CALL_STATE_OFFHOOK) and self.state:
            self.mplayer.pause()
            self.stopped_by_call = True
            self.on_state_changed(False)
            Logger.info(f"Sound stopped by call")


    def __on_headset_plug(self, context, intent):
        state = int(intent.getIntExtra("state", -1))
        
        if self.headset_plug_state == 1 and state == 0:
            self.mplayer.pause()
            self.stopped_by_plug = True
            Logger.info('Headset plug removed. Song paused')

        if self.headset_plug_state == 0 and state == 1 and self.stopped_by_plug:
            self.mplayer.start()
            self.stopped_by_plug = False
            Logger.info('Headset plug removed. Song paused')
        self.headset_plug_state = state
            

        Logger.info(f"State - {state}, previous state: {self.headset_plug_state}")

    def __on_song_end(self, mp):
        Logger.info("__on_song_end  ")
        self.state = False
        self.on_song_end(mp)
        
    def __load(self, filename):
        if self.mplayer is None:
            self.mplayer = MediaPlayer()
            self.mplayer.setDataSource(filename)
            self.mplayer.prepare()
            self.length = self.mplayer.getDuration() / 1000