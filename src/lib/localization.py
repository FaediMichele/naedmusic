'''
Loads the strings for the current os language
'''
import locale

__languages = [
    {"names": ["en_EN", "en_US"], "value": {
        "filechooser":{
            "title_save": "Save configuration file",
            "title_load": "Load configuration file",
        },
        "category_names": [("artist", "Artist"), ("album", "Album"), ("playlist", "Playlist")],
        "category_dialog": {
            "title": "Select category",
            "confirm": "Ok",
            "cancel": "Cancel"
        },
        "add_to_playlist_dialog": {
            "title": "Add to playlist - {name}",
            "delete": "Delete",
            "confirm": "Confirm",
            "cancel": "Cancel",
            "rename": "Rename",
            "edit": "Edit",
            "new": "New",

            "rename_dialog_init": "Rename",
            "delete_dialog_init": "Delete",

            "delete_ask_title": "Delete playlist - {name}",
            "delete_ask_yes": "Confirm",
            "delete_ask_no": "Cancel",

            "rename_ask_title": "Rename playlist - {name}",
            "rename_ask_yes": "Confirm",
            "rename_ask_no": "Cancel",
            "rename_ask_hint": "Playlist name",

            "new_ask_title": "Create new playlist",
            "new_ask_yes": "Confirm",
            "new_ask_no": "Cancel",
            "new_ask_hint": "New playlist name",

            "edit_ask_title": "Edit the playlist",
            "edit_cancel": "Cancel",
        },
        "empty_playlist": "This playlist is empty!",
        "search":{
            "search_field_hint": "Title"
        },
        "errors": {
            "read_infos": "Error reading {song} infos. Message: {msg}.",
            "opening_sound": "Error reading {song} and cannot be played. Message: {msg}.",
            "asking_permissions": "Permissions to use memory not granted. The application will not load the songs!"
        },
        "favorites": "Favorites",
        "notification": {
            "notification_channel_name": "Playlist notification",
            "notification_channel_desc": "The notification that shows the current playing song, is possible to pause and skip a song"
        }
    }},
    {"names": ["it_IT"], "value": {
        "filechooser":{
            "title_save": "Salva file di configurazione",
            "title_load": "Carica file di configurazione",
        },
        "category_names": [("artist", "Artisti"), ("album", "Album"), ("playlist", "Playlist")],
        "category_dialog": {
            "title": "Seleziona categoria",
            "confirm": "Ok",
            "cancel": "Annulla"
        },
        "add_to_playlist_dialog": {
            "title": "Aggiungi a playlist - {name}",
            "delete": "Cancella",
            "confirm": "Conferma",
            "cancel": "Annulla",
            "rename": "Rinomina",
            "edit": "Modifica",
            "new": "Nuova",

            "rename_dialog_init": "Rinomina",
            "delete_dialog_init": "Elimina",

            "delete_ask_title": "Cancella playlist - {name}",
            "delete_ask_yes": "Conferma",
            "delete_ask_no": "Annulla",

            "rename_ask_title": "Rinomina playlist - {name}",
            "rename_ask_yes": "Conferma",
            "rename_ask_no": "Annulla",
            "rename_ask_hint": "Nome playlist",

            "new_ask_title": "Crea nuova playlist",
            "new_ask_yes": "Conferma",
            "new_ask_no": "Annulla",
            "new_ask_hint": "Nome nuova playlist",

            "edit_ask_title": "Modifica la playlist",
            "edit_cancel": "Cancella",
        },
        "empty_playlist": "Questa playlist è vuota",
        "search":{
            "search_field_hint": "Titolo"
        },
        "errors": {
            "read_infos": "Errore leggendo le informazioni di {song}. Informazioni errore: {msg}",
            "opening_sound": "Errore tentando di riprodurre {song}. Informazioni errore: {msg}"
        },
        "favorites": "Preferiti"
    }}
]

localization = __languages[0]["value"]
for l in __languages:
    if locale.getlocale()[0] in l["names"]:
        localization = l["value"]