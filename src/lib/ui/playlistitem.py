from kivymd.uix.card import MDCard
from kivymd.app import MDApp
from kivy.properties import ObjectProperty
from kivymd.uix.snackbar import Snackbar
from lib.platform.datamanager import get_data_manager
from lib.localization import localization
from lib.util import show_snackbar

class PlaylistItem(MDCard):
    '''Card for show a playlist

    Attributes
    ----------
    name : ObjectProperty (string)
        The name of the playlist
    image : ObjectProperty (string)
        The image of the playlist
    data : dict["name": str, "songs": list[str]]
        The data of the shown playlist

    Methods
    -------

    on_press() -> None
        Callback that occur when the card is clicked. It start playing the playlist
    '''
    name = ObjectProperty(None)
    '''The name of the playlist'''

    image = ObjectProperty(None)
    '''The image of the playlist'''

    data: dict["name": str, "songs": list[dict]] = None
    '''The data of the shown playlist'''

    def __init__(self, data:dict["name": str, "songs": list[int]], *args, **kwargs):
        '''Create new PlaylistItem

        Attributes
        ----------
        data : dict["name": str, "songs": list[str]]
            The data of the playlist. If the image field is empty try to estimate the image calling the :py:meth:`lib.ui.platform.datamanager.DataManager.get_image`
        '''
        super().__init__(*args, **kwargs)
        data_manager = get_data_manager()
        self.name.text = data["name"]
        self.data = [data_manager.store["data"]["songs"][i] for i in data["songs"]]
        if len(data["songs"]) > 0:
            self.image.source = get_data_manager().get_image([s["file"] for s in self.data])
        else:
            self.image.source = ""

    def on_press(self, *args) -> None:
        '''Callback that occur when the card is clicked. It start playing the playlist'''
        if len(self.data) > 0:
            MDApp.get_running_app().start_playlist(self.data)
        else:
            show_snackbar(localization["empty_playlist"])
        