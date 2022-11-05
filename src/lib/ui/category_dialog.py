from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.list.list import CheckboxLeftWidget
from localization import localization
from typing import Callable, Any

class CategoryDialog():
    '''Dialog for selecting the category to show. The categories are defined in :py:const:`localization.localization["category_names"]`.
    Show a Checkbox exclusive list, one for each category. Contains 2 buttons: confirm and cancel

    Attributes
    ----------
    dialog : MDDialog
        MDDialog that contains all the visual elements

    Methods
    -------
    show_dialog() -> None
        Show the dialog. Create the object lazily
    '''
    dialog: MDDialog = None

    def __init__(self, item_list: list[tuple[str, str]], initial_category: str, on_dialog_ended: Callable[[str], Any], **kwargs):
        '''Create the CategoryDialog object.

        Arguments
        ---------
        item_list : list[tuple(str, str)]
            list of categories. Each category is defined by tag and localized_tag (eg. ("artist", "Artist") or ("artist", "Artisti"))
        initial_category : str
            Category already viewed
        on_dialog_ended: (str) -> Any
            Callback called when the dialog ends. It pass the selected category tag
        '''
        super().__init__(**kwargs)
        self.on_dialog_ended = on_dialog_ended
        self.item_list = item_list
        self.initial_category = initial_category

    def show_dialog(self) -> None:
        '''Show the dialog window'''
        if self.dialog is None:
            self.__create_dialog()
        self.dialog.open()

    def __create_dialog(self):        
        self.items = [ItemConfirmExclusive(tag=tag, text=name, value=tag==self.initial_category) for (tag, name) in self.item_list]
        
        self.dialog = MDDialog(
            title=localization["category_dialog"]["title"],
            type="confirmation",
            items=self.items,
            buttons=[
                MDFlatButton(
                    text=localization["category_dialog"]["cancel"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_cancel
                ),
                MDFlatButton(
                    text=localization["category_dialog"]["confirm"],
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=self.on_confirm
                ),
            ],
        )

        old_dismiss = self.dialog.dismiss
        def new_dismiss(tag=self.initial_category):
            old_dismiss(force = True)
            self.on_dialog_ended(tag)
        self.dialog.dismiss = new_dismiss

    def on_cancel(self, _):
        self.dialog.dismiss(self.initial_category)
        
    def on_confirm(self, _):
        for item in self.items:
            if item.ids["check"].active:
                self.dialog.dismiss(item.tag)
                return

class ItemConfirmExclusive(OneLineAvatarIconListItem):
    '''Item for confirmation. Simple one line row that contains a checkbox.'''
    divider = None

    def __init__(self, tag: str, value:bool, *args, **kwargs):
        '''Create new ItemConfirmExclusive.

        Arguments
        ---------
        tag : str
            Tag of the item (eg. "artist")
        value : bool
            Initial value of the checkbox
        '''
        super().__init__(*args, **kwargs)
        self.tag = tag
        self.ids["check"].active = value

    def set_icon(self, instance_check: CheckboxLeftWidget) -> None:
        '''Function called when ItemConfirmExclusive is clicked. It check the checkbox
        
        Arguments
        ---------
        instance_check: CheckboxLeftWidget
            The clicked widget
        '''
        instance_check.active = True