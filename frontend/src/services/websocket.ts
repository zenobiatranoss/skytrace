import type { AircraftPosition, AircraftStatus } from "../types/aircraft";
import type { Anomaly } from "../types/anomaly";

export interface LiveState {
  aircraft: AircraftPosition[];
  anomalies: Anomaly[];
  connected: boolean;
  updatedAt: string | null;
  error: string | null;
}

const initialState: LiveState = {
  aircraft: [],
  anomalies: [],
  connected: false,
  updatedAt: null,
  error: null,
};

function deriveUrl(): string {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${window.location.host}/ws`;
}

type Cell = string | number | boolean | null;

type Message =
  | { type: "status"; aircraft_tracked: number }
  | {
      type: "positions";
      updated_at: string | null;
      count: number;
      fields: string[];
      aircraft: Cell[][];
    }
  | { type: "anomalies"; count: number; items: Anomaly[] };

const STATUS_BY_CODE: AircraftStatus[] = [
  "unknown",
  "on_ground",
  "airborne",
  "stale",
];

// the server sends rows of values plus the field order, so we rebuild the
// same object shape the rest api returns. decoding by field name keeps us
// from breaking if the server reorders columns.
export function decodePositions(
  fields: string[],
  rows: Cell[][],
): AircraftPosition[] {
  const index = new Map(fields.map((name, i) => [name, i]));
  const get = (row: Cell[], name: string): Cell => {
    const i = index.get(name);
    return i === undefined ? null : row[i];
  };

  return rows.map((row) => {
    const lastContact = get(row, "last_contact");
    return {
      icao24: String(get(row, "icao24")),
      callsign: (get(row, "callsign") as string | null) ?? null,
      registration: null,
      type_code: null,
      latitude: (get(row, "latitude") as number | null) ?? null,
      longitude: (get(row, "longitude") as number | null) ?? null,
      altitude_m: (get(row, "altitude_m") as number | null) ?? null,
      velocity_ms: (get(row, "velocity_ms") as number | null) ?? null,
      heading: (get(row, "heading") as number | null) ?? null,
      vertical_rate_ms: (get(row, "vertical_rate_ms") as number | null) ?? null,
      on_ground: (get(row, "on_ground") as boolean | null) ?? null,
      status: STATUS_BY_CODE[Number(get(row, "status"))] ?? "unknown",
      last_contact:
        typeof lastContact === "number"
          ? new Date(lastContact * 1000).toISOString()
          : null,
      age_seconds: (get(row, "age_seconds") as number | null) ?? null,
      is_stale: Boolean(get(row, "is_stale")),
    };
  });
}

export class FlightSocket {
  private socket: WebSocket | null = null;
  private listeners = new Set<() => void>();
  private state: LiveState = initialState;
  private reconnectDelay = 1000;
  private reconnectTimer: number | null = null;
  private readonly url: string;

  constructor(url: string = deriveUrl()) {
    this.url = url;
  }

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    this.open();
    return () => {
      this.listeners.delete(listener);
      // last listener gone, no reason to keep the connection
      if (this.listeners.size === 0) this.close();
    };
  };

  getSnapshot = (): LiveState => this.state;

  private emit(): void {
    for (const listener of this.listeners) listener();
  }

  private patch(partial: Partial<LiveState>): void {
    this.state = { ...this.state, ...partial };
    this.emit();
  }

  private open(): void {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectDelay = 1000;
      this.patch({ connected: true, error: null });
    };

    socket.onmessage = (event) => {
      let message: Message;
      try {
        message = JSON.parse(event.data);
      } catch {
        return;
      }
      if (message.type === "positions") {
        this.patch({
          aircraft: decodePositions(message.fields, message.aircraft),
          updatedAt: message.updated_at,
        });
      } else if (message.type === "anomalies") {
        this.patch({ anomalies: message.items });
      }
    };

    socket.onclose = () => {
      this.socket = null;
      this.patch({ connected: false });
      this.scheduleReconnect();
    };

    socket.onerror = () => {
      this.patch({ error: "live connection lost" });
    };
  }

  private scheduleReconnect(): void {
    if (this.listeners.size === 0) return;
    if (this.reconnectTimer !== null) return;

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.open();
    }, this.reconnectDelay);

    // back off up to half a minute
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  close(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.close();
      this.socket = null;
    }
    this.patch({ connected: false });
  }
}

export const flightSocket = new FlightSocket();
