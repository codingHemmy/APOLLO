import React from "react";
import { Box, Chip } from "@mui/material";

interface Props {
  machines: number[];
  selected: number;
  onSelect: (machine: number) => void;
}

const MachineSelector: React.FC<Props> = ({ machines, selected, onSelect }) => {
  return (
    <Box sx={{ display: "flex", gap: 1, overflowX: "auto", py: 1 }}>
      {machines.map((machine) => (
        <Chip
          key={machine}
          label={`RoboDrill ${machine}`}
          color={machine === selected ? "primary" : "default"}
          onClick={() => onSelect(machine)}
          sx={{ minWidth: 120 }}
          clickable
        />
      ))}
    </Box>
  );
};

export default MachineSelector;
