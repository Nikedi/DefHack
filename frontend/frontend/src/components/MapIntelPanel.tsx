import { memo, useMemo } from "react";
import {
  CONFIDENCE_TIERS,
  OBSERVATION_TYPES_IN_ORDER,
  formatConfidenceTierLabel,
  formatObservationTypeLabel,
  type MapIntelStats
} from "../utils/mapIntel";

interface MapIntelPanelProps {
  stats: MapIntelStats | null;
}

const MapIntelPanel = ({ stats }: MapIntelPanelProps) => {
  const tierEntries = useMemo(() => {
    if (!stats) return [];
    return CONFIDENCE_TIERS.filter((tier) => (stats.tierCounts[tier] ?? 0) > 0);
  }, [stats]);

  const typeEntries = useMemo(() => {
    if (!stats) return [];
    return OBSERVATION_TYPES_IN_ORDER.filter((type) => (stats.typeCounts[type] ?? 0) > 0);
  }, [stats]);

  const hasTierData = tierEntries.length > 0;
  const hasTypeData = typeEntries.length > 0;

  const content = (() => {
    if (!stats) {
      return <div className="mil-map-intel-panel__empty">Waiting for map data…</div>;
    }

    if (stats.total === 0) {
      return <div className="mil-map-intel-panel__empty">No geolocated observations available yet.</div>;
    }

    return (
      <div className="mil-map-intel-panel__content">
        <div className="mil-map-intel-panel__metrics">
          <div className="mil-map-intel-panel__metric">
            <span className="mil-map-intel-panel__metric-label">Observations</span>
            <span className="mil-map-intel-panel__metric-value">{stats.total}</span>
          </div>
            <div className="mil-map-intel-panel__metric">
            <span className="mil-map-intel-panel__metric-label">Average Confidence</span>
            <span className="mil-map-intel-panel__metric-value">
              {stats.avgConfidence != null ? `${Math.round(stats.avgConfidence)}%` : "—"}
            </span>
          </div>
        </div>

        {(hasTierData || hasTypeData) && (
          <div
            className={`mil-map-intel-panel__sections ${
              hasTierData && hasTypeData ? "mil-map-intel-panel__sections--dual" : ""
            }`}
          >
            {hasTierData && (
              <section className="mil-map-intel-panel__section">
                <h3 className="mil-map-intel-panel__section-title">Confidence Tiers</h3>
                <div className="mil-map-intel-panel__chip-row">
                  {tierEntries.map((tier) => (
                    <span key={tier} className={`mil-map-legend-chip mil-map-legend-chip--${tier}`}>
                      {formatConfidenceTierLabel(tier)} · {stats.tierCounts[tier]}
                    </span>
                  ))}
                </div>
              </section>
            )}
            {hasTypeData && (
              <section className="mil-map-intel-panel__section">
                <h3 className="mil-map-intel-panel__section-title">Unit Types</h3>
                <div className="mil-map-intel-panel__chip-row">
                  {typeEntries.map((type) => (
                    <span key={type} className={`mil-map-type-chip mil-map-type-chip--${type}`}>
                      <span className="mil-map-type-chip__icon" aria-hidden="true" />
                      <span className="mil-map-type-chip__label">{formatObservationTypeLabel(type)}</span>
                      <span className="mil-map-type-chip__count">{stats.typeCounts[type]}</span>
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}

        {stats.topSignals.length > 0 && (
          <section>
            <h3 className="mil-map-intel-panel__section-title">Top Signals</h3>
            <div className="mil-map-intel-panel__signals">
              {stats.topSignals.map((signal) => (
                <div key={signal.label} className="mil-map-intel-panel__signal">
                  <span className="mil-map-intel-panel__signal-label">{signal.label}</span>
                  <span className="mil-map-intel-panel__signal-count">{signal.count}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    );
  })();

  return (
    <div className="mil-panel mil-map-intel-panel">
      <div className="mil-map-intel-panel__header">Map Intel Summary</div>
      {content}
    </div>
  );
};

export default memo(MapIntelPanel);
