import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "mapbox-gl/dist/mapbox-gl.css";
import "./index.css";

const queryClient = new QueryClient();

// NOTE: React.StrictMode is intentionally omitted. Its dev-only double-mount
// (mount → unmount → remount) makes the Mapbox GL map create → remove → recreate
// itself on every load, churning WebGL contexts and racing the GL teardown.
// Mapbox GL doesn't tolerate the synthetic remount; omitting StrictMode is the
// standard approach for a map-backed app. (The intake form's robustness — the
// pending-target flyTo queue — does not depend on this.)
ReactDOM.createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
);
