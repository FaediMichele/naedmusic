import os
from lib.platform.datamanager import DataManager
from lib.platform.android.util import save_external_file, load_external_file
from kivy.clock import Clock
from typing import Callable
from android.runnable import run_on_ui_thread # type:ignore
from android.storage import primary_external_storage_path # type: ignore
from android.permissions import request_permissions, Permission, check_permission # type: ignore
from kivy.logger import Logger
from jnius import autoclass





perms = [
        Permission.INTERNET,
        Permission.READ_PHONE_STATE,
        Permission.READ_MEDIA_AUDIO,
        Permission.READ_MEDIA_IMAGES,
        Permission.POST_NOTIFICATIONS,
        'android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK'
    ]

class AndroidDataManager(DataManager):
    '''DataManager for Android. Should use check_permissions and ask_permissions before actually creating an instance'''

    def __init__(self, data_file_name="playlist.json"):
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

        Clock.schedule_once(lambda _: request_permissions(
            perms,
            lambda _, results: Clock.schedule_once(
                lambda _: callback(AndroidDataManager.check_permissions())
            )
        ))

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
                Logger.error(f'Permission {p} not granted')
                return False
        return True