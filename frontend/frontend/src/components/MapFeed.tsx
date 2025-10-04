import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MapContainer, Marker, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import type { SensorObservation } from "../api";
import * as mgrs from "mgrs";
import { DivIcon, latLngBounds } from "leaflet";
import type { LatLngTuple } from "leaflet";

interface MapFeedProps {
  observations: SensorObservation[];
}

interface FeaturePoint {
  key: string;
  position: LatLngTuple;
  label: string;
  confidence: number | null;
  mgrs?: string | null;
  tier: ConfidenceTier;
  classification: ObservationType;
}

const DEFAULT_CENTER: LatLngTuple = [0, 0];

type ConfidenceTier = "low" | "medium" | "high" | "unknown";
type ObservationType = "armor" | "vehicle" | "infantry" | "air" | "artillery" | "unknown";

const MARKER_SIZE: [number, number] = [34, 34];
const MARKER_ANCHOR: [number, number] = [17, 17];
const TOOLTIP_ANCHOR: [number, number] = [18, 0];
const TYPE_ORDER: ObservationType[] = ["armor", "vehicle", "infantry", "artillery", "air", "unknown"];

function deriveConfidenceTier(confidence: number | null): ConfidenceTier {
  if (confidence == null || Number.isNaN(confidence)) return "unknown";
  if (confidence >= 80) return "high";
  if (confidence >= 50) return "medium";
  return "low";
}

function formatConfidence(confidence: number | null): string {
  if (confidence == null || Number.isNaN(confidence)) return "—";
  const value = confidence > 1 ? confidence : confidence * 100;
  return `${Math.round(value)}%`;
}

const OBSERVATION_KEYWORDS: Array<{ type: ObservationType; patterns: RegExp[] }> = [
  { type: "armor", patterns: [/\btank(s)?\b/i, /\bmbt\b/i, /armou?red?/i, /afv/i, /apc/i, /abrams/i, /t[-\s]?\d+/i] },
  { type: "vehicle", patterns: [/\bconvoy\b/i, /\bvehicle(s)?\b/i, /truck(s)?/i, /logistic(s)?/i, /jeep/i, /transport/i] },
  { type: "infantry", patterns: [/infantry/i, /soldier(s)?/i, /troop(s)?/i, /platoon/i, /squad/i, /foot (unit|patrol)/i, /sniper/i, /combatant(s)?/i] },
  { type: "air", patterns: [/helicopter/i, /helo/i, /uav/i, /drone/i, /aircraft/i, /jet/i, /fighter/i] },
  { type: "artillery", patterns: [/artillery/i, /howitzer/i, /mortar/i, /rocket battery/i, /mlrs/i] }
];

function deriveObservationType(label: string | null | undefined): ObservationType {
  if (!label) return "unknown";
  const text = label.toLowerCase();
  for (const entry of OBSERVATION_KEYWORDS) {
    if (entry.patterns.some((pattern) => pattern.test(text))) {
      return entry.type;
    }
  }
  return "unknown";
}

function formatObservationTypeLabel(type: ObservationType): string {
  if (type === "unknown") return "Other";
  return type.replace(/(^.|\s.)/g, (segment) => segment.toUpperCase());
}

function formatConfidenceTierLabel(tier: ConfidenceTier): string {
  if (tier === "unknown") return "Unknown";
  return tier.charAt(0).toUpperCase() + tier.slice(1);
}

const NATO_GLYPHS: Record<ObservationType, string> = {
  armor: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="10" width="20" height="12" rx="2.5" ry="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="22" r="2" fill="currentColor"/><circle cx="20" cy="22" r="2" fill="currentColor"/></svg>',
  vehicle: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="12" width="20" height="8" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 12v-2h8l3 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="22" r="2" fill="currentColor"/><circle cx="22" cy="22" r="2" fill="currentColor"/></svg>',
  infantry: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M10 8l12 16M22 8l-12 16" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="16" cy="10" r="3" fill="currentColor"/></svg>',
  air: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 6l6 10h-4l3 10-5-4-5 4 3-10h-4z" fill="currentColor"/></svg>',
  artillery: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><rect x="8" y="14" width="16" height="6" rx="2" ry="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 14l12-6M12 20l-2 6M20 20l2 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  unknown: '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 8a6 6 0 0 1 6 6c0 2.5-1.5 3.9-3 5-1 0.7-1.5 1.3-1.5 2.4v1.6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="16" cy="24.5" r="1.6" fill="currentColor"/></svg>'
};

function createNatoIconHtml(classification: ObservationType, tier: ConfidenceTier): string {
  const glyph = NATO_GLYPHS[classification] ?? NATO_GLYPHS.unknown;
  return `
    <div class="mil-nato-marker mil-nato-marker--${classification} mil-nato-marker--tier-${tier}">
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

const MapFeed = ({ observations }: MapFeedProps) => {
  const [hasUserInteraction, setHasUserInteraction] = useState(false);
  const [expandedMarkers, setExpandedMarkers] = useState<Record<string, boolean>>({});
  const iconCache = useRef<Record<string, DivIcon>>({});

  const getIconForMarker = useCallback((tier: ConfidenceTier, classification: ObservationType) => {
    const cacheKey = `${classification}::${tier}`;
    if (!iconCache.current[cacheKey]) {
      iconCache.current[cacheKey] = new DivIcon({
        className: "mil-nato-icon",
        html: createNatoIconHtml(classification, tier),
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
        return {
          key: `${obs.id ?? obs.time ?? idx}-${normalized}`,
          position: coords,
          label: obs.what?.trim() || "Observation",
          confidence: confidenceValue,
          mgrs: normalized,
          tier,
          classification
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

  const stats = useMemo(() => {
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

  const tierEntries = useMemo(() => {
    const ordered: ConfidenceTier[] = ["high", "medium", "low", "unknown"];
    return ordered.filter((tier) => stats.tierCounts[tier] > 0);
  }, [stats]);

  const typeEntries = useMemo(() => TYPE_ORDER.filter((type) => stats.typeCounts[type] > 0), [stats]);

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
    setExpandedMarkers((prev) => ({
      ...prev,
      [key]: !(prev[key] ?? false)
    }));
  }, []);

  return (
    <div className="mil-map-large">
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
              icon={getIconForMarker(feature.tier, feature.classification)}
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
              ) : (
                <Tooltip
                  permanent
                  direction="right"
                  offset={[10, 0]}
                  className="mil-map-label mil-map-label--collapsed"
                  interactive
                >
                  <button
                    type="button"
                    className="mil-map-tooltip-collapsed"
                    onClick={(event) => {
                      event.stopPropagation();
                      event.preventDefault();
                      toggleMarker(feature.key);
                    }}
                  >
                    Expand
                  </button>
                </Tooltip>
              )}
            </Marker>
          );
        })}
      </MapContainer>
      {!features.length && (
        <div className="mil-map-empty">No observations with MGRS coordinates yet.</div>
      )}
      {features.length > 0 && (
        <div className="mil-map-intel" role="status" aria-live="polite">
          <div className="mil-map-intel__grid">
            <div className="mil-map-intel__stat">
              <span className="mil-map-intel__label">Observations</span>
              <span className="mil-map-intel__value">{stats.total}</span>
            </div>
            <div className="mil-map-intel__stat">
              <span className="mil-map-intel__label">Avg Conf.</span>
              <span className="mil-map-intel__value">{stats.avgConfidence != null ? `${Math.round(stats.avgConfidence)}%` : "—"}</span>
            </div>
            {tierEntries.length > 0 && (
              <div className="mil-map-intel__legend">
                {tierEntries.map((tier) => (
                  <span key={tier} className={`mil-map-legend-chip mil-map-legend-chip--${tier}`}>
                    {formatConfidenceTierLabel(tier)} · {stats.tierCounts[tier]}
                  </span>
                ))}
              </div>
            )}
            {typeEntries.length > 0 && (
              <div className="mil-map-intel__types">
                {typeEntries.map((type) => (
                  <span key={type} className={`mil-map-type-chip mil-map-type-chip--${type}`}>
                    <span className="mil-map-type-chip__icon" aria-hidden="true" />
                    <span className="mil-map-type-chip__label">{formatObservationTypeLabel(type)}</span>
                    <span className="mil-map-type-chip__count">{stats.typeCounts[type]}</span>
                  </span>
                ))}
              </div>
            )}
            {stats.topSignals.length > 0 && (
              <div className="mil-map-intel__signals">
                <span className="mil-map-intel__label">Top Signals</span>
                <div className="mil-map-intel__signals-wrap">
                  {stats.topSignals.map((signal) => (
                    <span key={signal.label} className="mil-map-intel__signal">
                      <span className="mil-map-intel__signal-label">{signal.label}</span>
                      <span className="mil-map-intel__signal-count">{signal.count}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      <div className="mil-map-overlay" aria-hidden="true" />
    </div>
  );
};

export default MapFeed;
