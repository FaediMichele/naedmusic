from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from threading import Thread
import lib.ui.scroll # NOQA
from lib.platform.datamanager import get_data_manager
from lib.ui.category_dialog import CategoryDialog
from playing_bar import PlaylistBar
from localization import localization
import logging
from kivy.clock import Clock
from functools import partial

class MusicApp(MDApp):

    def build(self):
        self.theme_cls.primary_palette = "DeepOrange"
        self.theme_cls.primary_hue = "A100"
        self.theme_cls.accent_palette = "Red"
        self.theme_cls.accent_hue = "100"
        self.root = AppRoot()
        return self.root

    def on_start(self, **kwargs):
        self.root.on_start(**kwargs)

    def start_playlist(self, data):
        self.root.start_playlist(data)

class AppRoot(MDBoxLayout):
    playlistbar = None

    def set_loading_state(self, state):
        if state and not self.previous_state:
            self.add_widget(self.loading_spinner, 1 if self.playlistbar is None else 2)
        elif not state and self.previous_state:
            self.remove_widget(self.loading_spinner)
        self.previous_state = state

    def on_start(self, **kwargs):
        self.loading_spinner = self.ids["loading_spinner"]
        self.previous_state = True
        t = Thread(target=self.load_data)
        t.daemon = True
        t.start()

    def load_data(self):
        # if return None it require additional time.
        # When the time has passed it call the callback in the kivy thread.
        # So the thread is restarted until it return not None
        if get_data_manager(callback=self.on_start) is not None:
            Clock.schedule_once(partial(self.on_loading_ended))

    def on_loading_ended(self, _):
        data_manager = get_data_manager()
        logging.info(f'Last category: {data_manager.store["config"]["last_category"]}')
        self.set_category(data_manager.store["config"]["last_category"], force_reload=True)

    def start_playlist(self, data):
        if self.playlistbar is None:
            self.playlistbar = PlaylistBar()
            self.add_widget(self.playlistbar)

        if len(data["songs"]) > 0:
            self.playlistbar.select_playlist(data)
            self.playlistbar.play()


    def change_category_async_function(self, selected_category):
        data_manager = get_data_manager()
        data_manager.put_data(["config", "last_category"], selected_category)
        category_elements = data_manager.store["data"][selected_category]
        last_schedule_delay = self.ids["playlist_container"].set_data(category_elements)
        Clock.schedule_once(lambda _: self.set_loading_state(False), last_schedule_delay + 0.5)

    def set_category(self, selected_category, force_reload=False):
        data_manager = get_data_manager()
        if force_reload or selected_category != data_manager.store["config"]["last_category"]:
            self.set_loading_state(True)
            # if self.playlistbar is not None:
            #     self.playlistbar.close()
            #     self.remove_widget(self.playlistbar)
            #     self.playlistbar = None

            t = Thread(target=self.change_category_async_function, args=[selected_category])
            t.daemon = True
            t.start()
    
    def launch_category_dialog(self):
        category = localization["category_names"]
        data_manager = get_data_manager()
        CategoryDialog(category, data_manager.store["config"]["last_category"], self.set_category).show_dialog()
        


if __name__ == '__main__':
    MusicApp().run()