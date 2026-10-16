import type { SearchResult } from "../../types/api";

interface Props {
  results: SearchResult[];
  activeIndex: number;
  onSelect: (result: SearchResult) => void;
  onHover: (index: number) => void;
}

export function SearchResults({ results, activeIndex, onSelect, onHover }: Props) {
  if (results.length === 0) return null;

  return (
    <div className="search-results">
      <ul>
        {results.map((result, index) => (
          <li
            key={`${result.kind}-${result.id}`}
            className={index === activeIndex ? "active" : undefined}
            onMouseEnter={() => onHover(index)}
            onMouseDown={(e) => {
              // mousedown fires before the input blur closes the dropdown
              e.preventDefault();
              onSelect(result);
            }}
          >
            <span className="kind">{result.kind}</span>
            <span className="label">{result.label}</span>
            {result.subtitle && (
              <span className="subtitle">{result.subtitle}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
