package org.test.naedmusic;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.MediaItem;
import android.net.Uri;

import android.content.Context;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class MediaRepository {
    private final static String TAG = "MediaRepository";
    private static final MediaNode root = new MediaNode();
    private static String lastMediaItemId = "";
    private static String lastPlaylist = "";
    private static String lastPlaylistName = "";
    private static final String STORAGE_FILE_NAME = "playlist.json";
    private static Long lastMediaItemPosition = -1L;
    private static final List<JSONObject> savedItems = new ArrayList<>();

    public static void addMediaItemToInternalStore(String[] path, String file_path, String artist, String title,
                                                   String albumTitle, int trackNumber, String id,
                                                   String image_path, boolean persistent) {
        MediaItem item = createMediaItem(file_path, artist, title, albumTitle, trackNumber, id, image_path);
        List<String> pathList = List.of(path);
        if(persistent) {
            saveMediaItem(pathList, file_path, artist, title, albumTitle, trackNumber, id, image_path);
        }
        root.addMediaItem(pathList, item);
    }


    public static void clearPath(String[] path){
        root.clearPath(List.of(path));
    }

    public static MediaItem createMediaItem(String file_path, String artist, String title,
                                            String albumTitle, int trackNumber, String id,
                                            String image_path) {
        return new MediaItem.Builder()
                .setMediaId(id)
                .setUri(Uri.parse(file_path))
                .setMediaMetadata(
                        new MediaMetadata.Builder()
                                .setArtist(artist)
                                .setAlbumArtist(artist)
                                .setAlbumTitle(albumTitle)
                                .setTrackNumber(trackNumber)
                                .setTitle(title)
                                .setArtworkUri(Uri.parse(image_path))
                                .build())
                .build();
    }

    public static void loadFromStorage(@NonNull Context context) {
        File dir = new File(context.getFilesDir(), "app");
        File file = new File(dir, STORAGE_FILE_NAME);
        if (!file.exists()) return;

        File[] subFiles = dir.listFiles();
        if (subFiles != null){
            Log.d(TAG, "loadFromStorage:\n" + dir.getName());
            for (File subFile : subFiles) {
                Log.d(TAG, "-  " + subFile.getName());
                if (subFile.getName().equals("assets")){
                    File[] subSubFiles = subFile.listFiles();
                    if (subSubFiles != null){
                        for (File subSubFile : subSubFiles) {
                            Log.d(TAG, "  -  " + subSubFile.getName());
                        }
                    }
                }
            }
        }

        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            StringBuilder builder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
            root.clear();
            JSONObject store = new JSONObject(builder.toString());
            JSONObject config = store.getJSONObject("config");
            JSONObject lastData = config.getJSONObject("last_data");

            lastPlaylist = lastData.getString("last_playlist");
            lastPlaylistName = lastData.getString("last_playlist_name");
            lastMediaItemId = lastData.getString("last_song");
            if (lastData.has("last_song_time")) {
                try{
                    lastMediaItemPosition = lastData.getLong("last_song_time");
                } catch( JSONException e){
                    Log.d(TAG, "last_song_time is not a Long: " + lastData.toString(4));
                }
                
            }

            JSONObject data = store.getJSONObject("data");
            JSONArray songs = data.getJSONArray("songs");

            String[] categories = new String[]{"artist", "album", "playlist"};
            int addedMediaItems = 0;

            for (String category : categories) {
                JSONArray subData = data.getJSONArray(category);
                for (int j = 0; j < subData.length(); j++) {
                    String name = subData.getJSONObject(j).getString("name");
                    JSONArray subDataSongsId = subData.getJSONObject(j).getJSONArray("songs");
                    for (int k = 0; k < subDataSongsId.length(); k++) {
                        int songId = subDataSongsId.getInt(k);
                        JSONObject obj = songs.getJSONObject(songId);
                        MediaItem newItem = MediaRepository.createMediaItem(
                                obj.getString("file"),
                                obj.getString("artist"),
                                obj.getString("title"),
                                obj.getString("album"),
                                obj.getInt("track"),
                                "" + songId,
                                obj.getString("image")
                        );
                        String categoryLocalized = Localization.getText(new Object[]{"category_names", category});
                        root.addMediaItem(Arrays.asList(categoryLocalized, name), newItem);
                        addedMediaItems++;
                    }
                }
            }
            Log.d(TAG, "Added from storage: " + addedMediaItems);
        } catch (IOException | JSONException e) {
            Log.e(TAG, "Failed to load media items from storage", e);
        }
    }

    private static void saveMediaItem(List<String> path, String file_path, String artist, String title,
                                      String albumTitle, int trackNumber, String id,
                                      String image_path) {
        try {
            JSONObject obj = new JSONObject();
            obj.put("path", new JSONArray(path));
            obj.put("id", id);
            obj.put("file_path", file_path);
            obj.put("artist", artist);
            obj.put("title", title);
            obj.put("albumTitle", albumTitle);
            obj.put("trackNumber", trackNumber);
            obj.put("image_path", image_path);

            savedItems.add(obj);
        } catch (JSONException e) {
            Log.e(TAG, "Failed to serialize media item", e);
        }
    }

    private static void saveAllToFile(Context context) {
        File dir = new File(context.getFilesDir(), "app");

        try (FileWriter writer = new FileWriter(new File(dir, STORAGE_FILE_NAME))) {
            JSONArray array = new JSONArray(savedItems);
            writer.write(array.toString());
        } catch (IOException e) {
            Log.e(TAG, "Failed to save media items to storage", e);
        }
    }

    private static List<String> jsonArrayToList(JSONArray jsonArray) throws JSONException {
        List<String> list = new ArrayList<>();
        for (int i = 0; i < jsonArray.length(); i++) {
            list.add(jsonArray.getString(i));
        }
        return list;
    }

    public static MediaNode getRoot() {
        return root;
    }

    public static String getLastMediaItemId(){
        return lastMediaItemId;
    }
    public static String getLastPlaylist(){
        return lastPlaylist;
    }

    public static String getLastPlaylistName(){
        return lastPlaylistName;
    }
    public static long getLastMediaItemPosition(){
        return lastMediaItemPosition;
    }

    public static void setLastMediaItemId(String lastMediaItemId){
        MediaRepository.lastMediaItemId = lastMediaItemId;
    }
    public static void setLastPlaylist(String lastPlaylist){
        MediaRepository.lastPlaylist = lastPlaylist;
    }

    public static void setLastPlaylistName(String lastPlaylistName){
        MediaRepository.lastPlaylistName = lastPlaylistName;
    }
    public static void setLastMediaItemPosition(long position){
        MediaRepository.lastMediaItemPosition = position;
    }

    public static void saveLastData(Context context) {
        File dir = new File(context.getFilesDir(), "app");
        File file = new File(dir, STORAGE_FILE_NAME);
        if (!file.exists()) return;
        JSONObject store = null;
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            StringBuilder builder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
            store = new JSONObject(builder.toString());
        } catch (IOException | JSONException e) {
            Log.e(TAG, "Failed to load media items from storage", e);
            return;
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            JSONObject config = store.getJSONObject("config");
            JSONObject lastData = config.getJSONObject("last_data");
            lastData.put("last_song", lastMediaItemId);
            lastData.put("last_song_time", lastMediaItemPosition);
            lastData.put("last_playlist", lastPlaylist);
            lastData.put("last_playlist_name", lastPlaylistName);

            writer.write(store.toString());
        } catch (IOException | JSONException e) {
            Log.e(TAG, "Failed to save media", e);
            return;
        }
    }
}
