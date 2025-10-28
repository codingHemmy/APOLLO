import React from "react";
import { Box, Card, CardContent, Divider, Stack, Typography } from "@mui/material";

interface DetailProps {
  machine: number;
  totalFiles: number;
  ftpStatus: "ok" | "error";
  runtimePercent: number;
  latestFileName?: string;
  selectedFile?: { name: string; content: string } | null;
}

const DetailsPanel: React.FC<DetailProps> = ({
  machine,
  totalFiles,
  ftpStatus,
  runtimePercent,
  latestFileName,
  selectedFile,
}) => {
  return (
    <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <CardContent sx={{ flex: "0 0 auto" }}>
        <Typography variant="h5" gutterBottom>
          RoboDrill {machine}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          IP: 192.168.105.{machine}
        </Typography>
        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
          <InfoBadge label="Kugeln" value={totalFiles.toString()} />
          <InfoBadge label="FTP" value={ftpStatus === "ok" ? "✓ Verbunden" : "✗ Fehler"} color={ftpStatus === "ok" ? "success.main" : "error.main"} />
          <InfoBadge label="Laufzeit" value={`${runtimePercent.toFixed(1)} %`} />
        </Stack>
        <Typography variant="subtitle2" sx={{ mt: 3 }}>
          Aktuelles Protokoll: {latestFileName ?? "-"}
        </Typography>
      </CardContent>
      <Divider />
      <Box sx={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <Typography variant="subtitle2" sx={{ px: 2, pt: 2, pb: 1 }}>
          Protokollinhalt
        </Typography>
        <Box
          sx={{
            px: 2,
            pb: 2,
            flex: 1,
            overflow: "auto",
            fontFamily: "'Fira Code', 'Roboto Mono', monospace",
            whiteSpace: "pre",
            backgroundColor: (theme) => theme.palette.mode === "dark" ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)",
            borderTop: (theme) => `1px solid ${theme.palette.divider}`,
          }}
        >
          {selectedFile ? selectedFile.content : "Bitte Datenpunkt auswählen"}
        </Box>
      </Box>
    </Card>
  );
};

interface BadgeProps {
  label: string;
  value: string;
  color?: string;
}

const InfoBadge: React.FC<BadgeProps> = ({ label, value, color }) => (
  <Box
    sx={{
      px: 2,
      py: 1,
      borderRadius: 3,
      bgcolor: color ?? "action.hover",
      minWidth: 110,
    }}
  >
    <Typography variant="caption" color="text.secondary">
      {label}
    </Typography>
    <Typography variant="subtitle1" fontWeight={600}>
      {value}
    </Typography>
  </Box>
);

export default DetailsPanel;
