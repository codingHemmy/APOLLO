import { createTheme, ThemeOptions } from "@mui/material/styles";

export const createApolloTheme = (mode: "light" | "dark") =>
  createTheme({
    palette: {
      mode,
      primary: {
        main: mode === "dark" ? "#00bcd4" : "#006064",
      },
      background: {
        default: mode === "dark" ? "#101418" : "#f7f9fb",
        paper: mode === "dark" ? "#1a1f25" : "#ffffff",
      },
    },
    typography: {
      fontFamily: "'Inter', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    },
    shape: {
      borderRadius: 14,
    },
  });
