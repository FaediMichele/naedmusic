package org.test.naedmusic;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.util.Log;

import androidx.core.content.ContextCompat;

import java.util.function.BiFunction;
import java.lang.IllegalArgumentException;

public class MyBroadcastReceiver extends BroadcastReceiver {
    private final Context context;
    private final String[] actions;
    private final BiFunction<Context, Intent, Object> callback;

    public MyBroadcastReceiver(Context context, String[] actions, BiFunction<Context, Intent, Object> callback) {
        this.context = context;
        this.actions = actions;
        this.callback = callback;
    }

    public void Start() {
        IntentFilter filter = new IntentFilter();
        for(String a : this.actions){
            filter.addAction(a);
        }
        ContextCompat.registerReceiver(this.context, this, filter, ContextCompat.RECEIVER_EXPORTED);
    }

    public void Stop() {
        try{
            this.context.unregisterReceiver(this);
        } catch(IllegalArgumentException e){
            e.printStackTrace();
        }
        
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        
        this.callback.apply(context, intent);
    }


    public class MyContainer {
        public final Context context;
        public final Intent intent;

        public MyContainer(Context context, Intent intent) {
            this.context = context;
            this.intent = intent;
        }
    }
}