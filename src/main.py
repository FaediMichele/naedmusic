from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from lib.front import Front
from lib.search import Search

class MusicApp(MDApp):
    '''MDApp: entrypoint for the application. Run the application using "run()"

    Attributes
    ----------
    root : Front
        The root widget

    Methods
    -------
    on_start() -> None
        Callback called when the application completed the starting process
    start_playlist(data: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]) -> None
        Start a playlist by passing its data
    '''
    root: Front = None
    '''The root widget'''

    def build(self):
        self.theme_cls.primary_palette = "DeepOrange"
        self.theme_cls.primary_hue = "A100"
        self.theme_cls.accent_palette = "Red"
        self.theme_cls.accent_hue = "100"
        sm = ScreenManager()
        self.front = Front(name="front")
        self.search = Search(name="search")
        sm.add_widget(self.front)
        sm.add_widget(self.search)
        return sm

    def on_start(self, **kwargs):
        '''Callback called when the application completed the starting process'''
        self.front.on_start(**kwargs)

    def start_playlist(self, data: list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]) -> None:
        '''Start a playlist by passing its data

        Parameters
        ----------
        data : list[dict["title": str, "album": str, "artist": str, "file": str, "track": int, "id": int]]
            List of songs to play
        '''
        self.front.start_playlist(data)



if __name__ == '__main__':
    MusicApp().run()