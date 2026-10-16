import { NavLink } from "react-router-dom";

import { useAnomalies } from "../../hooks/useAnomalies";
import { SearchBar } from "../search/SearchBar";

export function TopBar() {
  const anomalies = useAnomalies();

  return (
    <header className="topbar">
      <SearchBar />

      <nav>
        <NavLink to="/" end>
          Map
        </NavLink>
        <NavLink to="/search">Search</NavLink>
        <NavLink to="/alerts">
          Alerts{anomalies.length > 0 ? ` (${anomalies.length})` : ""}
        </NavLink>
      </nav>
    </header>
  );
}
