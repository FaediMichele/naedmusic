package org.test.naedmusic;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.session.LibraryResult;
import androidx.media3.session.MediaLibraryService;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSession.MediaItemsWithStartPosition;
import androidx.media3.common.C;

import android.content.Intent;
import android.provider.MediaStore;
import android.util.Log;

import com.google.common.collect.ImmutableList;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;

import java.util.Arrays;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.time.LocalDate;
import java.util.Random;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;

import org.test.naedmusic.MediaRepository;
import org.test.naedmusic.MediaNode;


@UnstableApi
public class MyMediaLibraryCallback implements MediaLibraryService.MediaLibrarySession.Callback {
    private static final String ROOT_ID = "ROOT-ID";
    private static final String ROOT_ID_FOLDER_NAME = "Musica";

    private static final String UNKNOWN_ARTIST = "Unknown Artist";
    private static final String UNKNOWN_ALBUM = "Unknown Album";
    private static final String TAG = "MyMediaLibraryCallback";
    private static Random random = new Random(LocalDate.now().getMonthValue() * 100L + LocalDate.now().getDayOfMonth());

    @NonNull
    @Override
    public ListenableFuture<LibraryResult<MediaItem>> onGetLibraryRoot(
            @NonNull MediaLibraryService.MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @Nullable MediaLibraryService.LibraryParams params) {
        // Return the root item for browsing
        MediaItem rootItem = createBrowsableFolder(ROOT_ID, ROOT_ID_FOLDER_NAME, MediaMetadata.MEDIA_TYPE_FOLDER_PLAYLISTS, true);
        return Futures.immediateFuture(LibraryResult.ofItem(rootItem, params));
    }

    @NonNull
    @Override
    public ListenableFuture<LibraryResult<ImmutableList<MediaItem>>> onGetChildren(
            @NonNull MediaLibraryService.MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String parentId,
            int page,
            int pageSize,
            @Nullable MediaLibraryService.LibraryParams params) {
        MediaNode root_node = MediaRepository.getRoot();
        List<String> path = Arrays.asList(parentId.split("/"));
        path = path.subList(1, path.size());

        Log.d(TAG, "onGetChildren: " + parentId +  "; path: " + Arrays.toString(path.toArray()));

        MediaNode current_node = root_node.getMediaNode(path);
        if(current_node == null) {
            Log.d(TAG, "onGetChildren: empty");
            return Futures.immediateFuture(LibraryResult.ofItemList(ImmutableList.of(), params));
        }

        List<MediaItem> children = new ArrayList<>();

        for (String child : current_node.getChildren().keySet()) {
            boolean playable = current_node.getChildren().get(child).getMediaItems().size() > 0;
            children.add(createBrowsableFolder(parentId + "/" + child, child, MediaMetadata.MEDIA_TYPE_PLAYLIST, playable));
        }

        for (MediaItem item : current_node.getMediaItems()) {
            children.add(item);
        }

        Log.d(TAG, "onGetChildren: " + children.size() + " items");

        // Apply pagination (important!)
        List<MediaItem> pagedResult = getPagedList(children, page, pageSize);

        return Futures.immediateFuture(LibraryResult.ofItemList(ImmutableList.copyOf(pagedResult), params));
    }

    private List<MediaItem> shuffle(List<MediaItem> items){
        List<MediaItem> evens = new ArrayList<>();
        List<MediaItem> odds = new ArrayList<>();

        for (int i = 0; i < 19; i++) {
            odds.clear();
            evens.clear();
            for(int h = 0; h < items.size(); h += 2){
                evens.add(items.get(h));
                if(h + 1 < items.size()){
                    odds.add(items.get(h + 1));
                }
            }

            items = new java.util.ArrayList<>();
            items.addAll(odds);
            items.addAll(evens);
            Collections.shuffle(items, random);
        }
        return items;
    }

    @NonNull
    @Override
    public ListenableFuture<MediaItemsWithStartPosition> onSetMediaItems(
            @NonNull MediaSession mediaSession,
            @NonNull MediaSession.ControllerInfo controller,
            @NonNull List<MediaItem> mediaItems,
            int startIndex,
            long startPositionMs
    ) {
        MediaNode root_node = MediaRepository.getRoot();
        List<MediaItem> children = new ArrayList<>();
        List<String> path = null;

        Log.d(TAG, "onSetMediaItems: "+ mediaItems.size() + " items. Start index" + startIndex + " start position: " + startPositionMs);
        for (MediaItem item : mediaItems) {
            Log.d(TAG, "onSetMediaItems: " + item.mediaId);
            path = Arrays.asList(item.mediaId.split("/"));
            path = path.subList(1, path.size());
            children.addAll(root_node.getMediaNode(path).getMediaItems());
            for (MediaItem child : children) {
                Log.d(TAG, "onSetMediaItems: child: " + child.mediaId);
            }
        }
        if (path != null){
            Log.d(TAG, "onSetMediaItems: " + path.get(0) + "//" + path.get(1));
            MediaRepository.setLastPlaylist(path.get(0));
            MediaRepository.setLastPlaylistName(path.get(1));
        }

        MediaItemsWithStartPosition result = new MediaItemsWithStartPosition(
            shuffle(children),
            startIndex,
            startPositionMs
        );
        return Futures.immediateFuture(result);
    }

    @Override
    public void onDisconnected(MediaSession session, MediaSession.ControllerInfo controller) {
        Log.d(TAG, "My onDisconnected" + session.getId());
        MediaLibraryService.MediaLibrarySession.Callback.super.onDisconnected(session, controller);
    }

    @NonNull
    @Override
    public ListenableFuture<LibraryResult<MediaItem>> onGetItem(
            @NonNull MediaLibraryService.MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String mediaId) {
        Log.d(TAG, "onGetItem: " + mediaId);
        MediaNode root_node = MediaRepository.getRoot();

        if(mediaId.equals(ROOT_ID)){
            MediaItem rootItem = createBrowsableFolder(ROOT_ID, ROOT_ID_FOLDER_NAME, MediaMetadata.MEDIA_TYPE_FOLDER_PLAYLISTS, false);
            return Futures.immediateFuture(LibraryResult.ofItem(rootItem, new MediaLibraryService.LibraryParams
                    .Builder()
                    .setOffline(true)
                    .setSuggested(true)
                    .build()
            ));
        }

        if (mediaId.contains("/")) {
            List<String> path = Arrays.asList(mediaId.split("/"));
            path = path.subList(1, path.size());
            MediaNode node = root_node.getMediaNode(path);

            if (node != null) {
                Log.d(TAG, "onGetItem not null");
                boolean playable = node.getMediaItems().size() > 0;
                MediaItem item = null;

                Log.d(TAG, "onGetItem: " + mediaId + " -- playable: " + playable);
                if (playable) {
                    item = createBrowsableFolder(mediaId, path.get(path.size() - 1), MediaMetadata.MEDIA_TYPE_PLAYLIST, playable);
                } else{
                    item = createBrowsableFolder(mediaId, path.get(path.size() - 1), MediaMetadata.MEDIA_TYPE_FOLDER_ALBUMS, playable);
                }
                return Futures.immediateFuture(LibraryResult.ofItem(item, null));
            } else {
                MediaItem item = root_node.getMediaItem(path);
                if(item == null){
                    return Futures.immediateFuture(LibraryResult.ofError(-108));
                }
                return Futures.immediateFuture(LibraryResult.ofItem(item, null));
            }
        } else {
            return Futures.immediateFuture(LibraryResult.ofItem(root_node.searchMediaItem(mediaId), null));
        }
    }

    @NonNull
    @Override
    public ListenableFuture<MediaItemsWithStartPosition> onPlaybackResumption(
            @NonNull MediaSession mediaSession,
            @NonNull MediaSession.ControllerInfo controller) {
        Log.d(TAG, "onPlaybackResumption");
        String lastId = MediaRepository.getLastMediaItemId();
        String lastPlaylist = MediaRepository.getLastPlaylist();
        String lastPlaylistName = MediaRepository.getLastPlaylistName();
        Long lastSongPosition = MediaRepository.getLastMediaItemPosition();
        if (lastSongPosition < 0){
            lastSongPosition = C.TIME_UNSET;
        }
        MediaNode root_node = MediaRepository.getRoot();
        Log.d(TAG, "onPlaybackResumption: lastId: " + lastId + " lastPlaylist: " + lastPlaylist + " lastPlaylistName: " + lastPlaylistName);
        if (lastPlaylist.isEmpty() || lastPlaylistName.isEmpty()){
            return Futures.immediateFuture(new MediaItemsWithStartPosition(
                    ImmutableList.of(),
                    C.INDEX_UNSET,
                    C.TIME_UNSET
            ));
        }
        MediaNode node = root_node.getMediaNode(List.of(lastPlaylist, lastPlaylistName));
        if (node == null){
            return Futures.immediateFuture(new MediaItemsWithStartPosition(
                    ImmutableList.of(),
                    C.INDEX_UNSET,
                    C.TIME_UNSET
            ));
        } else {
            List<MediaItem> items = node.getMediaItems();
            if (!lastId.isEmpty()){
                for (int i = 0; i < items.size(); i++){
                    if (items.get(i).mediaId.equals(lastId)){
                        return Futures.immediateFuture(new MediaItemsWithStartPosition(
                                items,
                                i,
                                C.TIME_UNSET
                        ));
                    }
                }
            }
            return Futures.immediateFuture(new MediaItemsWithStartPosition(
                    items,
                    C.INDEX_UNSET,
                    C.TIME_UNSET
            ));
        }
    }

    private MediaItem createBrowsableFolder(String mediaId, String title, int folder_type, boolean isPlayable) {
        MediaMetadata metadata = new MediaMetadata.Builder()
                .setTitle(title)
                .setIsBrowsable(true)
                .setIsPlayable(isPlayable)
                .setMediaType(folder_type) // Is this needed?
                .build();
        return new MediaItem.Builder()
                .setMediaId(mediaId)
                .setMediaMetadata(metadata)
                .build();
    }

    /** Helper to apply pagination to a list. */
    private List<MediaItem> getPagedList(List<MediaItem> fullList, int page, int pageSize) {
        if (page < 0 || pageSize < 1) {
            page = 0;
            pageSize = Integer.MAX_VALUE;
        }

        int start = page * pageSize;
        if (start >= fullList.size()) {
            return Collections.emptyList();
        }

        int end = Math.min(start + pageSize, fullList.size());
        return new ArrayList<>(fullList.subList(start, end));
    }

    // Helper to get the total item count for a given parent ID (used for notifications).
    private int getItemCount(@NonNull String parentId) {
        Log.d(TAG, "getItemCount: " + parentId);
        MediaNode root_node = MediaRepository.getRoot();
        if(parentId.equals(ROOT_ID)){
            Log.d(TAG, "getItemCount: " + parentId + "return 2");
            return 2;
        }

        if (parentId.contains("/")) {
            List<String> path = Arrays.asList(parentId.split("/"));
            path = path.subList(1, path.size());
            MediaNode node = root_node.getMediaNode(path);

            if (node != null) {
                if (!node.getChildren().isEmpty()) {
                    Log.d(TAG, "getItemCount: " + parentId + "return " + node.getChildren().size());
                    return node.getChildren().size();
                }
                return node.getMediaItems().size();
            } else {
                Log.d(TAG, "getItemCount: " + parentId + "return 0");
                return 0;
            }
        } else {
            Log.d(TAG, "getItemCount: " + parentId + "return 1");
            return 1;
        }
    }
}
