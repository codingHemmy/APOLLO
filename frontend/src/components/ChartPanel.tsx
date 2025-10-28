import React from "react";
import ReactECharts from "echarts-for-react";
import { Card, CardContent, Stack, Typography } from "@mui/material";
import { AnalyzePoint } from "../api/types";

interface Props {
  points: AnalyzePoint[];
  mean: number | null;
  tooltipEnabled: boolean;
  tooltipThreshold: number;
  maxLabels: number;
  onPointClick: (point: AnalyzePoint) => void;
}

const ChartPanel: React.FC<Props> = ({ points, mean, tooltipEnabled, tooltipThreshold, maxLabels, onPointClick }) => {
  const option = React.useMemo(() => {
    const showTooltips = tooltipEnabled && points.length <= tooltipThreshold;
    const xAxisLabels = points.map((p) => p.idx);
    const step = Math.max(1, Math.floor(points.length / maxLabels));
    return {
      animation: false,
      backgroundColor: "transparent",
      tooltip: showTooltips
        ? {
            trigger: "item",
            formatter: (params: any) => {
              const point = points[params.dataIndex];
              return `#${point.idx}<br/>${point.label}<br/>${new Date(point.timeIso).toLocaleString()}<br/><b>${point.value.toFixed(4)} mm</b>`;
            },
          }
        : undefined,
      grid: { left: 40, right: 20, top: 40, bottom: 60 },
      xAxis: {
        type: "category",
        data: xAxisLabels,
        axisLabel: {
          interval: (value: number, index: number) => index % step === 0,
        },
      },
      yAxis: {
        type: "value",
        name: "mm",
        scale: true,
      },
      dataZoom: [
        { type: "slider", start: 0, end: 100 },
        { type: "inside" },
      ],
      series: [
        {
          name: "Messwert",
          type: "line",
          smooth: true,
          showSymbol: true,
          symbolSize: 10,
          data: points.map((p) => [p.idx, p.value]),
          lineStyle: { color: "#00bcd4" },
        },
        mean !== null
          ? {
              name: "Ø",
              type: "line",
              data: points.map((p) => [p.idx, mean]),
              lineStyle: { type: "dashed", color: "#ef5350" },
              showSymbol: false,
            }
          : {},
      ],
    };
  }, [points, mean, tooltipEnabled, tooltipThreshold, maxLabels]);

  return (
    <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <CardContent sx={{ flex: "1 1 auto", display: "flex", flexDirection: "column" }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Typography variant="h6">Diagramm</Typography>
        </Stack>
        <ReactECharts
          style={{ flex: 1, minHeight: 420 }}
          option={option}
          onEvents={{
            click: (params) => {
              const point = points[params.dataIndex];
              if (point) {
                onPointClick(point);
              }
            },
          }}
        />
      </CardContent>
    </Card>
  );
};

export default ChartPanel;
