import React from "react";
import { Box, Typography } from "@mui/material";

export type StatusLevel = "INFO" | "OK" | "WARN" | "ERROR";

interface Props {
  timestamp: Date;
  level: StatusLevel;
  message: string;
}

const levelColors: Record<StatusLevel, (theme: any) => string> = {
  INFO: (theme) => theme.palette.primary.main,
  OK: (theme) => theme.palette.success.main,
  WARN: (theme) => theme.palette.warning.main,
  ERROR: (theme) => theme.palette.error.main,
};

const StatusBar: React.FC<Props> = ({ timestamp, level, message }) => {
  return (
    <Box
      sx={{
        position: "sticky",
        bottom: 0,
        width: "100%",
        px: 3,
        py: 1,
        bgcolor: (theme) => theme.palette.background.paper,
        borderTop: (theme) => `1px solid ${theme.palette.divider}`,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        zIndex: 10,
      }}
    >
      <Typography variant="caption" color="text.secondary">
        {timestamp.toLocaleString()}
      </Typography>
      <Typography variant="subtitle2" sx={{ color: (theme) => levelColors[level](theme) }}>
        [{level}] {message}
      </Typography>
    </Box>
  );
};

export default StatusBar;
