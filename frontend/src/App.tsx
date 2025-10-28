import React from "react";
import { Box, Container, Grid } from "@mui/material";
import { useQuery } from "@tanstack/react-query";

import AnalyzeToolbar from "./components/AnalyzeToolbar";
import ChartPanel from "./components/ChartPanel";
import DetailsPanel from "./components/DetailsPanel";
import StatusBar, { StatusLevel } from "./components/StatusBar";
import {
  analyzeStream,
  fetchFileContent,
  fetchHealth,
  fetchLatest,
  fetchMachines,
} from "./api/client";
import { AnalyzePoint, AnalyzeResponse } from "./api/types";

interface AppProps {
  mode: "light" | "dark";
  setMode: (mode: "light" | "dark") => void;
}

const App: React.FC<AppProps> = ({ mode, setMode }) => {
  const [selectedMachine, setSelectedMachine] = React.useState(1);
  const [keyword, setKeyword] = React.useState("Durchmesser 1");
  const [history, setHistory] = React.useState<string[]>([]);
  const [analysisMode, setAnalysisMode] = React.useState<"date" | "last_x">("last_x");
  const [startDate, setStartDate] = React.useState("01-09-25");
  const [endDate, setEndDate] = React.useState("30-09-25");
  const [lastX, setLastX] = React.useState(10);
  const [maxLabels, setMaxLabels] = React.useState(120);
  const [tooltipEnabled, setTooltipEnabled] = React.useState(true);
  const [tooltipThreshold, setTooltipThreshold] = React.useState(300);
  const [result, setResult] = React.useState<AnalyzeResponse | null>(null);
  const [running, setRunning] = React.useState(false);
  const [progress, setProgress] = React.useState(0);
  const [status, setStatus] = React.useState<{ timestamp: Date; level: StatusLevel; message: string }>(() => ({
    timestamp: new Date(),
    level: "INFO",
    message: "Bereit",
  }));
  const [selectedFile, setSelectedFile] = React.useState<{ name: string; content: string } | null>(null);
  const controllerRef = React.useRef<AbortController | null>(null);

  const { data: machineData } = useQuery({
    queryKey: ["machines"],
    queryFn: fetchMachines,
  });

  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 15000,
  });

  const { data: latestData, refetch: refetchLatest } = useQuery({
    queryKey: ["latest", selectedMachine],
    queryFn: () => fetchLatest(selectedMachine),
  });

  const showStatus = (level: StatusLevel, message: string) => {
    setStatus({ level, message, timestamp: new Date() });
  };

  const handleKeywordSave = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    setHistory((prev) => Array.from(new Set([trimmed, ...prev])).slice(0, 6));
  };

  const handleAnalyze = React.useCallback(() => {
    if (!keyword.trim()) {
      showStatus("WARN", "Bitte Messwert eingeben");
      return;
    }
    if (analysisMode === "date" && (!startDate || !endDate)) {
      showStatus("WARN", "Start- und Enddatum erforderlich");
      return;
    }
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setRunning(true);
    setProgress(0);
    showStatus("INFO", "ANALYSE LÄUFT…");
    setSelectedFile(null);
    const payload = {
      machine: selectedMachine,
      mode: analysisMode,
      startDate: analysisMode === "date" ? startDate : undefined,
      endDate: analysisMode === "date" ? endDate : undefined,
      lastX: analysisMode === "last_x" ? lastX : undefined,
      keyword,
      maxLabels,
      tooltipThreshold,
    };
    analyzeStream(payload, (event) => {
      if (event.progress !== undefined) {
        setProgress(event.progress);
      }
      if (event.error) {
        showStatus("ERROR", event.error);
        setRunning(false);
      }
      if (event.result) {
        setResult(event.result);
        showStatus("OK", "FERTIG");
        setRunning(false);
        setProgress(1);
      }
    }, controller.signal).catch((error) => {
      if (controller.signal.aborted) {
        showStatus("WARN", "Analyse abgebrochen");
      } else {
        showStatus("ERROR", error.message);
      }
      setRunning(false);
    });
  }, [analysisMode, endDate, keyword, lastX, maxLabels, selectedMachine, startDate, tooltipThreshold]);

  const handleCancel = () => {
    controllerRef.current?.abort();
  };

  const handlePointClick = async (point: AnalyzePoint) => {
    if (!point.localPathId) {
      showStatus("WARN", "Kein Inhalt verfügbar");
      return;
    }
    try {
      const content = await fetchFileContent(point.localPathId);
      setSelectedFile({ name: point.label, content });
      showStatus("INFO", `Protokoll ${point.label} geladen`);
    } catch (error: any) {
      showStatus("ERROR", error.message);
    }
  };

  const toggleTheme = () => {
    setMode(mode === "dark" ? "light" : "dark");
  };

  React.useEffect(() => {
    if (result?.latestFileName) {
      refetchLatest();
    }
  }, [result?.latestFileName, refetchLatest]);

  React.useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape" && running) {
        handleCancel();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [running]);

  React.useEffect(() => {
    setResult(null);
    setSelectedFile(null);
    refetchLatest();
  }, [selectedMachine, refetchLatest]);

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <AnalyzeToolbar
        machines={machineData?.machines ?? []}
        selectedMachine={selectedMachine}
        onMachineSelect={setSelectedMachine}
        keyword={keyword}
        onKeywordChange={setKeyword}
        keywordHistory={history}
        onKeywordSave={handleKeywordSave}
        mode={analysisMode}
        onModeChange={setAnalysisMode}
        startDate={startDate}
        endDate={endDate}
        lastX={lastX}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
        onLastXChange={(value) => setLastX(Math.max(1, value || 1))}
        onRun={handleAnalyze}
        onCancel={handleCancel}
        running={running}
        progress={progress}
        maxLabels={maxLabels}
        onMaxLabelsChange={setMaxLabels}
        tooltipEnabled={tooltipEnabled}
        onTooltipToggle={setTooltipEnabled}
        modeTheme={mode}
        onThemeToggle={toggleTheme}
      />
      <Container maxWidth="xl" sx={{ flex: 1, py: 3 }}>
        <Grid container spacing={3} sx={{ height: "100%" }}>
          <Grid item xs={12} md={4} sx={{ height: { xs: "auto", md: "calc(100vh - 240px)" } }}>
            <DetailsPanel
              machine={selectedMachine}
              totalFiles={result?.totalFiles ?? 0}
              ftpStatus={result?.ftpStatus ?? (healthData?.ftp === "connected" ? "ok" : "error")}
              runtimePercent={result?.machineRuntimePercent ?? 0}
              latestFileName={result?.latestFileName ?? latestData?.filename}
              selectedFile={selectedFile ?? (latestData ? { name: latestData.filename, content: latestData.content } : null)}
            />
          </Grid>
          <Grid item xs={12} md={8} sx={{ height: { xs: "auto", md: "calc(100vh - 240px)" } }}>
            <ChartPanel
              points={result?.points ?? []}
              mean={result?.mean ?? null}
              tooltipEnabled={tooltipEnabled}
              tooltipThreshold={tooltipThreshold}
              maxLabels={maxLabels}
              onPointClick={handlePointClick}
            />
          </Grid>
        </Grid>
      </Container>
      <StatusBar timestamp={status.timestamp} level={status.level} message={status.message} />
    </Box>
  );
};

export default App;
