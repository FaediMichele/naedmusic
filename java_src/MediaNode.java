package org.test.naedmusic;

import androidx.media3.common.MediaItem;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;

public class MediaNode {
    private final Map<String, MediaNode> children = new HashMap<>();
    private final List<MediaItem> mediaItems = new ArrayList<>();

    public void addMediaItem(List<String> path, MediaItem item) {
        if (path == null || path.isEmpty()) {
            if (!mediaItems.contains(item)){
                mediaItems.add(item);
            }
        } else {
            String head = path.get(0);
            List<String> tail = path.subList(1, path.size());
            children.computeIfAbsent(head, k -> new MediaNode()).addMediaItem(tail, item);
        }
    }

    public void clearPath(List<String> path){
        if (path == null || path.isEmpty()) {
            return;
        }
        String head = path.get(0);
        if(!children.containsKey(head)){
            return;
        }
        List<String> tail = path.subList(1, path.size());
        if (tail.isEmpty()){
            children.remove(head);
        } else{
            children.get(head).clearPath(tail);
        }
    }

    public MediaNode getMediaNode(List<String> path) {
        if (path == null || path.isEmpty()) {
            return this;
        } else {
            String head = path.get(0);
            if (!children.containsKey(head)) {
                return null;
            }

            List<String> tail = path.subList(1, path.size());
            return children.get(head).getMediaNode(tail);
        }
    }

    public MediaItem getMediaItem(List<String> path) {
        String head = path.get(0);
        if (!children.containsKey(head)) {
            for (MediaItem item : mediaItems) {
                if (item.mediaId.equals(head)) {
                    return item;
                }
            }
            return null;
        }

        List<String> tail = path.subList(1, path.size());
        return children.get(head).getMediaItem(tail);
    }

    public MediaItem searchMediaItem(String id) {
        for (MediaItem item : mediaItems) {
            if (item.mediaId.equals(id)) {
                return item;
            }
        }

        for (MediaNode child : children.values()) {
            MediaItem result = child.searchMediaItem(id);
            if (result != null) {
                return result;
            }
        }

        return null;
    }

    public Map<String, MediaNode> getChildren() {
        return Collections.unmodifiableMap(children);
    }

    public List<MediaItem> getMediaItems() {
        return Collections.unmodifiableList(mediaItems);
    }

    public MediaNode getChild(String key) {
        return children.get(key);
    }

    public void clear() {
        children.clear();
        mediaItems.clear();
    }
}
