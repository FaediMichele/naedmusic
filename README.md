# Naed music
Application for linux, windows, android that reproduce music.

It search songs in the default os folder of music (eg. ~/Music).
It saves a file called playlist.json on ~/playlist.json if Windows or linux; on android is stored in the application reserved space.

## Features
- Filter by artist and album
- Does not use internet
- Custom playlist
- Random shaffle (seed change every day)
- On android play until the application is closed. No matter if there are other sources / call / locked.
- Multiplatform: Linux(tested on kubuntu 22.10), Windows, Android(tested on Samsung A52s)

## Future features
- Change configuration file (playlist.json) name and possibly location
- Change the gui for the playlist creation, edit and deletion. Now is functional but very counterintuitive, also bugged on smarphones
- Add hamburger menu for configuration, about, ...
- Search songs in other directory
- Exclude songs/directory
- Pin custom playlist(only favourites is pinned)
- Activity on the lock screen on android

## For android
is required to add something in the AndroidManigest.tmpl.xml in the definition of the application
unfortunately, Buildozer does not allow an external manipulation of the manifest (like using buildozer.spec):
xml```<service
    android:name=".PlaybackService"
    android:foregroundServiceType="mediaPlayback"
    android:exported="true">
    <intent-filter>
        <action android:name="androidx.media3.session.MediaSessionService"/>
    </intent-filter>
</service>```


## Known bug
- Localization seems to not correctly detect the language
- KivyMD does not work on android with version 1.2.0, actual 1.0.1 (https://github.com/kivymd/KivyMD/issues/1352)
- On linux the music use the pc default speakers. When bluetooth speaker or headphones is connected it does not use them (Only 0.1 is supported)

### Usefull suggestion(mostly for myself)
- To build for android run: "buildozer android adb -- logcat -c &&  buildozer android update debug deploy run logcat | grep python". It will clear all previous logcat and showing only the usefull ones.
- 