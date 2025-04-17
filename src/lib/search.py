from kivymd.icon_definitions import md_icons
from kivy.lang import Builder
from lib.ui.add_to_playlist_dialog import AddToPlaylistDialog
from lib.util import search
from kivymd.app import MDApp
from kivymd.uix.list import TwoLineAvatarIconListItem
from kivy.uix.screenmanager import Screen
from lib.platform.datamanager import get_data_manager
from lib.platform.localization import get_localization
from kivy.clock import Clock, ClockEvent

class Search(Screen):
    '''Screen for searching the song and adding to the playing playlist of add in a custom playlist'''
    search_event: ClockEvent = None
    all_songs: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]] = None

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ids.search_field.hint_text = get_localization()["search"]["search_field_hint"]
        self.search_event = None

    def pressed(self, value):
        '''When a result is selected play it or add to the playing playlist'''
        # value here is the OneLineListItem
        self.ids.container.clear_widgets()
        # set TextField text to selected list item
        self.ids.search_field.text = value.song["title"]
        MDApp.get_running_app().front.add_song_to_playlist(value.song)


    def set_list(self, text=""):
        '''When the search text field changed re run the search and show the results
        
        Arguments
        ---------
        text : str
            The text to search
        '''
        if self.search_event is not None:
            self.search_event.cancel()
        self.search_event = Clock.schedule_once(lambda _: self.__search(), .8)

    
    def set_focus_to_search(self):
        self.ids.search_field.focus = True
        
    
    def __search(self):
        text = self.ids.search_field.text
        if len(text.replace(" ", "")) > 0:
            self.ids.container.clear_widgets() # refresh list
            if self.all_songs == None:
               data_manager = get_data_manager()
               self.all_songs = data_manager.store["data"]["songs"]
            results = search(self.ids.search_field.text, self.all_songs)
            for value in results:
                # using casefold() to make the input case insensitve
                self.ids.container.add_widget(
                    SearchListItem(value, on_press=self.pressed)
                )
    
    def cancel(self):
        '''Close the screen and return to the front page'''
        self.ids.container.clear_widgets()
        self.ids.search_field.text = ""
        self.manager.switch_to(MDApp.get_running_app().front, direction="up")

class SearchListItem(TwoLineAvatarIconListItem):
    '''Item of the search list. Allow to add the song to the playlist and open the dialog to customize the playlists'''
    def __init__(self, song, *args, **kwargs):
        self.song = song
        super().__init__(text=song["title"], secondary_text=song["artist"], *args, **kwargs)

    def open_dialog(self):
        '''Show the dialog to customize the playlists'''
        AddToPlaylistDialog(self.song["id"], on_dialog_ended=lambda:None).show_dialog()

    def play(self):
        '''Play this song'''
        MDApp.get_running_app().front.add_song_to_playlist(self.song)
        
        