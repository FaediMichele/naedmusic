package org.test.naedmusic;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.util.Log;

import androidx.annotation.MainThread;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;

import androidx.car.app.connection.CarConnection;

import java.util.concurrent.CopyOnWriteArrayList;

public final class MyCarConnectionHandler {
    private static final String TAG = "MyCarConnectionHandler";

    private final Context applicationContext;

    private final CopyOnWriteArrayList<CarConnectionListener> listeners = new CopyOnWriteArrayList<>();

    private final BroadcastReceiver connectionReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d(TAG, "BroadcastReceiver.onReceive: " + intent.getAction());
            if (CarConnection.ACTION_CAR_CONNECTION_UPDATED.equals(intent.getAction())) {
                for (CarConnectionListener listener : listeners) {
                    listener.onConnectionStateChanged();
                }
            }
        }
    };
    private boolean isReceiverRegistered = false;
    private final Object lock = new Object();

    public interface CarConnectionListener {
        void onConnectionStateChanged();
    }

    @MainThread
    public MyCarConnectionHandler(@NonNull Context context) {
        this.applicationContext = context.getApplicationContext();
    }

    public void registerListener(@NonNull CarConnectionListener listener) {
        synchronized (lock) {
            listeners.add(listener);
            if (!isReceiverRegistered) {
                IntentFilter filter = new IntentFilter(CarConnection.ACTION_CAR_CONNECTION_UPDATED);
                ContextCompat.registerReceiver(applicationContext, connectionReceiver, filter, ContextCompat.RECEIVER_EXPORTED);
                isReceiverRegistered = true;
            }
        }
    }

    public void unregisterListener(@NonNull CarConnectionListener listener) {
        synchronized (lock) {
            listeners.remove(listener);
            if (isReceiverRegistered && listeners.isEmpty()) {
                try {
                    applicationContext.unregisterReceiver(connectionReceiver);
                } catch (IllegalArgumentException e) {
                    // Receiver might have already been unregistered, ignore.
                }
                isReceiverRegistered = false;
            }
        }
    }

    // Optional: Call this explicitly if the CarConnection instance needs cleanup
    // before all listeners are naturally unregistered (e.g., in onDestroy).
    public void release() {
        synchronized (lock) {
            if (isReceiverRegistered) {
                try {
                    applicationContext.unregisterReceiver(connectionReceiver);
                } catch (IllegalArgumentException e) {
                    // Receiver might have already been unregistered, ignore.
                }
                isReceiverRegistered = false;
            }
            listeners.clear();
        }
    }
}