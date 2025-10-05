import { useEffect } from "react";

export function useAlerts(onAlert?: (payload: any) => void) {
  useEffect(() => {
    // placeholder: connect to websocket or polling
    // const ws = new WebSocket("ws://localhost:8080/alerts");
    // ws.onmessage = (ev) => { const data = JSON.parse(ev.data); onAlert?.(data); /* play sound */ };
    return () => {
      // ws?.close();
    };
  }, [onAlert]);

  return {
    playSound: (name: string) => {
      // placeholder hook - integrate Howler or HTMLAudioElement here
      // new Audio(`/sounds/${name}.mp3`).play();
    },
  };
}