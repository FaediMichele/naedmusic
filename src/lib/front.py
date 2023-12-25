from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.snackbar import Snackbar
from threading import Thread
import lib.ui.scroll # type: ignore
from lib.platform.datamanager import get_data_manager
from lib.ui.category_dialog import CategoryDialog
from lib.playlistbar import PlaylistBar
from lib.localization import localization
import logging
from kivy.clock import Clock
from functools import partial
from lib.util import show_snackbar
from kivymd.app import MDApp

class Front(Screen):
    '''Front screen that contains the main page of the app.
    
    Attributes
    ----------
    plalistbar : PlaylistBar
        Bar that interact with the playing playlist
    loading_spinner : MDSpinner
        Spinner showed when there is a loading process(eg. creating config file, changing category)
    broken_state : bool
        True if the application is not usable due to missing memory permissions

    Methods
    -------
    on_start() -> None
        Callback called when loading for the application
    start_playlist(data: data : dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]) -> None
        Start a playlist by passing its data
    set_category(selected_category: str, force_reload=False) -> None
        Change the category to show (artist, album, playlist)
    launch_category_dialog() -> None
        Open the dialog for changing the selected category
    '''
    playlistbar: PlaylistBar = None
    '''Bar that interact with the playing playlist'''

    loading_spinner: MDSpinner = None
    '''Spinner showed when there is a loading process(eg. creating config file, changing category)'''

    broken_state: bool = False
    '''True if the application is not usable due to missing memory permissions'''

    def on_start(self, status=True, **kwargs) -> None:
        '''Callback called when loading for the application. Launch a thread in order to load the data asynchronously.
        
        Arguments
        ---------
        status : bool
            False if the previous attempt of loading data from memory failed
        '''
        if not status:
            def no_permission(_):
                show_snackbar(localization["errors"]["asking_permissions"])
                self.__set_loading_state(False)
                self.broken_state = True
            Clock.schedule_once(no_permission)
            return
        self.loading_spinner = self.ids["loading_spinner"]
        self._previous_state = True
        t = Thread(target=self.load_data)
        t.daemon = True
        t.start()

    def start_playlist(self, data: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]) -> None:
        '''Start a playlist by passing its data

        Arguments
        ---------
        data: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]
            The songs of the playlist
        '''
        if not self.broken_state:
            if self.playlistbar is None:
                self.playlistbar = PlaylistBar()
                self.ids.layout.add_widget(self.playlistbar)

            if len(data) > 0:
                self.playlistbar.select_playlist(data)
                self.playlistbar.play()

    def set_category(self, selected_category: str, force_reload=False) -> None:
        '''Change the category to show (artist, album, playlist)

        Arguments
        ---------
        selected_category: str
            Category to change into. (artist, album, playlist)
        force_reload: bool
            Reload the category even if selected_category is equals to the current displayed category
        '''
        if not self.broken_state:
            data_manager = get_data_manager()
            if force_reload or selected_category != data_manager.store["config"]["last_category"]:
                self.ids["topbar"].title = self.__localize_category(selected_category)
                self.__set_loading_state(True)
                # if self.playlistbar is not None:
                #     self.playlistbar.close()
                #     self.ids.layout.remove_widget(self.playlistbar)
                #     self.playlistbar = None

                t = Thread(target=self.__change_category_async_function, args=[selected_category])
                t.daemon = True
                t.start()
    
    def launch_category_dialog(self):
        '''Launch the dialog that allow to choose the category being showed'''
        if not self.broken_state:
            categories = localization["category_names"]
            data_manager = get_data_manager()
            CategoryDialog(categories, data_manager.store["config"]["last_category"], self.set_category).show_dialog()

    def add_song_to_playlist(self, song: dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]):
        '''Add a song to the current playing playlist. If there is not a playing playlist create a new one
        
        Attributes
        ----------
        song : dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]
            The song to play
        '''
        if not self.broken_state:
            if self.playlistbar is not None:
                self.playlistbar.playlist.add_song_to_playlist(song)
            else:
                self.start_playlist([song])

    def search(self):
        '''Change the screen to the search one'''
        search = MDApp.get_running_app().search
        self.manager.switch_to(search, direction="down")
        search.set_focus_to_search()

    def load_data(self):
        # if return None it require additional time.
        # When the time has passed it call the callback in the kivy thread.
        # So the thread is restarted until it return not None
        data_manager = get_data_manager(callback=self.on_start)
        if data_manager is not None:
            Clock.schedule_once(partial(self.__on_loading_ended))
            if data_manager.check_and_run_update():
                Clock.schedule_once(partial(self.__on_loading_ended))

    def __on_loading_ended(self, _):
        data_manager = get_data_manager()
        logging.info(f'Last category: {data_manager.store["config"]["last_category"]}')
        self.set_category(data_manager.store["config"]["last_category"], force_reload=True)

    def __change_category_async_function(self, selected_category):
        data_manager = get_data_manager()
        data_manager.put_data(["config", "last_category"], selected_category)
        category_elements = data_manager.store["data"][selected_category]
        last_schedule_delay = self.ids["playlist_container"].set_data(category_elements)
        Clock.schedule_once(lambda _: self.__set_loading_state(False), last_schedule_delay + 0.2)

    def __set_loading_state(self, state):
        if state and not self._previous_state:
            self.ids.layout.add_widget(self.loading_spinner, 1 if self.playlistbar is None else 2)
        elif not state and self._previous_state:
            self.ids.layout.remove_widget(self.loading_spinner)
        self._previous_state = state

    def __localize_category(self, category):
        for l_i in localization["category_names"]:
            if l_i[0] == category:
                return l_i[1]