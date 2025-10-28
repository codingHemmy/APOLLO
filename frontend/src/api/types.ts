export interface MachineResponse {
  machines: number[];
}

export interface HealthResponse {
  ok: boolean;
  ftp: "connected" | "error";
}

export interface LatestFileResponse {
  filename: string;
  modified: string | null;
  size: number | null;
  content: string;
}

export interface AnalyzeRequest {
  machine: number;
  mode: "date" | "last_x";
  startDate?: string;
  endDate?: string;
  lastX?: number;
  keyword: string;
  maxLabels?: number;
  tooltipThreshold?: number;
}

export interface AnalyzePoint {
  idx: number;
  value: number;
  label: string;
  timeIso: string;
  localPathId: string;
}

export interface AnalyzeResponse {
  points: AnalyzePoint[];
  mean: number | null;
  totalFiles: number;
  machineRuntimePercent: number;
  ftpStatus: "ok" | "error";
  latestFileName?: string;
}

export interface ProgressEvent {
  progress?: number;
  stage?: string;
  result?: AnalyzeResponse;
  error?: string;
  status?: number;
}
