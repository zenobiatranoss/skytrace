import { useSyncExternalStore } from "react";

export type Selection =
  | { type: "aircraft"; id: string }
  | { type: "airport"; id: string }
  | { type: "flight"; id: string }
  | null;

export interface FocusTarget {
  longitude: number;
  latitude: number;
  zoom?: number;
  // bumped every request so the map reacts even to a repeated target
  nonce: number;
}

export interface MapSelectionState {
  selection: Selection;
  focus: FocusTarget | null;
}

let state: MapSelectionState = { selection: null, focus: null };
const listeners = new Set<() => void>();
let nonce = 0;

function emit(): void {
  for (const listener of listeners) listener();
}

function set(next: MapSelectionState): void {
  state = next;
  emit();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): MapSelectionState {
  return state;
}

export const mapSelection = {
  selectAircraft(icao24: string): void {
    set({ ...state, selection: { type: "aircraft", id: icao24 } });
  },
  selectAirport(code: string): void {
    set({ ...state, selection: { type: "airport", id: code } });
  },
  selectFlight(id: string): void {
    set({ ...state, selection: { type: "flight", id } });
  },
  focusOn(longitude: number, latitude: number, zoom?: number): void {
    nonce += 1;
    set({ ...state, focus: { longitude, latitude, zoom, nonce } });
  },
  clear(): void {
    set({ selection: null, focus: state.focus });
  },
};

export function useMapSelection(): MapSelectionState {
  return useSyncExternalStore(subscribe, getSnapshot);
}
