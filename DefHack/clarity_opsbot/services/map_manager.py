"""Overview map management, storage, and rendering utilities.

Ported from copyDefHack version to enable /map feature in main DefHack bot.
"""

from __future__ import annotations

import asyncio
import io
import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from staticmap import IconMarker, StaticMap

from ..config import (
    MAP_CLUSTER_THRESHOLD_METERS,
    MAP_CONFIDENCE_SCALE_METERS,
    MAP_HEIGHT,
    MAP_LIVE_INTERVAL_SECONDS,
    MAP_LOOKBACK_MINUTES,
    MAP_MAX_POINTS,
    MAP_TILE_URL,
    MAP_WIDTH,
)

try:  # pragma: no cover - optional import
    import mgrs  # type: ignore
except ImportError:  # pragma: no cover - optional import
    mgrs = None  # type: ignore

_DEFAULT_FONT = ImageFont.load_default()


@dataclass(slots=True)
class SnapshotEntry:
    observation_id: str
    lat: float
    lon: float
    timestamp: float
    priority: int
    tags: Set[str] = field(default_factory=set)


@dataclass(slots=True)
class DiffInfo:
    new_ids: Set[str] = field(default_factory=set)
    moved: Dict[str, Tuple[Tuple[float, float], Tuple[float, float]]] = field(default_factory=dict)
    stale: List[SnapshotEntry] = field(default_factory=list)


@dataclass(slots=True)
class MapObservation:
    observation_id: str
    chat_id: int
    lat: float
    lon: float
    timestamp: float
    text: str
    unit: Optional[str]
    observer: Optional[str]
    tags: Set[str]
    priority: int
    confidence: float
    accuracy_m: Optional[float]
    original_format: str
    what: Optional[str] = None
    amount: Optional[float] = None
    sources: Set[str] = field(default_factory=set)
    last_updated: float = field(default_factory=lambda: time.time())

    def signature(self) -> Tuple[str, Tuple[int, int]]:
        """Return a coarse signature for diffing (rounded location + priority tag)."""
        return (
            "|".join(sorted(self.tags)) or "unknown",
            (int(self.lat * 10000), int(self.lon * 10000)),
        )


@dataclass(slots=True)
class MapPreferences:
    """User map preferences (layers removed)."""
    focus_terms: List[str] = field(default_factory=list)


@dataclass(slots=True)
class MapRenderResult:
    image_bytes: bytes
    observation_count: int
    cluster_count: int
    focus_terms: List[str]
    callouts: List[str] = field(default_factory=list)
    diff: Optional[DiffInfo] = None


class MapRenderer:
    """Render clustered observations into a static PNG map."""

    def __init__(self, tile_url: str, width: int, height: int) -> None:
        self._tile_url = tile_url
        self._width = width
        self._height = height
        self._icon_cache: Dict[Tuple[str, int], bytes] = {}
        self._ring_cache: Dict[Tuple[str, int], bytes] = {}
        self._stale_icon: Optional[bytes] = None

    async def render(
        self,
        observations: Sequence[MapObservation],
        *,
        diff: Optional[DiffInfo] = None,
        stale_entries: Sequence[SnapshotEntry] = (),
    ) -> MapRenderResult:
        if not observations and not stale_entries:
            raise ValueError("No observations available for rendering.")

        clustered = cluster_observations(observations, MAP_CLUSTER_THRESHOLD_METERS)
        m = StaticMap(self._width, self._height, url_template=self._tile_url)
        cluster_count = len(clustered)

        diff_new = diff.new_ids if diff else set()
        diff_moved = diff.moved if diff else {}

        callouts: List[str] = []
        for index, cluster in enumerate(clustered, start=1):
            primary = cluster.primary

            style_color = priority_color(primary.priority)

            if diff and primary.observation_id in diff_new:
                style_color = "#34C759"  # new -> green
            elif diff and primary.observation_id in diff_moved:
                style_color = "#AF52DE"  # moved -> purple

            icon_bytes = self._build_icon(
                color=style_color,
                cluster_size=len(cluster.members),
                priority=primary.priority,
            )
            icon_bytes = self._annotate_icon_with_index(icon_bytes, index)
            marker = IconMarker((cluster.lon, cluster.lat), io.BytesIO(icon_bytes), 0, 0)
            m.add_marker(marker)

            accuracy = cluster.aggregated_accuracy()
            if accuracy:
                arc_bytes = self._build_accuracy_ring(style_color, accuracy)
                if arc_bytes is not None:
                    arc_marker = IconMarker((cluster.lon, cluster.lat), io.BytesIO(arc_bytes), 0, 0)
                    m.add_marker(arc_marker)

            callouts.append(self._build_callout(index, cluster))

        if diff:
            for stale in diff.stale:
                stale_bytes = self._build_stale_icon()
                marker = IconMarker((stale.lon, stale.lat), io.BytesIO(stale_bytes), 0, 0)
                m.add_marker(marker)

        image = await asyncio.to_thread(m.render)
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return MapRenderResult(
            image_bytes=buf.getvalue(),
            observation_count=len(observations),
            cluster_count=cluster_count,
            focus_terms=[],
            callouts=callouts,
            diff=diff,
        )

    def _build_icon(
        self,
        *,
        color: str,
        cluster_size: int,
        priority: int,
    ) -> bytes:
        key = (color, cluster_size)
        cached = self._icon_cache.get(key)
        if cached is not None:
            return cached

        size = 44 if cluster_size > 1 else 36
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        shadow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        icon_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        icon_draw = ImageDraw.Draw(icon_layer)

        rgba = hex_to_rgba(color, 1.0)
        outline = hex_to_rgba(color, 1.0)
        shadow_color = (0, 0, 0, 160)
        shadow_offset = 2

        pad = 6
        shape_bbox = [pad, pad, size - pad, size - pad]
        shadow_bbox = [
            shape_bbox[0] + shadow_offset,
            shape_bbox[1] + shadow_offset,
            shape_bbox[2] + shadow_offset,
            shape_bbox[3] + shadow_offset,
        ]
        shadow_draw.rectangle(shadow_bbox, fill=shadow_color)
        icon_draw.rectangle(shape_bbox, fill=rgba, outline=outline, width=3)

        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=3))
        canvas = Image.alpha_composite(canvas, shadow_layer)
        canvas = Image.alpha_composite(canvas, icon_layer)
        draw = ImageDraw.Draw(canvas)

        if cluster_size > 1:
            label = str(cluster_size)
            draw_text_center(draw, canvas.size, label)
        else:
            draw_text_center(draw, canvas.size, f"P{priority}", fill=(255, 255, 255, 255))

        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        data = buffer.getvalue()
        self._icon_cache[key] = data
        return data

    def _annotate_icon_with_index(self, icon_bytes: bytes, index: int) -> bytes:
        if index <= 0:
            return icon_bytes
        with Image.open(io.BytesIO(icon_bytes)) as base_icon:
            icon = base_icon.convert("RGBA")
        draw = ImageDraw.Draw(icon)
        bubble_radius = 12
        diameter = bubble_radius * 2
        padding = 4
        bubble_bbox = [
            padding,
            padding,
            padding + diameter,
            padding + diameter,
        ]
        draw.ellipse(bubble_bbox, fill=(0, 0, 0, 210))
        label = str(index)
        text_bbox = draw.textbbox((0, 0), label, font=_DEFAULT_FONT)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = padding + (diameter - text_width) / 2
        text_y = padding + (diameter - text_height) / 2
        draw.text((text_x, text_y), label, font=_DEFAULT_FONT, fill=(255, 255, 255, 255))
        buffer = io.BytesIO()
        icon.save(buffer, format="PNG")
        return buffer.getvalue()

    def _build_callout(self, index: int, cluster: "Cluster") -> str:
        primary = cluster.primary
        description_source = primary.what or primary.text or "Observation"
        description = self._sanitize_text(description_source)
        amount_value = self._aggregate_amount(cluster.members)
        if amount_value is None and primary.amount is not None:
            amount_value = float(primary.amount)
        amount_text = self._format_amount(amount_value)
        location_text = self._format_location(primary)

        parts: List[str] = [f"#{index}"]
        if amount_text:
            parts.append(amount_text)
        parts.append(description)
        callout = " ".join(parts)
        if location_text:
            callout += f" @ {location_text}"
        return callout

    def _aggregate_amount(self, members: Sequence[MapObservation]) -> Optional[float]:
        values = [obs.amount for obs in members if obs.amount is not None]
        if not values:
            return None
        return float(sum(values))

    def _format_amount(self, amount: Optional[float]) -> Optional[str]:
        if amount is None:
            return None
        if math.isclose(amount, round(amount)):
            return f"{int(round(amount))}×"
        return f"{amount:.1f}×"

    def _format_location(self, observation: MapObservation) -> str:
        if observation.original_format and observation.original_format != "latlon":
            return observation.original_format
        return f"{observation.lat:.4f},{observation.lon:.4f}"

    def _sanitize_text(self, text: str, limit: int = 80) -> str:
        clean = " ".join(text.split())
        if len(clean) <= limit:
            return clean
        return clean[: limit - 1] + "…"

    def _build_accuracy_ring(self, color: str, accuracy_m: float) -> Optional[bytes]:
        if accuracy_m <= 0:
            return None
        size = int(min(max(accuracy_m / MAP_CONFIDENCE_SCALE_METERS * 10, 20), 200))
        if size % 2 == 1:
            size += 1
        cache_key = (color, size)
        cached = self._ring_cache.get(cache_key)
        if cached is not None:
            return cached
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        rgba = hex_to_rgba(color, 0.25)
        draw.ellipse([2, 2, size - 2, size - 2], outline=rgba, width=4)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()
        self._ring_cache[cache_key] = data
        return data

    def _build_stale_icon(self) -> bytes:
        if self._stale_icon is not None:
            return self._stale_icon
        size = 36
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line([(6, 6), (size - 6, size - 6)], fill=(180, 180, 180, 255), width=5)
        draw.line([(6, size - 6), (size - 6, 6)], fill=(180, 180, 180, 255), width=5)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()
        self._stale_icon = data
        return data


@dataclass(slots=True)
class Cluster:
    members: List[MapObservation] = field(default_factory=list)

    @property
    def primary(self) -> MapObservation:
        return max(self.members, key=lambda obs: (priority_rank(obs.priority), obs.timestamp))

    @property
    def lat(self) -> float:
        return sum(obs.lat for obs in self.members) / len(self.members)

    @property
    def lon(self) -> float:
        return sum(obs.lon for obs in self.members) / len(self.members)

    def aggregated_accuracy(self) -> Optional[float]:
        accs = [obs.accuracy_m for obs in self.members if obs.accuracy_m]
        if not accs:
            return None
        return sum(accs) / len(accs)


def cluster_observations(observations: Sequence[MapObservation], threshold_m: float) -> List[Cluster]:
    clusters: List[Cluster] = []
    for obs in observations:
        placed = False
        for cluster in clusters:
            if haversine_distance(obs.lat, obs.lon, cluster.lat, cluster.lon) <= threshold_m:
                cluster.members.append(obs)
                placed = True
                break
        if not placed:
            clusters.append(Cluster(members=[obs]))
    return clusters


def priority_color(priority: int) -> str:
    return {
        1: "#FF3B30",
        2: "#FF9500",
        3: "#FFCC00",
        4: "#34C759",
    }.get(priority, "#5AC8F5")


def priority_rank(priority: int) -> int:
    return 5 - priority


def hex_to_rgba(color: str, alpha: float) -> Tuple[int, int, int, int]:
    color = color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    a = int(max(0, min(alpha, 1.0)) * 255)
    return (r, g, b, a)


def draw_text_center(
    draw: ImageDraw.ImageDraw,
    size: Tuple[int, int],
    text: str,
    *,
    fill=(0, 0, 0, 255),
) -> None:
    width, height = size
    text = text[:4]
    bbox = draw.textbbox((0, 0), text, font=_DEFAULT_FONT)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((width - tw) / 2, (height - th) / 2), text, fill=fill, font=_DEFAULT_FONT)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


class MapManager:
    """Manage observations and render tactical overview maps."""

    def __init__(self, logger) -> None:
        self._logger = logger.getChild("map")
        self._observations: Dict[int, Dict[str, MapObservation]] = {}
        self._source_index: Dict[int, Dict[str, str]] = {}
        self._preferences: Dict[int, MapPreferences] = {}
        self._last_snapshot: Dict[int, Dict[str, SnapshotEntry]] = {}
        self._live_jobs: Dict[int, object] = {}
        self._renderer = MapRenderer(MAP_TILE_URL, MAP_WIDTH, MAP_HEIGHT)
        self._lock = asyncio.Lock()

    async def add_observation(
        self,
        *,
        chat_id: int,
        source_id: str,
        lat: Optional[float],
        lon: Optional[float],
        text: str,
        what: Optional[str] = None,
        amount: Optional[float] = None,
        observed_at: datetime,
        unit: Optional[str],
        observer: Optional[str],
        confidence: Optional[float] = None,
        accuracy_m: Optional[float] = None,
        tags: Optional[Iterable[str]] = None,
        mgrs: Optional[str] = None,
    ) -> Optional[MapObservation]:
        if lat is None or lon is None:
            if mgrs:
                lat, lon = self._mgrs_to_latlon(mgrs)
            else:
                lat, lon = self._extract_coordinates(text)
        if lat is None or lon is None:
            return None

        ts = observed_at.astimezone(timezone.utc).timestamp()
        tags_set, priority = self._classify(text, tags)
        conf = confidence if confidence is not None else 70.0

        async with self._lock:
            obs = await self._upsert_observation(
                chat_id=chat_id,
                source_id=source_id,
                lat=lat,
                lon=lon,
                ts=ts,
                text=text,
                what=what,
                amount=amount,
                unit=unit,
                observer=observer,
                priority=priority,
                confidence=conf,
                accuracy_m=accuracy_m,
                tags=tags_set,
                mgrs=mgrs,
            )
        return obs

    async def _upsert_observation(
        self,
        *,
        chat_id: int,
        source_id: str,
        lat: float,
        lon: float,
        ts: float,
        text: str,
        what: Optional[str],
        amount: Optional[float],
        unit: Optional[str],
        observer: Optional[str],
        priority: int,
        confidence: float,
        accuracy_m: Optional[float],
        tags: Set[str],
        mgrs: Optional[str],
    ) -> MapObservation:
        chat_obs = self._observations.setdefault(chat_id, {})
        source_map = self._source_index.setdefault(chat_id, {})

        if source_id in source_map:
            obs_id = source_map[source_id]
            obs = chat_obs[obs_id]
            obs.lat = lat
            obs.lon = lon
            obs.timestamp = ts
            obs.text = text
            if what:
                obs.what = what
            else:
                obs.what = obs.what or text
            if amount is not None:
                obs.amount = float(amount)
            obs.sources.add(source_id)
            obs.priority = min(obs.priority, priority)
            obs.confidence = (obs.confidence + confidence) / 2
            obs.last_updated = time.time()
            if accuracy_m is not None:
                obs.accuracy_m = accuracy_m
            obs.tags.update(tags)
            return obs

        candidate = self._find_merge_candidate(chat_id, lat, lon, ts, tags)
        if candidate is not None:
            candidate.lat = (candidate.lat + lat) / 2
            candidate.lon = (candidate.lon + lon) / 2
            candidate.timestamp = max(candidate.timestamp, ts)
            candidate.sources.add(source_id)
            candidate.text = text
            if what:
                candidate.what = what
            elif not candidate.what:
                candidate.what = text
            if amount is not None:
                candidate.amount = float(amount)
            candidate.priority = min(candidate.priority, priority)
            candidate.confidence = (candidate.confidence + confidence) / 2
            candidate.accuracy_m = accuracy_m or candidate.accuracy_m
            candidate.tags.update(tags)
            candidate.last_updated = time.time()
            source_map[source_id] = candidate.observation_id
            return candidate

        obs_id = str(uuid.uuid4())
        new_obs = MapObservation(
            observation_id=obs_id,
            chat_id=chat_id,
            lat=lat,
            lon=lon,
            timestamp=ts,
            text=text,
            what=what or text,
            amount=float(amount) if amount is not None else None,
            unit=unit,
            observer=observer,
            tags=set(tags),
            priority=priority,
            confidence=confidence,
            accuracy_m=accuracy_m,
            original_format=mgrs or "latlon",
            sources={source_id},
            last_updated=time.time(),
        )
        chat_obs[obs_id] = new_obs
        source_map[source_id] = obs_id
        self._prune(chat_id)
        return new_obs

    def _prune(self, chat_id: int) -> None:
        chat_obs = self._observations.get(chat_id, {})
        if len(chat_obs) <= MAP_MAX_POINTS:
            return
        sorted_obs = sorted(chat_obs.values(), key=lambda o: o.timestamp)
        for obs in sorted_obs[: len(chat_obs) - MAP_MAX_POINTS]:
            chat_obs.pop(obs.observation_id, None)

    def _find_merge_candidate(
        self,
        chat_id: int,
        lat: float,
        lon: float,
        ts: float,
        tags: Set[str],
    ) -> Optional[MapObservation]:
        chat_obs = self._observations.get(chat_id)
        if not chat_obs:
            return None
        for obs in chat_obs.values():
            if not obs.tags.intersection(tags):
                continue
            if abs(obs.timestamp - ts) > MAP_LOOKBACK_MINUTES * 60:
                continue
            if haversine_distance(obs.lat, obs.lon, lat, lon) <= MAP_CLUSTER_THRESHOLD_METERS / 2:
                return obs
        return None

    async def render_snapshot(
        self,
        chat_id: int,
        *,
        diff: bool = False,
        focus_terms: Optional[Sequence[str]] = None,
        lookback_minutes: Optional[int] = None,
        update_baseline: bool = True,
    ) -> Optional[MapRenderResult]:
        lookback = (lookback_minutes or MAP_LOOKBACK_MINUTES) * 60
        prefs = self._preferences.setdefault(chat_id, MapPreferences())
        focus_terms = list(focus_terms) if focus_terms is not None else list(prefs.focus_terms)
        cutoff = time.time() - lookback

        async with self._lock:
            chat_obs = list(self._observations.get(chat_id, {}).values())

        filtered = [
            obs
            for obs in chat_obs
            if obs.timestamp >= cutoff and self._matches_focus(obs, focus_terms)
        ]

        diff_info = None
        stale_entries: List[SnapshotEntry] = []
        if diff:
            diff_info, stale_entries = self._calculate_diff(chat_id, filtered, cutoff)
            if not filtered and not diff_info.stale:
                return None
        elif not filtered:
            return None

        rendered = await self._renderer.render(filtered, diff=diff_info, stale_entries=stale_entries)
        rendered.focus_terms = focus_terms

        if update_baseline:
            self._update_snapshot_baseline(chat_id, filtered)
        return rendered

    async def set_focus(self, chat_id: int, terms: Sequence[str]) -> MapPreferences:
        prefs = self._preferences.setdefault(chat_id, MapPreferences())
        prefs.focus_terms = [term.lower() for term in terms if term]
        return prefs

    # set_layers removed – layers feature deprecated.

    async def clear_focus(self, chat_id: int) -> MapPreferences:
        prefs = self._preferences.setdefault(chat_id, MapPreferences())
        prefs.focus_terms.clear()
        return prefs

    def get_preferences(self, chat_id: int) -> MapPreferences:
        return self._preferences.setdefault(chat_id, MapPreferences())

    async def stop_live(self, chat_id: int, *, job_queue) -> bool:
        job = self._live_jobs.pop(chat_id, None)
        if not job:
            return False
        job.schedule_removal()
        return True

    async def start_live(self, chat_id: int, *, job_queue, interval: Optional[int] = None) -> bool:
        if chat_id in self._live_jobs:
            return False

        async def _callback(context):  # pragma: no cover - scheduled callback
            rendered = await self.render_snapshot(chat_id, update_baseline=True)
            if not rendered:
                return
            caption = self.build_caption(rendered)
            await context.bot.send_photo(chat_id=chat_id, photo=rendered.image_bytes, caption=caption)

        job = job_queue.run_repeating(
            _callback,
            interval=interval or MAP_LIVE_INTERVAL_SECONDS,
            first=0,
            name=f"map-live-{chat_id}",
        )
        self._live_jobs[chat_id] = job
        return True

    def build_caption(self, result: MapRenderResult) -> str:
        header_parts = [f"Observations: {result.observation_count}"]
        if result.focus_terms:
            header_parts.append(f"Focus: {' '.join(result.focus_terms)}")
        if result.diff:
            diff = result.diff
            header_parts.append(
                f"Δ new {len(diff.new_ids)} | moved {len(diff.moved)} | stale {len(diff.stale)}"
            )


        header = " | ".join(header_parts)
        if not result.callouts:
            return header

        lines = [header, ""]
        max_lines = 8
        for callout in result.callouts[:max_lines]:
            lines.append(callout)
        remaining = len(result.callouts) - max_lines
        if remaining > 0:
            lines.append(f"… +{remaining} more")
        return "\n".join(lines)

    def _calculate_diff(
        self,
        chat_id: int,
        current: Sequence[MapObservation],
        cutoff: float,
    ) -> Tuple[DiffInfo, List[SnapshotEntry]]:
        diff = DiffInfo()
        stale_entries: List[SnapshotEntry] = []
        previous = self._last_snapshot.get(chat_id, {})
        current_ids = {obs.observation_id for obs in current}

        for obs in current:
            prev = previous.get(obs.observation_id)
            if prev is None:
                diff.new_ids.add(obs.observation_id)
            else:
                if haversine_distance(obs.lat, obs.lon, prev.lat, prev.lon) > MAP_CLUSTER_THRESHOLD_METERS / 4:
                    diff.moved[obs.observation_id] = ((prev.lat, prev.lon), (obs.lat, obs.lon))

        for obs_id, entry in previous.items():
            if obs_id not in current_ids and entry.timestamp >= cutoff:
                stale_entries.append(entry)
                diff.stale.append(entry)

        return diff, stale_entries

    def _update_snapshot_baseline(self, chat_id: int, observations: Sequence[MapObservation]) -> None:
        snapshot = {}
        for obs in observations:
            snapshot[obs.observation_id] = SnapshotEntry(
                observation_id=obs.observation_id,
                lat=obs.lat,
                lon=obs.lon,
                timestamp=obs.timestamp,
                priority=obs.priority,
                tags=set(obs.tags),
            )
        self._last_snapshot[chat_id] = snapshot

    def _matches_focus(self, obs: MapObservation, focus_terms: Sequence[str]) -> bool:
        if not focus_terms:
            return True
        haystack = " ".join(filter(None, [obs.text, obs.unit or "", obs.observer or ""])).lower()
        haystack_tags = " ".join(sorted(obs.tags))
        for term in focus_terms:
            normalized = term.lower()
            if normalized.startswith("p") and len(normalized) == 2 and normalized[1].isdigit():
                if int(normalized[1]) == obs.priority:
                    return True
            if normalized in haystack or normalized in haystack_tags:
                return True
        return False

    # _matches_layers removed – layer filtering deprecated.

    def _classify(self, text: str, tags: Optional[Iterable[str]]) -> Tuple[Set[str], int]:
        base_tags = set(tag.lower() for tag in tags) if tags else set()
        text_lower = text.lower()
        priority = 4
        if "enemy" in base_tags:
            priority = 2
        elif "logistics" in base_tags:
            priority = min(priority, 3)
        elif "terrain" in base_tags:
            priority = 4
        elif "friendly" in base_tags:
            priority = min(priority, 3)
        return base_tags or {"unclassified"}, priority

    def _mgrs_to_latlon(self, mgrs_str: str) -> Tuple[Optional[float], Optional[float]]:
        if not mgrs or not mgrs_str:
            return (None, None)
        try:
            lat, lon = mgrs.MGRS().toLatLon(mgrs_str)
            return (lat, lon)
        except Exception:
            self._logger.debug("Failed to convert MGRS '%s' to coordinates", mgrs_str)
            return (None, None)

    def _extract_coordinates(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        if not text:
            return (None, None)
        tokens = text.replace(",", " ").split()
        lat = lon = None
        for token in tokens:
            if token.count(".") == 1 and any(c.isdigit() for c in token):
                try:
                    value = float(token)
                except ValueError:
                    continue
                if -90 <= value <= 90 and lat is None:
                    lat = value
                elif -180 <= value <= 180 and lon is None:
                    lon = value
        if lat is not None and lon is not None:
            return (lat, lon)
        if mgrs:
            for token in tokens:
                if len(token) >= 5 and token[:2].isalpha():
                    latlon = self._mgrs_to_latlon(token)
                    if latlon != (None, None):
                        return latlon
        return (None, None)

__all__ = ["MapManager", "MapRenderResult", "MapObservation", "MapPreferences"]
