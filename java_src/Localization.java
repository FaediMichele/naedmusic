package org.test.naedmusic;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.media3.common.MediaItem;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

import java.util.HashMap;
import java.util.Map;
import java.util.Arrays;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

// import com.hubspot.jinjava.Jinjava;

public class Localization {
    private final static String TAG = "Localization";
    private static JSONObject activeLocalization = null;
    private static JSONArray allLocalizations = null;

    public static String getText(Object[] path) {
        return getText(path, new HashMap<>());
    }

    public static String getText(Object[] path, Map<String, String> params) {
        // Navigate the JSON object using the path
        Object current = activeLocalization;
        for (Object key : path) {
            if (key instanceof String){
                if (!((JSONObject) current).has((String) key)){
                    Log.d(TAG, "Key does not exist in localization obj. Key: " + (String) key + ", object: " + current.toString());
                }
                current = ((JSONObject) current).opt((String) key);
            }
            else if (key instanceof Integer){
                if (((JSONArray) current).length() < ((Integer) key)){
                    Log.d(TAG, "Key does not exist in localization obj. Key: " + key + ", object: " + current.toString());
                }
                current = ((JSONArray) current).opt((Integer) key);
            }
        }
        String rawTemplate = (String) current;
        if (!params.isEmpty()){
            throw new UnsupportedOperationException("params not yet implemented");
            // Jinjava jinjava = new Jinjava();
            // return jinjava.render(rawTemplate, params);
        }else {
            return rawTemplate;
        }
    }

    public static void loadFromStorage(@NonNull Context context) {
        if (allLocalizations == null){
            File dir = new File(context.getFilesDir(), "app");
            File assets = new File(dir, "assets");
            if (!assets.exists()) return;
            File file = new File(assets, "localization.json");

            try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
                StringBuilder builder = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    builder.append(line);
                }
                allLocalizations = new JSONArray(builder.toString());
            } catch (IOException | JSONException e) {
                Log.e(TAG, "Failed to load media items from storage", e);
            }
        }
        String userLanguage = Locale.getDefault().toLanguageTag().replace('-', '_');
        Log.d(TAG, "User language: " + userLanguage);

        try{
            for (int i=0; i < allLocalizations.length(); i++){
                JSONObject localizationRoot = allLocalizations.getJSONObject(i);
                JSONArray supportedLanguages = localizationRoot.getJSONArray("names");

                for (int j=0; j < supportedLanguages.length(); j++){
                    if (supportedLanguages.getString(j).equals(userLanguage)) {
                        activeLocalization = localizationRoot.getJSONObject("value");
                        return;
                    }
                }
            }

            for (int i=0; i < allLocalizations.length(); i++){
                JSONObject localizationRoot = allLocalizations.getJSONObject(i);
                JSONArray supportedLanguages = localizationRoot.getJSONArray("names");

                for (int j=0; j < supportedLanguages.length(); j++){
                    if (supportedLanguages.getString(j).equals("en_EN")) {
                        activeLocalization = localizationRoot.getJSONObject("value");
                        return;
                    }
                }
            }
        } catch (JSONException e){
            Log.e(TAG, "Failed to load media items from storage", e);
        }
    }
}
