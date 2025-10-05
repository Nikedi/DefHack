import { useMemo } from "react";
import type { SensorObservation } from "../api";

type TreeEntry = {
  sensors: Map<string, number>;
  humans: Map<string, number>;
};

const DEFAULT_UNIT = "Unassigned Unit";
const HUMAN_BRANCH = "Human Observer";

function normaliseLabel(value: string | null | undefined, fallback: string): string {
  const label = value?.trim();
  return label && label.length > 0 ? label : fallback;
}

export default function SensorTree({ observations }: { observations: SensorObservation[] }) {
  const units = useMemo(() => {
    const map = new Map<string, TreeEntry>();

    for (const obs of observations) {
      const unitName = normaliseLabel(obs.unit, DEFAULT_UNIT);
      const store = map.get(unitName) ?? { sensors: new Map(), humans: new Map() };

      const observerSignatureRaw = obs.observer_signature?.trim() || null;
      const fallbackSource = observerSignatureRaw || obs.sensor_id || "Unknown Source";
      const normalizedLabel = normaliseLabel(observerSignatureRaw, fallbackSource);
      const isSensor = observerSignatureRaw?.toLowerCase().includes("sensor") ?? false;

      if (isSensor) {
        store.sensors.set(normalizedLabel, (store.sensors.get(normalizedLabel) ?? 0) + 1);
      } else {
        store.humans.set(normalizedLabel, (store.humans.get(normalizedLabel) ?? 0) + 1);
      }

      map.set(unitName, store);
    }

    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [observations]);

  if (!units.length) {
    return <div className="mil-sensor-tree__empty">No sensor activity recorded.</div>;
  }

  return (
    <div className="mil-sensor-tree" role="tree">
      <ul className="mil-sensor-tree__units">
        {units.map(([unitName, entry]) => {
          const unitTotal = entry.sensors.size + entry.humans.size;
          return (
            <li key={unitName} className="mil-sensor-tree__unit" role="treeitem" aria-expanded>
              <div className="mil-sensor-tree__branch">
                <span className="mil-sensor-tree__label">{unitName}</span>
                <span className="mil-sensor-tree__badge" title="Distinct sources">
                  {unitTotal}
                </span>
              </div>
              <ul className="mil-sensor-tree__children" role="group">
                {entry.sensors.size > 0 && (
                  <li className="mil-sensor-tree__category" role="treeitem" aria-expanded>
                    <div className="mil-sensor-tree__branch">
                      <span className="mil-sensor-tree__label">Sensors</span>
                      <span className="mil-sensor-tree__badge">{entry.sensors.size}</span>
                    </div>
                    <ul className="mil-sensor-tree__leaves" role="group">
                      {Array.from(entry.sensors.entries())
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([name, count]) => (
                          <li key={name} className="mil-sensor-tree__leaf" role="treeitem">
                            <span className="mil-sensor-tree__dot" aria-hidden="true" />
                            <span className="mil-sensor-tree__label" title={name}>{name}</span>
                            <span className="mil-sensor-tree__badge" title="Observation count">{count}</span>
                          </li>
                        ))}
                    </ul>
                  </li>
                )}
                {entry.humans.size > 0 && (
                  <li className="mil-sensor-tree__category" role="treeitem" aria-expanded>
                    <div className="mil-sensor-tree__branch">
                      <span className="mil-sensor-tree__label">{HUMAN_BRANCH}</span>
                      <span className="mil-sensor-tree__badge">{entry.humans.size}</span>
                    </div>
                    <ul className="mil-sensor-tree__leaves" role="group">
                      {Array.from(entry.humans.entries())
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([name, count]) => (
                          <li key={name} className="mil-sensor-tree__leaf" role="treeitem">
                            <span className="mil-sensor-tree__dot mil-sensor-tree__dot--human" aria-hidden="true" />
                            <span className="mil-sensor-tree__label" title={name}>{name}</span>
                            <span className="mil-sensor-tree__badge" title="Observation count">{count}</span>
                          </li>
                        ))}
                    </ul>
                  </li>
                )}
              </ul>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
