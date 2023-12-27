
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList
from kivy.properties import NumericProperty
from lib.ui.playlistitem import PlaylistItem
from kivy.clock import Clock
from lib.platform.datamanager import get_data_manager

loading_element_per_second = 300 # Used to set the 
'''Number of elements to show per second'''

_set_data_count = 0 #Used to not mix closed in time call to set_data

class MyScrollView(ScrollView):
    '''ScrollView that call on_scroll_stop on the first child(MDList) when on_scroll_move and update_from_scroll occur. Used to unload the image when the element is not visible

    Methods
    -------
    update_from_scroll(): -> None
        Call on_scroll_stop on the first child
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            on_scroll_move=lambda self, _: self.children[0].on_scroll_stop(self))

    def update_from_scroll(self, *largs) -> None:
        super().update_from_scroll(*largs)
        self.children[0].on_scroll_stop(self)

class MyMDList(MDList):
    '''MDList that unload the card image when not visible
    
    Attributes
    ----------
    load_space : NumericProperty (int)
        Number of images above, below and not visible to load in order to not show the empty image. If set to 0 does not unload images. Default 2

    Methods
    -------
    on_scroll_stop(parent:ScrollView) -> None
        Hide images not visible or show visible ones
    set_data(data: list[dict["name":str, "songs": list[str]]]) -> None
        Set the playlists to show. Order them by pinned and name
    '''

    load_space = NumericProperty(2)
    '''Number of images above, below and not visible to load in order to not show the empty image. If set to 0 does not unload images. Default 2'''

    def on_scroll_stop(self, parent: ScrollView) -> None:
        '''Hide images not visible or show visible ones
        
        Arguments
        ---------
        parent : ScrollView
            The ScrollView where the images to hide are
        '''
        if self.load_space > 0:
            for child in self.children:
                pos = parent.to_parent(child.pos[0], child.pos[1])[1]
                if pos + child.size[1] < -self.load_space or pos > parent.height+self.load_space:
                    if child.image.source != "":
                        child.image.save_image_tmp = child.image.source
                        child.image.source = ""
                elif hasattr(child.image, "save_image_tmp") and child.image.save_image_tmp != "":
                    child.image.source = child.image.save_image_tmp
    
    def set_data(self, data: list[dict["name":str, "songs": list[int]]]) -> None:
        '''Show the playlist list. Order them by pinned and name

        Attributes
        ----------
        data : list[dict["name":str, "songs": list[int]]]
            The playlist list to show.

        Returns
        -------
        int
            Time delay when the last element is loaded. It should be safe to use the widgets
        '''
        # Ready for async
        # Return number of second for last schedule
        global loading_element_per_second
        global _set_data_count
        _set_data_count += 1
        
        Clock.schedule_once(lambda _: self.clear_widgets())
        if len(data) == 0:
            return 1 / loading_element_per_second
        for i, playlist in enumerate(sorted(data, key=self.__key_order)):

            # Create function in order to not intersect with
            # the change of playlist during for set_data_count
            def create_func(pl, set_data):
                def tmp(_):
                    if set_data == _set_data_count:
                        self.add_widget(PlaylistItem(pl))
                return tmp
            
            Clock.schedule_once(create_func(playlist, _set_data_count),  (i+1) // loading_element_per_second + ((i+1) % loading_element_per_second) / loading_element_per_second)
        return (i+1) // loading_element_per_second + ((i+1) % loading_element_per_second) / loading_element_per_second
    
    def __key_order(self, x):
        if "pinned" in x.keys() and x["pinned"]:
            return "a" + x["name"].lower().strip()
        else:
            return "z" + x["name"].lower().strip()