package org.test.naedmusic;

import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.common.Player;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSessionService;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;

import java.util.function.BiFunction;

public class PlaybackService extends MediaSessionService {
    private MediaSession mediaSession = null;

    public static void startService(Activity activity){
        activity.startForegroundService(new Intent(activity, PlaybackService.class));
    }

    @Override
    public void onCreate() {
        super.onCreate();
        ExoPlayer player = new ExoPlayer.Builder(this).build();
        this.mediaSession = new MediaSession.Builder(this, player).build();
    }

    @Override
    public void onDestroy() {
        mediaSession.getPlayer().release();
        mediaSession.release();
        mediaSession = null;
        super.onDestroy();
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        Player player = mediaSession.getPlayer();
        if (player.getPlayWhenReady()) {
            // Make sure the service is not in foreground.
            player.pause();
        }
        stopSelf();
    }

    @Override
    public MediaSession onGetSession(MediaSession.ControllerInfo controllerInfo) {
        // This example always accepts the connection request
        return mediaSession;
    }
}
