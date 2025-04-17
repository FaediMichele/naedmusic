package org.test.naedmusic;

import android.content.Context;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.os.Build;
import androidx.media3.common.AudioAttributes; // Use Media3 AudioAttributes
import androidx.media3.common.Player; // Use Media3 Player interface
import androidx.media3.common.util.Util; // Use Media3 Util for SDK_INT

public class AudioFocusManager implements AudioManager.OnAudioFocusChangeListener {
    private final Context context;
    private final Player player;
    private final AudioManager audioManager;
    private AudioFocusRequest audioFocusRequest;
    private int currentFocusState = AudioManager.AUDIOFOCUS_LOSS;

    private static final float VOLUME_DUCK = 0.0f;
    private static final float VOLUME_NORMAL = 1.0f;

    private boolean resumeWhenFocusGained = false;

    public AudioFocusManager(Context context, Player player) {
        this.context = context.getApplicationContext();
        this.player = player;
        this.audioManager = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
    }

    public void raiseVolume(){
        player.setVolume(VOLUME_NORMAL);
    }
    

    public boolean requestAudioFocus() {
        if (currentFocusState == AudioManager.AUDIOFOCUS_GAIN) {
            return true;
        }
        AudioAttributes playerAudioAttributes = player.getAudioAttributes();

        // Convert Media3 AudioAttributes to android.media.AudioAttributes for the request
        android.media.AudioAttributes systemAudioAttributes = new android.media.AudioAttributes.Builder()
                .setUsage(playerAudioAttributes.usage)
                .setContentType(playerAudioAttributes.contentType)
                .build();

        int focusRequestResult;

        audioFocusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
                .setAudioAttributes(systemAudioAttributes)
                .setAcceptsDelayedFocusGain(true)
                .setWillPauseWhenDucked(false)
                .setOnAudioFocusChangeListener(this)
                .build();
        focusRequestResult = audioManager.requestAudioFocus(audioFocusRequest);

        if (focusRequestResult == AudioManager.AUDIOFOCUS_REQUEST_GRANTED) {
            currentFocusState = AudioManager.AUDIOFOCUS_GAIN;
            return true;
        } else {
            currentFocusState = AudioManager.AUDIOFOCUS_LOSS;
            return false;
        }
    }

    public void abandonAudioFocus() {
        currentFocusState = AudioManager.AUDIOFOCUS_LOSS;
        resumeWhenFocusGained = false;

        if (audioFocusRequest != null) {
            audioManager.abandonAudioFocusRequest(audioFocusRequest);
        }
    }

    @Override
    public void onAudioFocusChange(int focusChange) {
        switch (focusChange) {
            case AudioManager.AUDIOFOCUS_GAIN:
                currentFocusState = AudioManager.AUDIOFOCUS_GAIN;
                player.setVolume(VOLUME_NORMAL);
                if (resumeWhenFocusGained) {
                   player.setPlayWhenReady(true);
                    resumeWhenFocusGained = false;
                }
                break;

            case AudioManager.AUDIOFOCUS_LOSS:
                currentFocusState = AudioManager.AUDIOFOCUS_LOSS;
                resumeWhenFocusGained = true;
                player.setVolume(VOLUME_DUCK);
                // player.pause();
                abandonAudioFocus();
                break;

            case AudioManager.AUDIOFOCUS_LOSS_TRANSIENT:
                currentFocusState = AudioManager.AUDIOFOCUS_LOSS_TRANSIENT;
                player.setVolume(VOLUME_DUCK);
                resumeWhenFocusGained = player.isPlaying() || player.getPlayWhenReady();
                // player.pause();
                break;

            case AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK:
                currentFocusState = AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK;
                player.setVolume(VOLUME_DUCK);
                resumeWhenFocusGained = false;
                break;
        }
    }
}