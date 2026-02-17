/**
 * Coordinate navigator input.
 *
 * Small helper used by the control panel to let users jump to a map location
 * by typing latitude/longitude.
 *
 * Behavior:
 * - Accepts plain numeric input (no degree symbols).
 * - Validates ranges: latitude ∈ [-90, 90], longitude ∈ [-180, 180].
 * - Submits on Enter in either input or via the button.
 */
import { useState } from "react";

export type CoordinateNavigatorProps = {
  /** Called with `(lat, lon)` when both inputs validate. */
  onGo: (latitude: number, longitude: number) => void;

  /** Optional label for the submit button. */
  buttonLabel?: string;

  /** Placeholder for the latitude input. */
  latPlaceholder?: string;

  /** Placeholder for the longitude input. */
  lonPlaceholder?: string;
};

function parseNumber(s: string): number | null {
  /** Parse a user-typed number; returns `null` for empty/non-finite input. */
  const t = s.trim();
  if (!t) return null;
  const v = Number(t);
  return Number.isFinite(v) ? v : null;
}

export default function CoordinateNavigator({
  onGo,
  buttonLabel = "Go",
  latPlaceholder = "Latitude",
  lonPlaceholder = "Longitude",
}: CoordinateNavigatorProps) {
  const [latInput, setLatInput] = useState("");
  const [lonInput, setLonInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    const lat = parseNumber(latInput);
    const lon = parseNumber(lonInput);

    if (lat === null || lon === null) {
      setError("Please enter valid numeric values for latitude and longitude.");
      return;
    }
    if (lat < -90 || lat > 90) {
      setError("Latitude must be between -90 and 90.");
      return;
    }
    if (lon < -180 || lon > 180) {
      setError("Longitude must be between -180 and 180.");
      return;
    }

    setError(null);
    onGo(lat, lon);
  };

  return (
    <div style={styles.wrap}>
      <div style={styles.row}>
        <input
          type="text"
          value={latInput}
          onChange={(e) => setLatInput(e.target.value)}
          placeholder={latPlaceholder}
          style={styles.input}
          aria-label="Latitude"
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
        />
        <input
          type="text"
          value={lonInput}
          onChange={(e) => setLonInput(e.target.value)}
          placeholder={lonPlaceholder}
          style={styles.input}
          aria-label="Longitude"
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
        />
        <button type="button" onClick={submit} style={styles.btn}>
          {buttonLabel}
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
    gap: 6,
    alignItems: "center",
  },
  input: {
    flex: 1,
    minWidth: 0,
    height: 30,
    padding: "0 8px",
    borderRadius: 8,
    border: "1px solid rgba(0,0,0,0.25)",
    outline: "none",
    fontSize: 10,
  },
  btn: {
    height: 30,
    padding: "0 10px",
    borderRadius: 8,
    border: "1px solid rgba(0,0,0,0.25)",
    background: "#fff",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 10,
  },
  error: {
    marginTop: 6,
    fontSize: 12,
    color: "rgba(180, 0, 0, 0.9)",
  },
};
