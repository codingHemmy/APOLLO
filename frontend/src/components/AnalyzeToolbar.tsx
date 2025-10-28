import React from "react";
import {
  AppBar,
  Box,
  Button,
  IconButton,
  LinearProgress,
  Slider,
  Stack,
  Switch,
  Tab,
  Tabs,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import SaveIcon from "@mui/icons-material/Save";

import MachineSelector from "./MachineSelector";

interface Props {
  machines: number[];
  selectedMachine: number;
  onMachineSelect: (machine: number) => void;
  keyword: string;
  onKeywordChange: (value: string) => void;
  keywordHistory: string[];
  onKeywordSave: (keyword: string) => void;
  mode: "date" | "last_x";
  onModeChange: (mode: "date" | "last_x") => void;
  startDate: string;
  endDate: string;
  lastX: number;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onLastXChange: (value: number) => void;
  onRun: () => void;
  onCancel: () => void;
  running: boolean;
  progress: number;
  maxLabels: number;
  onMaxLabelsChange: (value: number) => void;
  tooltipEnabled: boolean;
  onTooltipToggle: (enabled: boolean) => void;
  modeTheme: "light" | "dark";
  onThemeToggle: () => void;
}

const AnalyzeToolbar: React.FC<Props> = ({
  machines,
  selectedMachine,
  onMachineSelect,
  keyword,
  onKeywordChange,
  keywordHistory,
  onKeywordSave,
  mode,
  onModeChange,
  startDate,
  endDate,
  lastX,
  onStartDateChange,
  onEndDateChange,
  onLastXChange,
  onRun,
  onCancel,
  running,
  progress,
  maxLabels,
  onMaxLabelsChange,
  tooltipEnabled,
  onTooltipToggle,
  modeTheme,
  onThemeToggle,
}) => {
  return (
    <AppBar position="sticky" elevation={4} color="default" sx={{ backdropFilter: "blur(6px)", py: 1 }}>
      <Toolbar sx={{ flexDirection: "column", alignItems: "stretch", gap: 1 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ width: "100%" }}>
          <Typography variant="h6">RoboDrill Navigator</Typography>
          <IconButton onClick={onThemeToggle} color="primary">
            {modeTheme === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        </Stack>
        <MachineSelector machines={machines} selected={selectedMachine} onSelect={onMachineSelect} />
        <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems={{ xs: "stretch", md: "center" }} sx={{ width: "100%" }}>
          <TextField
            label="Messwert"
            value={keyword}
            onChange={(event) => onKeywordChange(event.target.value)}
            placeholder="Durchmesser 1"
            sx={{ minWidth: 220 }}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                onRun();
              }
            }}
          />
          <Stack direction="row" spacing={1} alignItems="center">
            {keywordHistory.map((item) => (
              <Button key={item} size="small" variant="outlined" onClick={() => onKeywordChange(item)}>
                {item}
              </Button>
            ))}
            <Tooltip title="Begriff merken">
              <IconButton onClick={() => onKeywordSave(keyword)} disabled={!keyword.trim()}>
                <SaveIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
          <Tabs value={mode} onChange={(_, value) => onModeChange(value as "date" | "last_x")} sx={{ minHeight: 48 }}>
            <Tab label="Datum" value="date" />
            <Tab label="Letzte X" value="last_x" />
          </Tabs>
          {mode === "date" ? (
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1} alignItems="center">
              <TextField
                label="Start"
                value={startDate}
                placeholder="dd-mm-yy"
                onChange={(event) => onStartDateChange(event.target.value)}
                inputProps={{ pattern: "\\d{2}-\\d{2}-\\d{2}" }}
              />
              <TextField
                label="Ende"
                value={endDate}
                placeholder="dd-mm-yy"
                onChange={(event) => onEndDateChange(event.target.value)}
                inputProps={{ pattern: "\\d{2}-\\d{2}-\\d{2}" }}
              />
            </Stack>
          ) : (
            <TextField
              label="Letzte X"
              type="number"
              value={lastX}
              onChange={(event) => onLastXChange(Number(event.target.value))}
              inputProps={{ min: 1, max: 1000 }}
            />
          )}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 220 }}>
            <Typography variant="caption" color="text.secondary">
              Max. X-Labels
            </Typography>
            <Slider
              size="small"
              min={10}
              max={1000}
              value={maxLabels}
              onChange={(_, value) => onMaxLabelsChange(value as number)}
            />
          </Box>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="caption">Tooltips</Typography>
            <Switch checked={tooltipEnabled} onChange={(_, checked) => onTooltipToggle(checked)} />
          </Stack>
          <Box sx={{ position: "relative" }}>
            <Button
              variant="contained"
              color={running ? "secondary" : "primary"}
              onClick={running ? onCancel : onRun}
              sx={{ minWidth: 160 }}
            >
              {running ? "Abbrechen" : "AUSWERTEN"}
            </Button>
            {running && (
              <LinearProgress
                variant="determinate"
                value={Math.round(progress * 100)}
                sx={{ position: "absolute", left: 0, right: 0, bottom: -6, height: 4, borderRadius: 2 }}
              />
            )}
          </Box>
        </Stack>
      </Toolbar>
    </AppBar>
  );
};

export default AnalyzeToolbar;
