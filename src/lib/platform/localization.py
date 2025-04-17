from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from mutagen.easyid3 import EasyID3
from plyer import filechooser
from kivy.logger import Logger

import locale

import random
from typing import Any
import os
import re
from pathlib import Path
import json



implemented_platoforms = ["Windows", "Android", "Linux"]
'''Implemented platorms'''

__localization = None


def reload_localization(callback=lambda:None):
    global __localization
    __localization = None
    return get_localization(callback)

def get_localization(callback=lambda dm:None):
    '''Get the localization dictionary. The first time ever the program is runned on a system may require time to calculate
    
    Arguments
    ---------
    callback : (bool) -> None
        Callback used only when the system require additional time to retrive the localization(eg. asking permission). In this case the return value is None. Called always in the kivy thread. Pass the result of asking the permissions
    
    Raises
    ----------
    Exception
        if the platform is not recognized or implemented

    Returns
    -------
    localization : dict
        If the localization is ready to use returns it. Otherwise return None and call callback when ready.
    '''

    # callback return in kivy thread
    global __localization
    if __localization is None:
        if platform == "win":
            from lib.platform.windows.localization import WindowsLocalization
            __localization = WindowsLocalization()
        elif platform == "android":
            from lib.platform.android.localization import AndroidLocalization
            __localization = AndroidLocalization()
        elif platform == "linux":
            from lib.platform.linux.localization import LinuxLocalization
            __localization = LinuxLocalization()
        else:
            raise Exception(f"Platoform not recognized({platform}). Implemented platforms: {implemented_platoforms}")
    return __localization.get_localization()

class Localization():
    '''Class that store and read the data in a JSON file
    
    Attributes
    ----------
    base_path : str
        The default path for all songs. Used to save a bit the space of the json file
    store : JsonStore
        Kivy object that save and read the data. Use only to read values, NOT to write.

    Methods
    -------
    put_data(path: str, value: Any) -> None
        Save the data in the file following a path. eg. store["field1"]["field2"]["field3"] = value <=> put_fata(["field1", "field2", "field3"], value)
    get_image(songs: list[str])  -> str
        Search an image in a list of songs. Search for an image in the same folder of the songs.
    '''

    file_path: str = None

    def __init__(
        self,
        file_path=os.path.expanduser("~/localization.json")
        ):
        '''Create new DataManager
        
        Arguments
        ---------
        base_path : str
            Base path for all the songs
        data_file_name : str
            Path to the file to use as memory
        '''
        self.file_path = file_path
        with open(self.file_path, 'r') as f:
            self.localization = json.load(f)

        user_language = self.estimate_locale().replace("-", "_")
        self.active_localization = self.get_localization_for_language(user_language)

    def estimate_locale(self):
        return locale.getlocale()[0]

    def get_localization_for_language(self, language, with_default=True):
        for l in self.localization:
            if language in l["names"]:
                return l["value"]
        if with_default:
            return self.get_localization_for_language("en_EN", False)
        return None
    
    def get_localization(self):
        return self.active_localization
