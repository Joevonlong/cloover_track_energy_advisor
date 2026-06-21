import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

// Heimwende SPA — Vite config (backbone F01).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
    // Force a single React instance — guards against the "Invalid hook call"
    // dual-React that bites when a dep (react-hook-form) is imported the first
    // time and Vite resolves react via a second path.
    dedupe: ["react", "react-dom"],
  },
  optimizeDeps: {
    include: ["react", "react-dom", "react-hook-form", "zod"],
  },
  server: { port: 5173 },
});
