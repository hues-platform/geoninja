/**
 * Location search input (geocoding).
 *
 * Uses OpenStreetMap Nominatim to geocode a free-text query and returns the best
 * match (limit=1). When a result is found, calls `onSelect` with the coordinate
 * (lat/lng in WGS84) and a human-readable label.
 *
 * UX notes:
 * - Searches on Enter or via the button.
 * - Debounce is not implemented; instead, in-flight requests are aborted when a
 *   new search starts.
 * - Errors are shown inline below the input.
 */
import { useRef, useState } from "react";

export type LocationSearchBarProps = {
  /** Called with the chosen coordinate and display label when geocoding succeeds. */
  onSelect: (pos: { lat: number; lng: number }, label: string) => void;

  /** Optional placeholder text for the input. */
  placeholder?: string;

  /** Optional label for the search button. */
  buttonLabel?: string;

  /** Minimum number of characters required before searching. */
  minChars?: number;
};

type NominatimResult = {
  /** Human-readable place label returned by Nominatim. */
  displayName: string;

  /** Latitude as a string (per Nominatim response schema). */
  lat: string;

  /** Longitude as a string (per Nominatim response schema). */
  lon: string;
};

export default function LocationSearchBar({
  onSelect,
  placeholder = "Search location",
  buttonLabel = "Search",
  minChars = 3,
}: LocationSearchBarProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const doSearch = async () => {
    const q = query.trim();
    if (q.length < minChars) {
      setError(`Please enter at least ${minChars} characters.`);
      return;
    }

    // Abort prior request
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      setIsLoading(true);
      setError(null);

      const url =
        `https://nominatim.openstreetmap.org/search?` +
        new URLSearchParams({
          q,
          format: "json",
          addressdetails: "0",
          limit: "1", // best match only
        }).toString();

      const resp = await fetch(url, {
        method: "GET",
        signal: controller.signal,
        headers: { Accept: "application/json" },
      });

      if (!resp.ok) {
        throw new Error(`Geocoder error: ${resp.status} ${resp.statusText}`);
      }

      const data = (await resp.json()) as NominatimResult[];
      if (controller.signal.aborted) return;

      if (!data.length) {
        setError("No results found.");
        return;
      }

      const best = data[0];
      const lat = Number(best.lat);
      const lng = Number(best.lon);

      if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        setError("Invalid coordinates returned by geocoder.");
        return;
      }

      onSelect({ lat, lng }, best.displayName);
    } catch (e) {
      if (controller.signal.aborted) return;
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (!controller.signal.aborted) setIsLoading(false);
    }
  };

  return (
    <div style={styles.wrap}>
      <div style={styles.row}>
        <input
          type="text"
          value={query}
          placeholder={placeholder}
          onChange={(e) => setQuery(e.target.value)}
          style={styles.input}
          aria-label="Location search"
          onKeyDown={(e) => {
            if (e.key === "Enter") void doSearch();
          }}
        />

        <button
          type="button"
          onClick={() => void doSearch()}
          disabled={isLoading}
          style={{
            ...styles.searchBtn,
            ...(isLoading ? styles.searchBtnDisabled : null),
          }}
        >
          {isLoading ? "…" : buttonLabel}
        </button>
      </div>

      {error ? <div style={styles.error}>{error}</div> : null}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    marginBottom: 10,
  },
  row: {
    display: "flex",
    gap: 8,
    alignItems: "center",
  },
  input: {
    flex: 1,
    height: 30,
    padding: "0 10px",
    borderRadius: 8,
    border: "1px solid rgba(0,0,0,0.25)",
    outline: "none",
    fontSize: 10,
  },
  searchBtn: {
    height: 30,
    padding: "0 10px",
    borderRadius: 8,
    border: "1px solid rgba(0,0,0,0.25)",
    background: "#fff",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 10,
  },
  searchBtnDisabled: {
    cursor: "not-allowed",
    opacity: 0.7,
  },
  error: {
    marginTop: 6,
    fontSize: 12,
    color: "rgba(180, 0, 0, 0.9)",
  },
};
