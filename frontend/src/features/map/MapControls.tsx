import maplibregl from "maplibre-gl";

const HOME_CENTER: [number, number] = [0, 0];
const HOME_ZOOM = 1.5;

interface Props {
  map: maplibregl.Map;
  following: boolean;
  onToggleFollow: () => void;
}

export function MapControls({ map, following, onToggleFollow }: Props) {
  return (
    <div className="map-controls">
      <button type="button" title="Zoom in" onClick={() => map.zoomIn()}>
        +
      </button>
      <button type="button" title="Zoom out" onClick={() => map.zoomOut()}>
        –
      </button>
      <button
        type="button"
        title="Reset view"
        onClick={() => map.flyTo({ center: HOME_CENTER, zoom: HOME_ZOOM })}
      >
        ⟳
      </button>
      <button
        type="button"
        title="Follow selected aircraft"
        className={following ? "on" : undefined}
        onClick={onToggleFollow}
      >
        ◎
      </button>
    </div>
  );
}
