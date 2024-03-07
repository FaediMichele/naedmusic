from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
from kivymd.toast.kivytoast.kivytoast import toast
from plyer import filechooser
from kivy.logger import Logger
from kivy.utils import platform
from lib.localization import localization
from kivymd.app import MDApp

from lib.platform.datamanager import get_data_manager, reload_data_manager
from lib.platform.android.util import save_external_file, load_external_file

import os
import json

class Menu(MDNavigationDrawer):
    def download_configuration_file(self):
        def on_ready_data_manager(data_manager):

            dest_file = os.path.join(os.path.expanduser("~"), 'playlist.json')

            if os.path.exists(dest_file):
                filename = ".".join(data_manager.store.filename.split('.')[:-1])
                ext = data_manager.store.filename.split('.')[-1]
                i = 0
                while os.path.exists(f'{filename} ({i}).{ext}'):
                    i += 1
                
                dest_file = f'{filename} ({i}).{ext}'

            data = json.dumps(data_manager.store._data)

            # with open(data_manager.store.filename, 'r') as f:
            #     data = f.readlines()
            

            if platform == 'android':
                save_external_file('playlist.json', data)
            else:
                def on_selection(files):
                    with open(files[0], 'w') as f_w:
                        f_w.writelines(data)
                filechooser.save_file(
                    path=os.path.expanduser("~"),
                    multiple=False,
                    filters=["*json"],
                    title=localization["filechooser"]["title_save"], 
                    callback=on_selection)

        data_manager = get_data_manager(on_ready_data_manager)
        if data_manager is not None:
            on_ready_data_manager(data_manager)

    def load_configuration_file(self):
        def on_ready_data_manager(data_manager):

            if platform == 'android':
                def on_selection(uri, content):
                    data = json.loads(content)
                    with open(data_manager.store.filename, 'w') as f:
                        json.dump(data, f, indent=data_manager.store.indent, sort_keys=data_manager.store.sort_keys)
                    reload_data_manager()
                    MDApp.get_running_app().front.load_data()
                load_external_file(on_selection)
            else:

                def on_selection(files):
                    Logger.debug(f"Results of selection: {files}")
                    # with open(files[0], 'r') as f_r:
                    #     with open(data_manager.store.filename, 'w') as f_w:
                    #         f_w.writelines(f_r.readlines())
            
                filechooser.open_file(
                    path=os.path.expanduser("~"),
                    multiple=False,
                    filters=["*json"],
                    title=localization["filechooser"]["title_load"], 
                    on_selection=on_selection)
            

        data_manager = get_data_manager(on_ready_data_manager)
        if data_manager is not None:
            on_ready_data_manager(data_manager)