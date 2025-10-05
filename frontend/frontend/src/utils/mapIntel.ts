export type ConfidenceTier = "low" | "medium" | "high" | "unknown";
export type ObservationType = "armor" | "vehicle" | "infantry" | "air" | "artillery" | "unknown";

export const CONFIDENCE_TIERS: ConfidenceTier[] = ["high", "medium", "low", "unknown"];
export const OBSERVATION_TYPES_IN_ORDER: ObservationType[] = [
  "armor",
  "vehicle",
  "infantry",
  "artillery",
  "air",
  "unknown"
];

const OBSERVATION_KEYWORDS: Array<{ type: ObservationType; patterns: RegExp[] }> = [
  { type: "armor", patterns: [/\btank(s)?\b/i, /\bmbt\b/i, /armou?red?/i, /afv/i, /apc/i, /abrams/i, /t[-\s]?\d+/i] },
  { type: "vehicle", patterns: [/\bconvoy\b/i, /\bvehicle(s)?\b/i, /truck(s)?/i, /logistic(s)?/i, /jeep/i, /transport/i] },
  {
    type: "infantry",
    patterns: [/infantry/i, /soldier(s)?/i, /troop(s)?/i, /platoon/i, /squad/i, /foot (unit|patrol)/i, /sniper/i, /combatant(s)?/i]
  },
  { type: "air", patterns: [/helicopter/i, /helo/i, /uav/i, /drone/i, /aircraft/i, /jet/i, /fighter/i] },
  { type: "artillery", patterns: [/artillery/i, /howitzer/i, /mortar/i, /rocket battery/i, /mlrs/i] }
];

export interface MapIntelStats {
  total: number;
  avgConfidence: number | null;
  tierCounts: Record<ConfidenceTier, number>;
  typeCounts: Record<ObservationType, number>;
  topSignals: Array<{ label: string; count: number }>;
}

export function deriveConfidenceTier(confidence: number | null): ConfidenceTier {
  if (confidence == null || Number.isNaN(confidence)) return "unknown";
  if (confidence >= 80) return "high";
  if (confidence >= 50) return "medium";
  return "low";
}

export function formatConfidence(confidence: number | null): string {
  if (confidence == null || Number.isNaN(confidence)) return "—";
  const value = confidence > 1 ? confidence : confidence * 100;
  return `${Math.round(value)}%`;
}

export function deriveObservationType(label: string | null | undefined): ObservationType {
  if (!label) return "unknown";
  const text = label.toLowerCase();
  for (const entry of OBSERVATION_KEYWORDS) {
    if (entry.patterns.some((pattern) => pattern.test(text))) {
      return entry.type;
    }
  }
  return "unknown";
}

export function formatObservationTypeLabel(type: ObservationType): string {
  if (type === "unknown") return "Other";
  return type.replace(/(^.|\s.)/g, (segment) => segment.toUpperCase());
}

export function formatConfidenceTierLabel(tier: ConfidenceTier): string {
  if (tier === "unknown") return "Unknown";
  return tier.charAt(0).toUpperCase() + tier.slice(1);
}
