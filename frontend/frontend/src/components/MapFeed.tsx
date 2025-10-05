import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MapContainer, Marker, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import type { SensorObservation } from "../api";
import * as mgrs from "mgrs";
import { DivIcon, latLngBounds } from "leaflet";
import type { LatLngTuple } from "leaflet";
import {
  deriveConfidenceTier,
  deriveObservationType,
  formatConfidence,
  formatObservationTypeLabel,
  type ConfidenceTier,
  type MapIntelStats,
  type ObservationType
} from "../utils/mapIntel";

interface MapFeedProps {
  observations: SensorObservation[];
  onStatsChange?: (stats: MapIntelStats) => void;
}

interface FeaturePoint {
  key: string;
  position: LatLngTuple;
  label: string;
  confidence: number | null;
  mgrs?: string | null;
  tier: ConfidenceTier;
  classification: ObservationType;
  tone: MarkerTone;
}

const DEFAULT_CENTER: LatLngTuple = [0, 0];

const MARKER_SIZE: [number, number] = [34, 34];
const MARKER_ANCHOR: [number, number] = [17, 17];
const TOOLTIP_ANCHOR: [number, number] = [18, 0];

type MarkerTone = "support" | "hostile";

const NATO_GLYPHS: Record<ObservationType, string> = {
  armor: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="10" width="20" height="12" rx="2.5" ry="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="22" r="2" fill="currentColor"/><circle cx="20" cy="22" r="2" fill="currentColor"/></svg>',
  vehicle: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="12" width="20" height="8" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 12v-2h8l3 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="22" r="2" fill="currentColor"/><circle cx="22" cy="22" r="2" fill="currentColor"/></svg>',
  infantry: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M10 8l12 16M22 8l-12 16" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="16" cy="10" r="3" fill="currentColor"/></svg>',
  air: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 6l6 10h-4l3 10-5-4-5 4 3-10h-4z" fill="currentColor"/></svg>',
  artillery: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="8" y="14" width="16" height="6" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 14l12-6M12 20l-2 6M20 20l2 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  unknown: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 8a6 6 0 0 1 6 6c0 2.5-1.5 3.9-3 5-1 0.7-1.5 1.3-1.5 2.4v1.6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="16" cy="24.5" r="1.6" fill="currentColor"/></svg>'
};

function deriveTone(label: string | null | undefined): MarkerTone {
  if (!label) return "hostile";
  return /logistic|support/i.test(label) ? "support" : "hostile";
}

function createNatoIconHtml(classification: ObservationType, tier: ConfidenceTier, tone: MarkerTone): string {
  const glyph = NATO_GLYPHS[classification] ?? NATO_GLYPHS.unknown;
  return `
    <div class="mil-nato-marker mil-nato-marker--${classification} mil-nato-marker--tier-${tier} mil-nato-marker--tone-${tone}">
      <div class="mil-nato-marker__frame">
        <span class="mil-nato-marker__glyph mil-nato-marker__glyph--${classification}">${glyph}</span>
      </div>
    </div>
  `;
}

const FitToPoints = ({ positions, shouldFit }: { positions: LatLngTuple[]; shouldFit: boolean }) => {
  const map = useMap();
  const previousCount = useRef(0);

  useEffect(() => {
    if (!positions.length) {
      previousCount.current = 0;
      return;
    }

    previousCount.current = positions.length;
    if (!shouldFit) return;

    if (!positions.length) return;
    const bounds = latLngBounds(positions);
    if (!bounds.isValid()) return;
    map.fitBounds(bounds, { padding: [24, 24], maxZoom: 13, animate: false });
  }, [map, positions, shouldFit]);

  return null;
};

const MapInteractionGuard = ({ onInteract }: { onInteract: () => void }) => {
  useMapEvents({
    dragstart: onInteract,
    zoomstart: onInteract,
    movestart: onInteract
  });
  return null;
};

function sanitizeMgrs(value: string | null | undefined): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.toUpperCase();
}

function mgrsToLatLng(value: string): LatLngTuple | null {
  try {
    const [lon, lat] = mgrs.toPoint(value);
    if (Number.isNaN(lat) || Number.isNaN(lon)) return null;
    return [lat, lon];
  } catch {
    return null;
  }
}

const MapFeed = ({ observations, onStatsChange }: MapFeedProps) => {
  const [hasUserInteraction, setHasUserInteraction] = useState(false);
  const [expandedMarkers, setExpandedMarkers] = useState<Record<string, boolean>>({});
  const iconCache = useRef<Record<string, DivIcon>>({});

  const getIconForMarker = useCallback((tier: ConfidenceTier, classification: ObservationType, tone: MarkerTone) => {
    const cacheKey = `${classification}::${tier}::${tone}`;
    if (!iconCache.current[cacheKey]) {
      iconCache.current[cacheKey] = new DivIcon({
        className: "mil-nato-icon",
        html: createNatoIconHtml(classification, tier, tone),
        iconSize: MARKER_SIZE,
        iconAnchor: MARKER_ANCHOR,
        tooltipAnchor: TOOLTIP_ANCHOR
      });
    }
    return iconCache.current[cacheKey];
  }, []);

  const features = useMemo<FeaturePoint[]>(() => {
    return observations
      .map<FeaturePoint | null>((obs, idx) => {
        const normalized = sanitizeMgrs(obs.mgrs);
        if (!normalized) return null;
        const coords = mgrsToLatLng(normalized);
        if (!coords) return null;
        const confidenceValue = typeof obs.confidence === "number" ? obs.confidence : null;
        const tier = deriveConfidenceTier(confidenceValue);
        const classification = deriveObservationType(obs.what);
        const tone = deriveTone(obs.what);
        return {
          key: `${obs.id ?? obs.time ?? idx}-${normalized}`,
          position: coords,
          label: obs.what?.trim() || "Observation",
          confidence: confidenceValue,
          mgrs: normalized,
          tier,
          classification,
          tone
        };
      })
      .filter((entry): entry is FeaturePoint => Boolean(entry));
  }, [observations]);

  const positions = useMemo(() => features.map((f) => f.position), [features]);
  const center = features[0]?.position ?? DEFAULT_CENTER;
  const previousCountRef = useRef(0);

  useEffect(() => {
    setExpandedMarkers((prev) => {
      const next: Record<string, boolean> = {};
      for (const feature of features) {
        const existing = prev[feature.key];
        next[feature.key] = typeof existing === "boolean" ? existing : true;
      }
      return next;
    });
  }, [features]);

  const stats = useMemo<MapIntelStats>(() => {
    if (!features.length) {
      return {
        total: 0,
        avgConfidence: null as number | null,
        tierCounts: { high: 0, medium: 0, low: 0, unknown: 0 } as Record<ConfidenceTier, number>,
        typeCounts: {
          armor: 0,
          vehicle: 0,
          infantry: 0,
          air: 0,
          artillery: 0,
          unknown: 0
        } as Record<ObservationType, number>,
        topSignals: [] as Array<{ label: string; count: number }>
      };
    }

    const tierCounts: Record<ConfidenceTier, number> = { high: 0, medium: 0, low: 0, unknown: 0 };
    const typeCounts: Record<ObservationType, number> = {
      armor: 0,
      vehicle: 0,
      infantry: 0,
      air: 0,
      artillery: 0,
      unknown: 0
    };
    let confidenceSum = 0;
    let confidenceSamples = 0;
    const signalCounts = new Map<string, number>();

    for (const feature of features) {
      tierCounts[feature.tier] = (tierCounts[feature.tier] ?? 0) + 1;
      typeCounts[feature.classification] = (typeCounts[feature.classification] ?? 0) + 1;
      if (feature.confidence != null && !Number.isNaN(feature.confidence)) {
        confidenceSum += feature.confidence > 1 ? feature.confidence : feature.confidence * 100;
        confidenceSamples += 1;
      }
      if (feature.label) {
        signalCounts.set(feature.label, (signalCounts.get(feature.label) ?? 0) + 1);
      }
    }

    const topSignals = Array.from(signalCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([label, count]) => ({ label, count }));

    const avgConfidence = confidenceSamples ? confidenceSum / confidenceSamples : null;

    return { total: features.length, avgConfidence, tierCounts, typeCounts, topSignals };
  }, [features]);

  useEffect(() => {
    onStatsChange?.(stats);
  }, [stats, onStatsChange]);

  useEffect(() => {
    const previousCount = previousCountRef.current;
    if ((previousCount === 0 && features.length > 0) || features.length === 0) {
      setHasUserInteraction(false);
    }
    previousCountRef.current = features.length;
  }, [features.length]);

  const handleUserInteraction = useCallback(() => {
    setHasUserInteraction((prev) => (prev ? prev : true));
  }, []);

  const toggleMarker = useCallback((key: string) => {
    setExpandedMarkers((prev) => {
      const next = { ...prev, [key]: !(prev[key] ?? false) };
      return next;
    });
  }, []);

  const toggleAllMarkers = useCallback(() => {
    setExpandedMarkers((prev) => {
      const shouldExpand = !features.every((feature) => prev[feature.key]);
      const next: Record<string, boolean> = {};
      for (const feature of features) {
        next[feature.key] = shouldExpand;
      }
      return next;
    });
  }, [features]);

  const areAllExpanded = useMemo(() => {
    if (!features.length) return true;
    return features.every((feature) => expandedMarkers[feature.key]);
  }, [expandedMarkers, features]);

  return (
    <div className="mil-map-large">
      <div className="mil-map-controls">
        <button
          type="button"
          className="btn-mil mil-map-controls__toggle"
          onClick={toggleAllMarkers}
          disabled={!features.length}
        >
          {areAllExpanded ? "Collapse All" : "Expand All"}
        </button>
      </div>
      <MapContainer
        center={center}
        minZoom={2}
        zoom={5}
        maxZoom={18}
        className="mil-map-canvas"
        scrollWheelZoom
        preferCanvas
      >
        <TileLayer
          url="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"
          attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors, &copy; <a href='https://stadiamaps.com/'>Stadia Maps</a>"
          className="mil-map-tiles"
        />
        <MapInteractionGuard onInteract={handleUserInteraction} />
        <FitToPoints positions={positions} shouldFit={!hasUserInteraction} />
        {features.map((feature) => {
          const expanded = expandedMarkers[feature.key] ?? false;
          return (
            <Marker
              key={feature.key}
              position={feature.position}
              icon={getIconForMarker(feature.tier, feature.classification, feature.tone)}
              eventHandlers={{
                click: () => toggleMarker(feature.key)
              }}
            >
              {expanded ? (
                <Tooltip
                  permanent
                  direction="right"
                  offset={[14, 0]}
                  className="mil-map-label"
                  interactive
                >
                  <div
                    className="mil-map-tooltip"
                    onClick={(event) => {
                      event.stopPropagation();
                      event.preventDefault();
                      toggleMarker(feature.key);
                    }}
                  >
                    <div className="mil-map-tooltip__title">{feature.label}</div>
                    <div className="mil-map-tooltip__meta">
                      <span className={`mil-map-badge mil-map-badge--${feature.tier}`}>
                        Confidence {formatConfidence(feature.confidence)}
                      </span>
                      {feature.classification && feature.classification !== "unknown" && (
                        <span className={`mil-map-tooltip__type mil-map-tooltip__type--${feature.classification}`}>
                          {formatObservationTypeLabel(feature.classification)}
                        </span>
                      )}
                      {feature.mgrs && <span className="mil-map-tooltip__mgrs">{feature.mgrs}</span>}
                    </div>
                  </div>
                </Tooltip>
              ) : null}
            </Marker>
          );
        })}
      </MapContainer>
      {!features.length && (
        <div className="mil-map-empty">No observations with MGRS coordinates yet.</div>
      )}
      <div className="mil-map-overlay" aria-hidden="true" />
    </div>
  );
};

export default MapFeed;
