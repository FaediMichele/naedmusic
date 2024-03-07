package org.test.naedmusic;

import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.common.Player;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSessionService;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;

import java.util.function.BiFunction;


public class MyListener implements Player.Listener  {
    private final BiFunction<String, Object, Object> callback;

    public MyListener(BiFunction<String, Object, Object> callback) {
        this.callback = callback;
    }

    @Override
    public void onIsPlayingChanged(boolean isPlaying){
        this.callback.apply("onIsPlayingChanged", isPlaying);
    }

    @Override
    public void onPlaybackStateChanged(int state){
        this.callback.apply("onPlaybackStateChanged", state);
    }
}
