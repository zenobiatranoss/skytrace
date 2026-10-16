import { describe, expect, it, vi } from "vitest";

import { FlightSocket, decodePositions } from "./websocket";

const FIELDS = [
  "icao24",
  "callsign",
  "latitude",
  "longitude",
  "altitude_m",
  "velocity_ms",
  "heading",
  "vertical_rate_ms",
  "on_ground",
  "status",
  "last_contact",
  "age_seconds",
  "is_stale",
];

describe("decodePositions", () => {
  it("rebuilds positions from the compact row format", () => {
    const rows = [
      ["39de4f", "TVF89EQ", 40.4619, 1.9286, 9753.6, 233.3, 351.0, 7.8, false, 2, 1792174618, 7.3, false],
    ];

    const [position] = decodePositions(FIELDS, rows);
    expect(position.icao24).toBe("39de4f");
    expect(position.callsign).toBe("TVF89EQ");
    expect(position.latitude).toBe(40.4619);
    expect(position.status).toBe("airborne");
    expect(position.last_contact).toBe(
      new Date(1792174618 * 1000).toISOString(),
    );
    expect(position.is_stale).toBe(false);
  });

  it("maps status codes back to names", () => {
    const rows = [
      ["a", null, null, null, null, null, null, null, true, 1, null, null, false],
      ["b", null, null, null, null, null, null, null, false, 3, null, null, true],
    ];
    const [first, second] = decodePositions(FIELDS, rows);
    expect(first.status).toBe("on_ground");
    expect(second.status).toBe("stale");
  });

  it("keeps missing values null instead of undefined", () => {
    const rows = [
      ["abc123", null, null, null, null, null, null, null, null, 0, null, null, false],
    ];
    const [position] = decodePositions(FIELDS, rows);
    expect(position.altitude_m).toBeNull();
    expect(position.last_contact).toBeNull();
    expect(position.status).toBe("unknown");
  });

  it("decodes by field name, not order", () => {
    const shuffled = [...FIELDS].reverse();
    const row = ["39de4f", "TVF89EQ", 40.4619, 1.9286, 9753.6, 233.3, 351.0, 7.8, false, 2, 1792174618, 7.3, false];
    const reversed = [...row].reverse();

    const [position] = decodePositions(shuffled, [reversed]);
    expect(position.icao24).toBe("39de4f");
    expect(position.status).toBe("airborne");
  });
});

describe("FlightSocket", () => {
  function withFakeWebSocket() {
    const sockets: Array<Record<string, unknown>> = [];
    class FakeSocket {
      onopen: (() => void) | null = null;
      onmessage: ((event: { data: string }) => void) | null = null;
      onclose: (() => void) | null = null;
      onerror: (() => void) | null = null;
      readyState = 0;
      constructor(public url: string) {
        sockets.push(this as unknown as Record<string, unknown>);
      }
      close() {
        this.readyState = 3;
      }
    }
    vi.stubGlobal("WebSocket", FakeSocket);
    return sockets;
  }

  it("stores anomalies from the live message", () => {
    const sockets = withFakeWebSocket();
    const socket = new FlightSocket("ws://test/ws");
    const unsubscribe = socket.subscribe(() => {});
    const fake = sockets[0] as unknown as {
      onopen?: () => void;
      onmessage?: (event: { data: string }) => void;
    };

    fake.onopen?.();
    fake.onmessage?.({
      data: JSON.stringify({
        type: "anomalies",
        count: 1,
        items: [
          {
            id: 7,
            icao24: "abc123",
            callsign: "EZY123",
            kind: "emergency_squawk",
            severity: "critical",
            message: "Squawking 7700 - general emergency",
            latitude: 40.4,
            longitude: 1.9,
            first_seen: "2026-01-01T00:00:00Z",
            last_seen: "2026-01-01T00:00:00Z",
            active: true,
          },
        ],
      }),
    });

    const state = socket.getSnapshot();
    expect(state.connected).toBe(true);
    expect(state.anomalies).toHaveLength(1);
    expect(state.anomalies[0].kind).toBe("emergency_squawk");

    unsubscribe();
    vi.unstubAllGlobals();
  });
});
