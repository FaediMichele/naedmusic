package org.test.naedmusic;

import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaController;
import androidx.media3.session.SessionToken;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import android.content.ComponentName;
import android.content.Context;
import android.net.Uri;
import java.util.concurrent.ExecutionException;
import java.lang.InterruptedException;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.util.concurrent.MoreExecutors;

import org.test.naedmusic.PlaybackService;
import org.test.naedmusic.MediaRepository;

public class PlayerControllerContainer {
    protected MediaController controller = null;

    public PlayerControllerContainer(Context context){
        this.requestController(context);
    }

    public MediaController getController(){
        return this.controller;
    }

    private void requestController(Context context) {
        PlayerControllerContainer this_obj = this;
        SessionToken sessionToken = new SessionToken(context, new ComponentName(context, PlaybackService.class));
        ListenableFuture<MediaController> controllerFuture = new MediaController.Builder(context, sessionToken).buildAsync();
        controllerFuture.addListener(() -> {
            try{
                this_obj.controller = controllerFuture.get();
            } catch(ExecutionException e){
                e.printStackTrace();
            } catch(InterruptedException e){
                e.printStackTrace();
            }
            
        }, MoreExecutors.directExecutor());
    }
    
}
