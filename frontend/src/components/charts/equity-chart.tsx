"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  LineSeries,
  type IChartApi,
  type LineData,
  type Time,
} from "lightweight-charts";

interface EquityPoint {
  time: string;
  value: number;
}

interface EquityChartProps {
  data: EquityPoint[];
  height?: number;
}

export function EquityChart({ data, height = 300 }: EquityChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.1)" },
      timeScale: { borderColor: "rgba(255,255,255,0.1)" },
    });

    const lineSeries = chart.addSeries(LineSeries, {
      color: "#22c55e",
      lineWidth: 2,
    });

    const lineData: LineData<Time>[] = data.map((d) => ({
      time: d.time.slice(0, 10) as unknown as Time,
      value: d.value,
    }));

    lineSeries.setData(lineData);
    chart.timeScale().fitContent();
    chartRef.current = chart;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data, height]);

  return <div ref={containerRef} className="w-full" />;
}
