export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_URL = API_URL.replace(/^http/, "ws");
export const HEARTBEAT_INTERVAL_SECONDS = 10;
export const PRESENCE_POLL_INTERVAL_MS = 20_000;
