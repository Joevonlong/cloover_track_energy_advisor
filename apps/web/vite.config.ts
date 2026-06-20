import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Heimwende SPA — Vite config (backbone F01).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: { port: 5173 },
});
