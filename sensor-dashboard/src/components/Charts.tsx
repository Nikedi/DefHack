// src/components/Charts.tsx
import { LineChart, Line, PieChart, Pie, Tooltip, XAxis, YAxis, CartesianGrid, Legend, ResponsiveContainer } from "recharts";

export function TimeSeriesChart({ data }: any) {
  return (
    <div className="bg-white/5 rounded p-4 h-64 flex items-center justify-center text-gray-400">
      Time series chart (data points: {Array.isArray(data) ? data.length : 0})
    </div>
  );
}

export function WhatPieChart({ data }: any) {
  return (
    <div className="bg-white/5 rounded p-4 h-64 flex items-center justify-center text-gray-400">
      What distribution chart (categories: {Array.isArray(data) ? data.length : 0})
    </div>
  );
}