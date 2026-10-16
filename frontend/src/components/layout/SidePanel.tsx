import { useMapSelection } from "../../hooks/useMapSelection";
import { AircraftPanel } from "../aircraft/AircraftPanel";
import { AirportPanel } from "../airports/AirportPanel";
import { FlightDetails } from "../../features/flights/FlightDetails";

export function SidePanel() {
  const { selection } = useMapSelection();
  if (!selection) return null;

  return (
    <aside className="side-panel">
      {selection.type === "aircraft" && <AircraftPanel icao24={selection.id} />}
      {selection.type === "airport" && <AirportPanel code={selection.id} />}
      {selection.type === "flight" && (
        <FlightDetails flightId={Number(selection.id)} />
      )}
    </aside>
  );
}
