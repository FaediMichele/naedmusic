from jnius import autoclass

from lib.platform.localization import Localization

Locale = autoclass('java.util.Locale')

class AndroidLocalization(Localization):
    def __init__(self, file_path='assets/localization.json'):
        super().__init__(file_path)

    def estimate_locale(self):
        # Use Android's Locale class to get the current locale
        
        return Locale.getDefault().toLanguageTag()