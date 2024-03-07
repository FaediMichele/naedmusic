package org.test.naedmusic;


import android.app.Activity;
import android.content.pm.PackageManager;
import android.util.Log;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.List;
import java.util.Arrays;
import java.lang.Integer;

public class MyUtil {
    // Function to check and request permission
    public static boolean[] checkPermissions(Activity activity, String[] permissions) {
        // ActivityCompat.requestPermissions(activity, permissions, 1);
        List<String> permissions_list = new ArrayList<>();
        List<Integer> permissions_indexes = new ArrayList<>();
        boolean[] ret = new boolean[permissions.length];

        for (int i=0; i < permissions.length; i++) {
            // Checking if permission is not granted

            if (ContextCompat.checkSelfPermission(activity, permissions[i]) == PackageManager.PERMISSION_DENIED) {
                permissions_list.add(permissions[i]);
                permissions_indexes.add(i);
            } else {
                ret[i] = true;
            }
        }
        if (permissions_list.size() > 0) {
            ActivityCompat.requestPermissions(activity, permissions_list.toArray(new String[0]), 1);
        }

        for (int i=0; i < permissions_indexes.size(); i++) {
            ret[permissions_indexes.get(i)] = ContextCompat.checkSelfPermission(activity, permissions[permissions_indexes.get(i)]) == PackageManager.PERMISSION_DENIED;
        }
        return ret;
    }
    public static boolean checkPermission(Activity activity, String permission) {
        return ContextCompat.checkSelfPermission(activity, permission) != PackageManager.PERMISSION_DENIED;
    }
}