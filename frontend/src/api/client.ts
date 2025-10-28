import axios from "axios";
import { AnalyzeRequest, AnalyzeResponse, HealthResponse, LatestFileResponse, MachineResponse, ProgressEvent } from "./types";

const api = axios.create({
  baseURL: "/api",
  timeout: 20000,
});

export const fetchMachines = async (): Promise<MachineResponse> => {
  const { data } = await api.get<MachineResponse>("/machines");
  return data;
};

export const fetchHealth = async (): Promise<HealthResponse> => {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
};

export const fetchLatest = async (machine: number): Promise<LatestFileResponse> => {
  const { data } = await api.get<LatestFileResponse>("/latest", { params: { machine } });
  return data;
};

export const fetchFileContent = async (token: string): Promise<string> => {
  const { data } = await api.get<string>("/file", { params: { token }, responseType: "text" });
  return data;
};

export const analyzeStream = async (
  payload: AnalyzeRequest,
  onEvent: (event: ProgressEvent) => void,
  signal: AbortSignal,
): Promise<void> => {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    throw new Error(`Analyse konnte nicht gestartet werden (${response.status})`);
  }
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Keine Stream-Verbindung verfügbar");
  }
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const chunk = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 2);
      if (chunk.startsWith("data:")) {
        const data = chunk.replace(/^data:/, "").trim();
        if (data) {
          onEvent(JSON.parse(data));
        }
      }
    }
  }
};
