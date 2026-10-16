import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { searchAircraft } from "../../services/aircraftApi";
import type { SearchResult } from "../../types/api";
import { mapSelection } from "../../hooks/useMapSelection";
import { SearchResults } from "./SearchResults";

const DEBOUNCE_MS = 220;

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const navigate = useNavigate();
  const boxRef = useRef<HTMLDivElement>(null);

  // debounce the lookup so we're not firing a request per keystroke
  useEffect(() => {
    const term = query.trim();
    if (term.length < 2) {
      setResults([]);
      return;
    }

    const timer = window.setTimeout(async () => {
      try {
        const response = await searchAircraft(term);
        setResults(response.results);
        setActiveIndex(response.results.length ? 0 : -1);
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function onClickAway(event: MouseEvent) {
      if (!boxRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickAway);
    return () => document.removeEventListener("mousedown", onClickAway);
  }, []);

  function choose(result: SearchResult) {
    if (result.kind === "aircraft") mapSelection.selectAircraft(result.id);
    else if (result.kind === "airport") mapSelection.selectAirport(result.id);
    else if (result.kind === "flight") mapSelection.selectFlight(result.id);

    if (result.latitude !== null && result.longitude !== null) {
      mapSelection.focusOn(result.longitude, result.latitude, 6);
    }

    setQuery("");
    setResults([]);
    setOpen(false);
    navigate("/");
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (!open || results.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => (i + 1) % results.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => (i - 1 + results.length) % results.length);
    } else if (event.key === "Enter" && activeIndex >= 0) {
      choose(results[activeIndex]);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="search-bar" ref={boxRef}>
      <input
        type="search"
        value={query}
        placeholder="Search flight, registration, airport…"
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
        onKeyDown={onKeyDown}
      />
      {open && (
        <SearchResults
          results={results}
          activeIndex={activeIndex}
          onSelect={choose}
          onHover={setActiveIndex}
        />
      )}
    </div>
  );
}
