Map Feature (/map command)
=================================

This deployment includes an overview map capability ported from the copyDefHack branch.

Commands (group chats only):

 /map                Render a snapshot of recent observations (default lookback window)
 /map <minutes>      Render a snapshot limited to the last N minutes
 /map diff           Highlight changes (new / moved / stale) since previous snapshot
 /map focus <terms>  Set focus filters (keywords or priority like P1). Example: /map focus armor P1
 /map focus clear    Clear focus terms
 /map live [seconds] Start periodic map updates (minimum 120s interval, default configured)
 /map stop           Stop live map updates
 /map help           Show help summary

Layers (removed)
----------------
Previous layer selection functionality has been deprecated; all observations are displayed subject to focus filters.

Environment Variables
---------------------
MAP_TILE_URL (default https://tile.openstreetmap.org/{z}/{x}/{y}.png)
MAP_WIDTH (default 1024)
MAP_HEIGHT (default 768)
MAP_LOOKBACK_MINUTES (default 120)
MAP_CLUSTER_THRESHOLD_METERS (default 200)
MAP_LIVE_INTERVAL_SECONDS (default 420)
MAP_MAX_POINTS (default 400)
MAP_AGE_FADE_MINUTES (default 60)
MAP_RECENT_SECONDS (default 300)
MAP_CONFIDENCE_SCALE_METERS (default 15)

Dependencies added: pillow, staticmap

Notes
-----
- Accuracy rings scale with MAP_CONFIDENCE_SCALE_METERS
- Diff mode tracks new / moved / stale relative to last baseline snapshot. Baseline updates after each snapshot unless diff requested.
- Live mode posts periodically until /map stop.
