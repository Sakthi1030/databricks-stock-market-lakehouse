import * as echarts from "echarts";
import { useEffect, useRef } from "react";

interface EChartProps {
  option: echarts.EChartsCoreOption;
  className?: string;
  onClick?: (params: echarts.ECElementEvent) => void;
  ariaLabel?: string;
}

/** Thin ECharts wrapper: one instance per mount, resized with its container, options merged on change. */
export function EChart({ option, className = "h-64", onClick, ariaLabel }: EChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const clickRef = useRef(onClick);
  clickRef.current = onClick;

  useEffect(() => {
    if (!ref.current) return;
    const instance = echarts.init(ref.current, undefined, { renderer: "canvas" });
    chart.current = instance;
    instance.on("click", (p) => clickRef.current?.(p as echarts.ECElementEvent));
    const observer = new ResizeObserver(() => instance.resize());
    observer.observe(ref.current);
    return () => {
      observer.disconnect();
      instance.dispose();
      chart.current = null;
    };
  }, []);

  useEffect(() => {
    chart.current?.setOption({ animationDuration: 700, animationEasing: "cubicOut", ...option }, true);
  }, [option]);

  return <div ref={ref} className={className} role="img" aria-label={ariaLabel} />;
}
