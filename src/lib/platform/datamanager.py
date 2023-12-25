from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from lib.localization import localization
from mutagen.easyid3 import EasyID3
from typing import Any
import os
import re
import logging


implemented_platoforms = ["Windows", "Android", "Linux"]
'''Implemented platorms'''

__data_manager = None


def reload_data_manager(callback=lambda:None):
    global __data_manager
    __data_manager = None
    return get_data_manager(callback)

def get_data_manager(callback=lambda dm:None):
    '''Get the data manager. The first time ever the program is runned on a system may require time to calculate
    
    Arguments
    ---------
    callback : (bool) -> None
        Callback used only when the system require additional time to retrive the data manager(eg. asking permission). In this case the return value is None. Called always in the kivy thread. Pass the result of asking the permissions
    
    Raises
    ----------
    Exception
        if the platform is not recognized or implemented

    Returns
    -------
    data_manager : DataManager|None
        If the data manager is ready to use returns it. Otherwise return None and call callback when ready.
    '''

    # callback return in kivy thread
    global __data_manager
    if __data_manager is None:
        if platform == "win":
            import lib.platform.windows as windows
            __data_manager = windows.WindowsDataManager()
        elif platform == "android":
            def my_callback(status):
                if status:
                    global __data_manager
                    __data_manager = android.AndroidDataManager()
                callback(status)
            import lib.platform.android as android
            if not android.AndroidDataManager.check_permissions():
                android.AndroidDataManager.ask_permissions(my_callback)
                return None
            __data_manager = android.AndroidDataManager()
        elif platform == "linux":
            import lib.platform.linux as linux
            __data_manager = linux.LinuxDataManager()
        else:
            raise Exception(f"Platoform not recognized({platform}). Implemented platforms: {implemented_platoforms}")
    return __data_manager

class DataManager():
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

    base_path: str = None
    store: JsonStore = None

    def __init__(self, base_path=os.path.expanduser("~/Music"), data_file_name=os.path.expanduser("~/playlist.json")):
        '''Create new DataManager
        
        Arguments
        ---------
        base_path : str
            Base path for all the songs
        data_file_name : str
            Path to the file to use as memory
        '''
        self.base_path = base_path
        self.store = JsonStore(data_file_name)

        if not self.store.exists("data"):
            new_data = self.__build_json(self.base_path)
            self.store.put("data", **new_data)
            self.store.put("config", **{"base_path": base_path, "shuffle": True, "last_category": "artist"})
            logging.info(f"Data Saved in {data_file_name}")
    
    def put_data(self, path:list[str], value: Any):
        '''Save the data in the file following a path. eg. store["field1"]["field2"]["field3"] = value <=> put_fata(["field1", "field2", "field3"], value)
        
        Arguments
        ---------
        path : list[str]
            Fields names for sub dictionary to navigate
        value : Any
            Value to save
        '''
        self.store[path[0]] = self.__put_data_rec(self.store[path[0]], path[1:], value)
        logging.info(f"Data updated: {path}")

    def get_image(self, songs: list[str]) -> str:
        '''Search an image in a list of songs. Search for an image in the same folder of the songs.
        
        Arguments
        ---------
        songs : list[str]
            List of songs where search the image

        Returns
        -------
        image_path : str
            Path to an image. If not image is found return ""
        '''
        folders = set([os.path.dirname(s) for s in songs])
        for dirname in folders:
            regex = re.compile("\.(jpg|png)$")
            for path, _, files in os.walk(os.path.join(self.base_path, dirname)):
                for file in files:
                    if regex.search(file):
                        return os.path.join(path, file)
        return "data/gelbe_Note.png"

    def check_and_run_update(self):
        '''Check if there are new songs in the music folder or if some songs are removed. It update the storage file'''
        all_songs = set(self.__traverse_folder(self.base_path, re.compile("\.(wav|mp3|flac)$")))
        old_songs = set([s["file"] for s in self.store["data"]["songs"]])
        removed_songs = old_songs - all_songs
        new_songs = all_songs - old_songs

        logging.info(f"Removed songs {removed_songs}")
        logging.info(f"Added songs {new_songs}")

        changes = False

        if len(removed_songs) > 0:
            self.__remove_songs(removed_songs)
            changes = True

        if len(new_songs) > 0:
            self.__add_songs(new_songs)
            changes = True
        return changes

    def __remove_songs(self, files):
        for file in files:
            for song in self.store["data"]["songs"].copy():
                if song["file"] == file:
                    del self.store["data"]["songs"][song["id"]]
                    for s in self.store["data"]["songs"][song["id"]:]:
                        s["id"] -=1
                    for cateogry in ["artist", "album", "playlist"]:
                        i = 0
                        while i < len(self.store["data"][cateogry]):
                            el = self.store["data"][cateogry][i]
                            el["songs"] = [index if index < song["id"] else index-1 for index in el["songs"] if index != song["id"]]
                            if len(el["songs"]) == 0:
                                del self.store["data"][cateogry][i]
                            i+=1
                    logging.info(f"Removed {song['title']}")
                    break
        self.store["data"] = self.store["data"]

    def __add_songs(self, files):
        songs = self.__create__list(files, self.base_path)
        previous_last_id = max([s["id"] for s in self.store["data"]["songs"]])
        for s in songs:
            s["id"] += previous_last_id + 1

        for s in songs:
            self.store["data"]["songs"].append(s)
            for cateogry in ["artist", "album"]:
                ok = True
                
                for el in self.store["data"][cateogry]:
                    if el["name"] == s[cateogry]:
                        el["songs"].append(s["id"])
                        ok = False
                        logging.info(f"Added {s['title']} to {cateogry}")
                if ok:
                    logging.info(f"Added new category({cateogry} - {s[cateogry]}) with: {s['title']}")
                    self.store["data"][cateogry].append({
                            "name": s[cateogry], "songs": [s["id"]]
                        })
        self.store["data"] = self.store["data"]

    def __put_data_rec(self, base, path, value):
        if len(path) > 0:
            base[path[0]] = self.__put_data_rec(base[path[0]], path[1:], value) 
            return base
        return value
        
    

    def __create__list(self, files, music_folder):
        # TODO multithread
        songs = []
        for f in files:
            try:
                id3 = EasyID3(f)
                songs.append({
                    "title": id3["title"][0],
                    "album": id3["album"][0],
                    "artist": id3["artist"][0],
                    "track": int(id3["tracknumber"][0]),
                    "file": f
                })
            except:
                def get_track(f):
                    try:
                        return int(re.sub(r"^([0-9]*)?\s?[-#.]?\s?(.*)\.(wav|mp3|flac])$", r"\1", f))
                    except ValueError:
                        return 0

                def get_artist(music_folder, file):
                    folder_name = os.path.dirname(file)
                    while os.path.dirname(folder_name) != music_folder:
                        folder_name = os.path.dirname(folder_name)
                    return os.path.basename(folder_name)

                songs.append({
                    "title": re.sub(r"^([0-9]*)?\s?[-#.]?\s?(.*)\.(wav|mp3|flac])$", r"\2", os.path.basename(f)),
                    "album": re.sub(r"^^([0-9]*)?\s?[\.#-]?\s?(.*) ((\(*[0-9]{4}\)?))?$", r"\2", os.path.basename(os.path.dirname(f))+ ("" if os.path.basename(os.path.dirname(f)).endswith(")") else " ")),
                    "artist": get_artist(music_folder, f),
                    "track": get_track(os.path.basename(f)),
                    "file": f
                })
        songs = sorted(songs, key=lambda song:song["artist"]+song["album"]+str(song["track"])+song["title"])
        for k, s in enumerate(songs):
            s["id"] = k
        return songs

    def __build_json(self, music_folder):
        files = self.__traverse_folder(music_folder, re.compile("\.(wav|mp3|flac)$"))
        songs = self.__create__list(files, music_folder)

        return {
            "songs": songs,
            "artist": self.__filter_by_field(songs, "artist"),
            "album": self.__filter_by_field(songs, "album"),
            "playlist": [{"name": localization["favorites"], "pinned": True, "songs": []}], 
        }

    def __filter_by_field(self, songs, field):
        tuples = [(k, song[field]) for k, song in enumerate(songs)]
        ret = {}
        for t in tuples:
            if t[1] in ret.keys():
                ret[t[1]]["songs"].append(t[0])
            else:
                ret[t[1]] = {"name": t[1], "songs": [t[0]]}
        return list(ret.values())


    def __traverse_folder(self, folder, regex):
        ret = []
        for path, _, files in os.walk(folder):
            for name in files:
                if regex.search(name):
                    ret.append(os.path.join(path, name))
        return list(set(ret))