package org.test.naedmusic;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;
import androidx.core.graphics.drawable.IconCompat;
import androidx.media3.common.AudioAttributes;
import androidx.media3.common.DeviceInfo;
import androidx.media3.common.MediaItem;
import androidx.media3.common.Player;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.common.MediaMetadata;
import androidx.media3.session.LibraryResult;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.session.MediaLibraryService;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSessionService;
import androidx.media3.session.SessionCommand;
import androidx.media3.session.SessionResult;
import androidx.media3.session.MediaSession.ConnectionResult;
import androidx.media3.session.MediaSession.ControllerInfo;
import androidx.media3.session.MediaSession.MediaItemsWithStartPosition;
import androidx.media3.common.Player.Commands;
import androidx.media3.common.C;

import androidx.car.app.connection.CarConnection;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;

import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.collect.ImmutableList;

import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;

import org.test.naedmusic.MyMediaLibraryCallback;
import org.test.naedmusic.MediaRepository;
import org.test.naedmusic.MyCarConnectionHandler;
import org.test.naedmusic.Localization;
import org.test.naedmusic.AudioFocusManager;


@UnstableApi
public class PlaybackService extends MediaLibraryService {
    private static final String TAG = "PlaybackService";
    private static final String CHANNEL_ID = "CHANNEL_ID_1";
    private MediaLibraryService.MediaLibrarySession mediaLibrarySession = null;
    

    private MyCarConnectionHandler carConnectionHandler = null;
    private MyCarConnectionHandler.CarConnectionListener listener = null;
    private AudioFocusManager audioFocusManager;

    public static void startService(Activity activity){
        activity.startForegroundService(new Intent(activity, PlaybackService.class));
    }

    @Override
    public void onCreate() {
        
        // Create the ExoPlayer instance
        // Set auto focus handling to false to avoid auto pausing
        ExoPlayer player = new ExoPlayer.Builder(this)
                .setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(C.USAGE_MEDIA)
                        .setAllowedCapturePolicy(C.ALLOW_CAPTURE_BY_ALL)
                        .build(),
                        false
                )
                .build();
        audioFocusManager = new AudioFocusManager(this, player);
        mediaLibrarySession = new MediaLibrarySession.Builder(this, player, new MyMediaLibraryCallback()).build();
        Context thisContext = this;


        // Player listners
        // Get the focus and raise the internal player volume when the player is playing
        // and release the focus when the player is ended
        player.addListener(new Player.Listener() {
            @Override
            public void onIsPlayingChanged(boolean isPlaying) {
                Player.Listener.super.onIsPlayingChanged(isPlaying);
                if (isPlaying){
                    audioFocusManager.requestAudioFocus();
                    audioFocusManager.raiseVolume();
                }
            }

            @Override
            public void onPlaybackStateChanged(int playbackState) {
                Log.d(TAG, "onPlaybackStateChanged: " + playbackState);

                if (player != null){
                    MediaItem currentItem = player.getCurrentMediaItem();
                    if (currentItem != null){
                        MediaRepository.setLastMediaItemId(currentItem.mediaId);
                        MediaRepository.setLastMediaItemPosition(player.getContentPosition());
                    } else{
                        MediaRepository.setLastMediaItemId("-1");
                        MediaRepository.setLastMediaItemPosition(-1L);
                    }
                }
                if (playbackState == Player.STATE_ENDED) {
                    audioFocusManager.abandonAudioFocus();
                }
                Player.Listener.super.onPlaybackStateChanged(playbackState);
            }
        });

        // Listener for the car connection
        // This is used to stop the service when the car is disconnected
        carConnectionHandler = new MyCarConnectionHandler(this);

        listener = () -> {
            MediaRepository.saveLastData(thisContext);
            if (mediaLibrarySession == null){
                carConnectionHandler.unregisterListener(listener);
            } else{
                Player _player = mediaLibrarySession.getPlayer();
                if (_player != null){
                    _player.stop();
                }
            }
            thisContext.stopService(new Intent(thisContext, PlaybackService.class));
        };
        carConnectionHandler.registerListener(listener);

        // Create the notification channel
        // This is required for media3 to handle notification
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID,
                "Naed Music",
                NotificationManager.IMPORTANCE_LOW);
        ((NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE)).createNotificationChannel(channel);

        // Load the data
        Localization.loadFromStorage(this);
        MediaRepository.loadFromStorage(this);
        audioFocusManager.requestAudioFocus();
        super.onCreate();

        // At this moment I surrendered to the fact that Android sucks and
        // I must leave this useless notification in the foreground
        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Naed Music ")
                .setContentText("Loading")
                .build();
        startForeground(1, notification);
    }

    @Override
    public void onDestroy() {
        if (mediaLibrarySession != null) {
            Player player = mediaLibrarySession.getPlayer();
            audioFocusManager.abandonAudioFocus();
            player.stop();
            player.release();
            mediaLibrarySession.release();
            mediaLibrarySession = null;
        }
        if (carConnectionHandler != null && listener != null){
            carConnectionHandler.unregisterListener(listener);
        }
        super.onDestroy();
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        Player player = mediaLibrarySession.getPlayer();
        if (player.getPlayWhenReady()) {
            // Make sure the service is not in foreground.
            player.pause();
        }
        stopSelf();
    }

    @Override
    public MediaLibrarySession onGetSession(@NonNull MediaLibrarySession.ControllerInfo controllerInfo) {
        return mediaLibrarySession;
    }
}