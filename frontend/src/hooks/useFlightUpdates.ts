import { useSyncExternalStore } from "react";

import { flightSocket, type LiveState } from "../services/websocket";

export function useFlightUpdates(): LiveState {
  return useSyncExternalStore(flightSocket.subscribe, flightSocket.getSnapshot);
}
