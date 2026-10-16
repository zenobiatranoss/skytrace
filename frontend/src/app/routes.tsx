import { Navigate, Route, Routes } from "react-router-dom";

import { FlightMap } from "../features/map/FlightMap";
import { SidePanel } from "../components/layout/SidePanel";
import { SearchPage } from "../features/search/SearchPage";
import { AlertsPage } from "../features/anomalies/AlertsPage";

function MapView() {
  return (
    <>
      <FlightMap />
      <SidePanel />
    </>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<MapView />} />
      <Route path="/search" element={<SearchPage />} />
      <Route path="/alerts" element={<AlertsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
