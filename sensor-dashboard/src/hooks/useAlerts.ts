import { useEffect } from "react";

export function useAlerts(onAlert?: (payload: any) => void) {
  useEffect(() => {
    // placeholder for websocket or polling integration
    // const ws = new WebSocket("ws://localhost:8080/alerts");
    // ws.onmessage = (ev) => { const data = JSON.parse(ev.data); onAlert?.(data); };
    return () => {
      // ws?.close();
    };
  }, [onAlert]);

  return {
    playSound: (name: string) => {
      // placeholder: integrate Howler or Audio element here
      // new Audio(`/sounds/${name}.mp3`).play();
    },
  };
}