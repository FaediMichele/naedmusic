import os
from lib.platform.audioplayer import AudioPlayer
from lib.platform.android.util import mplayer_controller_container
from lib.platform.datamanager import get_data_manager
from android.runnable import run_on_ui_thread # type:ignore
from jnius import autoclass # type:ignore
from kivy.logger import Logger


Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
TelephonyManager = autoclass('android.telephony.TelephonyManager')
Player = autoclass('androidx.media3.common.Player')

MyBroadcastReceiver = autoclass('org.test.naedmusic.MyBroadcastReceiver')
MyListener = autoclass('org.test.naedmusic.MyListener')


class AndroidAudioPlayer(AudioPlayer):
    '''AudioPlayer for Android. Use android.media.MediaPlayer'''

    mplayer_controller = None
    
    mplayer_service = None
    def __init__(self, on_song_end=lambda:None, on_state_changed=lambda state:None, **kwargs):
        '''Create a new AndroidAudioPlayer
        
        Arguments
        ---------
        on_song_end : () -> None
            Callback called when the song ends
        '''
        super().__init__(on_song_end, on_state_changed=on_state_changed, **kwargs)

        self.length = 0
        self.state = False
        self.headset_plug_state = -1
        self.stopped_by_call = False
        self.stopped_by_plug = False
        self.mplayer_controller = mplayer_controller_container.getController()
        self._complete_callback = MyListener(lambda event, state: self.__on_song_end(event, state))
        
        self.br = None
        if self.mplayer_controller is None:
            raise Exception('controller still none')
        
    @run_on_ui_thread
    def close_sound(self):
        '''Stop the sound'''
        if self.mplayer_controller is not None:
            self.state = False
            self.mplayer_controller.stop()
            self.mplayer_controller.removeListener(self._complete_callback)
            # self.mplayer_controller.reset()
            # self.mplayer_controller.release()
            # self.mplayer_controller = None

        if self.br is not None:
            self.br.Stop()
            self.br = None

    @run_on_ui_thread
    def open_sound(self, path:str, song: dict):
        '''Load the song and start to play it
        
        Arguments
        ---------
        path : str
            path to the song
        '''
        self.close_sound()
        self.mplayer_controller.addListener(self._complete_callback)
        
        self.br = MyBroadcastReceiver(PythonActivity.mActivity.getApplicationContext(), ['android.intent.action.HEADSET_PLUG', 'android.intent.action.PHONE_STATE'], lambda c,i: self.__on_broadcast(c,i))
        self.br.Start()

        self.__load(path, song)
        self.mplayer_controller.play()
        self.state = True

    @run_on_ui_thread
    def playpause_sound(self):
        '''Change the status of the reprodution between play and pause'''
        if self.state:
            self.mplayer_controller.pause()
            self.br.Stop()
        else:
            self.mplayer_controller.play()
            self.br.Start()
        self.state = not self.state

    @run_on_ui_thread
    def __on_external_action(self, action, data):
        # ignored in playlist
        if action == 'play' and not self.state:
            self.mplayer_controller.play()
            self.on_state_changed(True)
        if action == 'pause' and self.state:
            self.mplayer_controller.pause()
            self.on_state_changed(False)
        if action == 'stop':
            self.close_sound()
        if action == 'next':
            self.state = False
            self.on_song_end(3)
        if action == 'seek':
            self.mplayer_controller.seekTo(data, 0)

    
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

        if state == TelephonyManager.EXTRA_STATE_IDLE and self.stopped_by_call:
            self.mplayer_controller.start()
            self.stopped_by_call = False
            self.on_state_changed(True)
            Logger.info(f"Sound reasumed after call")
        if (state == TelephonyManager.EXTRA_STATE_RINGING or state == TelephonyManager.CALL_STATE_OFFHOOK) and self.state:
            self.mplayer_controller.pause()
            self.stopped_by_call = True
            self.on_state_changed(False)
            Logger.info(f"Sound stopped by call")
        
        self.mplayer_helper.showNotification(self.state)


    @run_on_ui_thread
    def __on_headset_plug(self, context, intent):
        state = int(intent.getIntExtra("state", -1))
        
        if self.headset_plug_state == 1 and state == 0:
            self.mplayer_controller.pause()
            self.stopped_by_plug = True 
            Logger.info('Headset plug removed. Song paused')

        if self.headset_plug_state == 0 and state == 1 and self.stopped_by_plug:
            self.mplayer_controller.start()
            self.stopped_by_plug = False
            Logger.info('Headset plug removed. Song paused')
        self.headset_plug_state = state
            

        Logger.info(f"State - {state}, previous state: {self.headset_plug_state}")

    def __on_song_end(self, event, state):
        Logger.info(f"__on_song_end {state}")
        if event == 'onPlaybackStateChanged' and state == 4:
            self.state = False
            self.on_song_end(self.state)


    @run_on_ui_thread   
    def __load(self, filename, song):
        data_manager = get_data_manager()
        image_path = data_manager.get_image([os.path.join(data_manager.base_path, song["file"])])
        self.mplayer_controller.setMediaItem(mplayer_controller_container.createMediaItem(
            filename, song['artist'], song['title'], song['album'], song['track'], song['id'], image_path))
        self.mplayer_controller.prepare()
        self.length = self.mplayer_controller.getDuration() / 1000