import type { AircraftPosition } from "../../types/aircraft";

export interface AircraftFilterState {
  hideOnGround: boolean;
  hideStale: boolean;
}

export const defaultFilters: AircraftFilterState = {
  hideOnGround: false,
  hideStale: false,
};

export function applyFilters(
  aircraft: AircraftPosition[],
  filters: AircraftFilterState,
): AircraftPosition[] {
  return aircraft.filter((plane) => {
    if (filters.hideOnGround && plane.on_ground) return false;
    if (filters.hideStale && plane.is_stale) return false;
    return true;
  });
}

interface Props {
  filters: AircraftFilterState;
  onChange: (next: AircraftFilterState) => void;
}

export function AircraftFilters({ filters, onChange }: Props) {
  return (
    <div className="aircraft-filters">
      <label>
        <input
          type="checkbox"
          checked={filters.hideOnGround}
          onChange={(e) =>
            onChange({ ...filters, hideOnGround: e.target.checked })
          }
        />
        Hide on ground
      </label>
      <label>
        <input
          type="checkbox"
          checked={filters.hideStale}
          onChange={(e) => onChange({ ...filters, hideStale: e.target.checked })}
        />
        Hide stale
      </label>
    </div>
  );
}
