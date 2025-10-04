declare module "mgrs" {
  export function toPoint(mgrsString: string): [number, number];
  export function forward(coordinates: [number, number], accuracy?: number): string;
}
