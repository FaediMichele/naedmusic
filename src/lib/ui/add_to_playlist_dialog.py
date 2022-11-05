from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.list.list import CheckboxLeftWidget
from localization import localization
from lib.platform.datamanager import get_data_manager
from kivy.uix.boxlayout import BoxLayout
from typing import Callable, Any

class AddToPlaylistDialog():
    '''Dialog that manage insertion/removal of a song in the playlists. Also manage creation, renaming, deletion of playlists.
    The input is a song followed by its name. It can create sub dialogs.
    If the list of item is changed it is not possible to update the list(bug with MDDialog.update_items). So the actual Dialog is closed and is created a new one without applying the changes to memory.
    The memory is updated only when the main dialog is closed with the confirm button.

    Methods
    -------
    show_dialog() -> None
        Open the dialog
    on_item_selected(playlist_selected) -> None
        Callback called when an item is selected
    on_delete_close(_) -> None
        Callback called when the dialog for deleting a playlist is closed negatively
    on_delete_confirm(_) -> None
        Callback called when the dialog for deleting a playlist is closed positively
    on_rename_close(_) -> None
        Callback called when the dialog for renaming a playlist is closed negatively
    on_rename_confirm(_) -> None
        Callback called when the dialog for renaming a playlist is closed positively
    on_new_close(_) -> None
        Callback called when the dialog for creating a playlist is closed negatively
    on_new_confirm(_) -> None
        Callback called when the dialog for creating a playlist is closed positively
    on_delete(_) -> None
        Callback called when the button that open the dialog for deleting a playlist is pressed
    on_rename(_) -> None
        Callback called when the button that open the dialog for deleting a playlist is pressed
    on_new(_) -> None
        Callback called when the button that open the dialog for deleting a playlist is pressed
    on_close(_) -> None
        Callback called when the main dialog is closing negatively
    on_confirm(_) -> None
        Callback called when the main dialog is closing positively and the data is saved in the memory
    
    '''
    _dialog = None
    _delete_dialog = None
    _rename_dialog = None
    _new_dialog = None
    _last_selected = None

    def __init__(self, song_path: str, song_name: str,on_dialog_ended: Callable[[], Any], playlist_list: list[dict["name": str, "image": str, "songs": list[str]]]=None, **kwargs):
        '''Create a new AddToPlaylistDialog
        
        Arguments
        ---------
        song_path : string
            Path of the song
        song_name : string
            Name of the song
        on_dialog_ended : () -> None
            Callback called when the dialog is closed positively or negatively
        '''
        super().__init__(**kwargs)
        datamanager = get_data_manager()
        self._song_path = song_path
        self._song_name = song_name
        self._on_dialog_ended = on_dialog_ended
        if playlist_list is None:
            self._playlists, self._playlists_indexes = self.__get_playlist(datamanager.store["data"]["playlist"])
        else:
            self._playlists, self._playlists_indexes = self.__get_playlist(playlist_list)

    def show_dialog(self):
        '''Open the dialog'''
        if self._dialog is None:
            self.__create_dialog()
        self._dialog.open()

    def on_item_selected(self, playlist_selected: int):
        '''Callback called when an item is selected

        Arguments
        ---------
        playlist_selected : int
            The index of the item to select
        '''
        if playlist_selected is None:
            self._dialog.buttons[0].opacity = 0
            self._dialog.buttons[0].disabled = True
            self._dialog.buttons[1].opacity = 0
            self._dialog.buttons[1].disabled = True
        elif self._last_selected is None:
            self._dialog.buttons[0].opacity = 1
            self._dialog.buttons[0].disabled = False
            self._dialog.buttons[1].opacity = 1
            self._dialog.buttons[1].disabled = False
        self._last_selected = playlist_selected

    def on_delete_close(self, _):
        '''Callback called when the dialog for deleting a playlist is closed negatively
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        self._delete_dialog.dismiss()

    def on_delete_confirm(self, _):
        '''Callback called when the dialog for deleting a playlist is closed positively
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        del self._playlists[self._last_selected]
        items = self._dialog.items
        for i in items[self._last_selected:]:
            i.playlist_index -=1
        del items[self._last_selected]
        self.items = [i.create_copy() for i in items]
        if self._last_selected < len((self._playlists_indexes)):
            self._playlists_indexes = [i if i<self._playlists_indexes[self._last_selected] else i-1 for i in self._playlists_indexes]
        del self._playlists_indexes[self._last_selected]
        self.on_item_selected(None)
        self._delete_dialog.dismiss()
        self.__copy_dialog()

    def on_rename_close(self, _):
        '''Callback called when the dialog for renaming a playlist is closed negatively
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        self._rename_dialog.dismiss()

    def on_rename_confirm(self, _):
        '''Callback called when the dialog for renaming a playlist is closed positively
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        self._playlists[self._last_selected]["name"] = self._rename_dialog.content_cls.ids["text_field"].text
        self._items[self._last_selected].text = self._playlists[self._last_selected]["name"]
        self._rename_dialog.dismiss()

    def on_new_close(self, _):
        '''Callback called when the dialog for creating a playlist is closed negatively
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        self._new_dialog.dismiss()

    def on_new_confirm(self, _):
        '''Callback called when the dialog for creating a playlist is closed positively
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        new_playlist = {"name": self._new_dialog.content_cls.ids["text_field"].text, "songs": [], "image": ""}
        self._playlists.append(new_playlist)
        self._playlists_indexes.append(len(self._playlists_indexes))
        self._items = [i.create_copy() for i in self._items]
        self._items.append(ItemConfirm(playlist_index=len(self._items), text=new_playlist["name"], value=False, on_selected_item=self.on_item_selected))
        self._new_dialog.dismiss()
        self.__copy_dialog()

    def on_delete(self, _):
        '''Callback called when the button that open the dialog for deleting a playlist is pressed
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        if self._delete_dialog is None:
            self.__create_delete_dialog()
        self._delete_dialog.title = localization["add_to_playlist_dialog"]["delete_ask_title"].format(name=self._playlists[self._last_selected]["name"])
        self._delete_dialog.open()

    def on_rename(self, _):
        '''Callback called when the button that open the dialog for deleting a playlist is pressed
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        if self._rename_dialog is None:
            self.__create_rename_dialog()
        self._rename_dialog.title = localization["add_to_playlist_dialog"]["rename_ask_title"].format(name=self._playlists[self._last_selected]["name"])
        self._rename_dialog.content_cls.ids["text_field"].text = self._playlists[self._last_selected]["name"]
        self._rename_dialog.open()

    def on_new(self, _):
        '''Callback called when the button that open the dialog for deleting a playlist is pressed
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        if self._new_dialog is None:
            self.__create_new_dialog()
        self._new_dialog.title = localization["add_to_playlist_dialog"]["new_ask_title"]
        self._new_dialog.open()

    def on_close(self, _):
        '''Callback called when the main dialog is closing negatively'''
        self._dialog.dismiss()
    
    def on_confirm(self, _):
        '''Callback called when the main dialog is closing positively and the data is saved in the memory
        
        Arguments
        ---------
        _ : Any
            [Unused] The widget that call the method
        '''
        data_manager = get_data_manager()
        data_manager.put_data(["data", "playlist"], self.__calculate_new_playlist_data())
        self._dialog.dismiss()


    def __get_playlist(self, playlist_list):
        def key(x):
            if self._song_path in playlist_list[x]["songs"]:
                return "a"+playlist_list[x]["name"]
            else:
                return "z"+playlist_list[x]["name"]
        
        indexes = sorted(range(len(playlist_list)), key=key)
        return [playlist_list[indexes[i]] for i in range(len(playlist_list))], indexes

    def __copy_dialog(self):
        # Since MDDialog.update_items does not work properly, modifying the _items list will create a new dialog. 
        old_callback = self._on_dialog_ended
        self._on_dialog_ended = lambda:None
        playlist_list=self.__calculate_new_playlist_data()
        self._dialog.dismiss()
        AddToPlaylistDialog(self._song_path, self._song_name, old_callback, playlist_list=playlist_list).show_dialog()




    def __create_dialog(self):
        self._items = [ItemConfirm(playlist_index=i, text=pl["name"], value=self._song_path in pl["songs"], on_selected_item=self.on_item_selected) for i, pl in enumerate(self._playlists)]
        
        self._dialog = MDDialog(
            title=localization["add_to_playlist_dialog"]["title"].format(name=self._song_name),
            type="confirmation",
            items=self._items,
            buttons=[
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["delete"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_delete,
                    disabled=True,
                    opacity=0
                ),
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["rename"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_rename,
                    disabled=True,
                    opacity=0
                ),
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["new"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_new
                ),
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["cancel"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_close
                ),
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["confirm"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_confirm
                ),
            ],
        )

        old_dismiss = self._dialog.dismiss
        def new_dismiss():
            old_dismiss(force = True)
            self._on_dialog_ended()
        self._dialog.dismiss = new_dismiss



    def __create_delete_dialog(self):
        self._delete_dialog = MDDialog(
            title="",
            buttons=[
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["delete_ask_yes"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_delete_confirm
                ),
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["delete_ask_no"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_delete_close
                ),
            ]
        )
    

    

    def __create_rename_dialog(self):
        self._rename_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=NewRenameDialogContent(),
            buttons=[
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["rename_ask_yes"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_rename_confirm
                ),
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["rename_ask_no"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_rename_close
                ),
            ]
        )
        self._rename_dialog.content_cls.ids["text_field"].hint_text = localization["add_to_playlist_dialog"]["rename_ask_hint"]

    

    def __create_new_dialog(self):
        self._new_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=NewRenameDialogContent(),
            buttons=[
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["new_ask_yes"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_new_confirm
                ),
                MDFlatButton(
                    text=localization["add_to_playlist_dialog"]["new_ask_no"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_new_close
                ),
            ]
        )
        self._new_dialog.content_cls.ids["text_field"].hint_text = localization["add_to_playlist_dialog"]["new_ask_hint"]

    def __calculate_new_playlist_data(self):
        for i, playlist in enumerate(self._playlists):
            if self._song_path not in playlist["songs"] and self._items[i].ids["check"].active:
                playlist["songs"].append(self._song_path)
            elif self._song_path in playlist["songs"] and not self._items[i].ids["check"].active:
                playlist["songs"].remove(self._song_path)
        return [self._playlists[self._playlists_indexes[i]] for i in range(len(self._playlists_indexes))]    

class ItemConfirm(OneLineAvatarIconListItem):
    divider = None
    playlist_index = None

    def __init__(self, playlist_index, value, on_selected_item, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids["check"].active = value
        self.playlist_index = playlist_index
        self._on_selected_item = on_selected_item

    def set_icon(self, _):
        self.ids["check"].active = not self.ids["check"].active
        self._on_selected_item(self.playlist_index)

    def create_copy(self):
        return ItemConfirm(self.playlist_index, self.ids["check"].active, self._on_selected_item, text=self.text)

class NewRenameDialogContent(BoxLayout):
    pass