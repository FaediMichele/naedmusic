import os
from lib.platform.datamanager import DataManager

class WindowsDataManager(DataManager):
    '''DataManager for Windows OS'''
    def __init__(self, data_file_name=os.path.expanduser("~/playlist.json")):
        '''Create a new WindowsDataManager

        Arguments
        ---------
        data_file_name : str
            path to the configuration file. Default "~/playlist.json"
        '''
        super().__init__(os.path.join(os.path.expanduser("~"), "Music"), data_file_name)