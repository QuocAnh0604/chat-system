import { useCallback, useEffect, useRef, useState } from "react";
import { HEARTBEAT_INTERVAL_SECONDS, WS_URL } from "../config";
import authAPI from "../API/authAPI";

export type SocketStatus = "disconnected" | "connecting" | "connected" | "reconnecting";

export interface MessageSendPayload {
  conversation_id?: string;
  target_user_id?: string;
  content: string;
  client_message_id: string;
}

export interface SocketEvent {
  event: string;
  [key: string]: unknown;
}

type EventHandler = (event: SocketEvent) => void;

const isSocketEvent = (value: unknown): value is SocketEvent => {
  if (typeof value !== "object" || value === null) return false;
  const event = (value as { event?: unknown }).event;
  return typeof event === "string";
};

export function useChatSocket(onAuthExpired?: () => void) {
  const socketRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef(new Set<EventHandler>());
  const reconnectTimerRef = useRef<number | null>(null);
  const connectRef = useRef<() => void>(() => undefined);
  const reconnectAttemptRef = useRef(0);
  const stoppedRef = useRef(false);
  const authExpiredRef = useRef(false);
  const manualReconnectRef = useRef(false);
  const onAuthExpiredRef = useRef(onAuthExpired);
  const [status, setStatus] = useState<SocketStatus>("disconnected");

  const emit = useCallback((event: SocketEvent) => {
    handlersRef.current.forEach((handler) => handler(event));
  }, []);

  const connect = useCallback(() => {
    if (stoppedRef.current || authExpiredRef.current) return;
    const token = localStorage.getItem("access_token");
    if (!token) {
      setStatus("disconnected");
      return;
    }

    setStatus(reconnectAttemptRef.current > 0 ? "reconnecting" : "connecting");
    const socket = new WebSocket(`${WS_URL}/ws`);
    socketRef.current = socket;
    let heartbeat: number | null = null;

    socket.addEventListener("open", () => {
      reconnectAttemptRef.current = 0;
      setStatus("connected");
      socket.send(JSON.stringify({ type: "auth", token }));
      heartbeat = window.setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ping" }));
        }
      }, HEARTBEAT_INTERVAL_SECONDS * 1000);
    });

    socket.addEventListener("message", (message) => {
      try {
        const parsed: unknown = JSON.parse(String(message.data));
        if (!isSocketEvent(parsed)) return;
        if (parsed.event === "auth.expired") {
          authExpiredRef.current = true;
          setStatus("disconnected");
          const refreshToken = localStorage.getItem("refresh_token");
          if (!refreshToken) {
            onAuthExpiredRef.current?.();
          } else {
            void authAPI
              .refresh(refreshToken)
              .then((tokens) => {
                localStorage.setItem("access_token", tokens.access_token);
                localStorage.setItem("refresh_token", tokens.refresh_token);
                authExpiredRef.current = false;
                reconnectAttemptRef.current = 0;
                manualReconnectRef.current = true;
                socket.close();
                connectRef.current();
              })
              .catch(() => onAuthExpiredRef.current?.());
          }
        }
        emit(parsed);
      } catch {
        // Ignore malformed server frames and keep the socket alive.
      }
    });

    socket.addEventListener("close", () => {
      if (heartbeat !== null) window.clearInterval(heartbeat);
      if (manualReconnectRef.current) {
        manualReconnectRef.current = false;
        return;
      }
      if (stoppedRef.current || authExpiredRef.current) return;
      const attempt = reconnectAttemptRef.current;
      reconnectAttemptRef.current = Math.min(attempt + 1, 6);
      const baseDelay = Math.min(1000 * 2 ** attempt, 30_000);
      const jitter = Math.floor(Math.random() * 250);
      setStatus("reconnecting");
      reconnectTimerRef.current = window.setTimeout(
        () => connectRef.current(),
        baseDelay + jitter,
      );
    });
  }, [emit]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    stoppedRef.current = false;
    authExpiredRef.current = false;
    connectRef.current();

    return () => {
      stoppedRef.current = true;
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [connect]);

  const sendMessage = useCallback((payload: MessageSendPayload): boolean => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ type: "message.send", ...payload }));
    return true;
  }, []);

  const onEvent = useCallback((handler: EventHandler) => {
    handlersRef.current.add(handler);
    return () => handlersRef.current.delete(handler);
  }, []);

  return { status, sendMessage, onEvent };
}
