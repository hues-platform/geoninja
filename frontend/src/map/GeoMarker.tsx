/**
 * Map marker component.
 *
 * Responsibilities:
 * - Listens for map clicks and emits a `(lat,lng)` position via `setMarker`.
 * - Renders a Leaflet `Marker` at the current `marker` location.
 *
 * Note:
 * Leaflet’s default marker icon assets need explicit imports in many bundlers
 * (including Vite) to avoid missing icon URLs.
 */

import { Marker, useMapEvents } from "react-leaflet";
import type { LatLngLiteral } from "leaflet";
import L from "leaflet";
import type { LatLng } from "../types/params";

// Fix leaflet marker issue
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

// Component for displaying and setting a location marker on the map
export type GeoMarkerProps = {
  marker: LatLng | null;
  setMarker: (pos: LatLng) => void;
};

// Define a custom icon for the marker
const geoMarkerIcon = L.icon({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [20, 32],
  iconAnchor: [10, 35],
  popupAnchor: [1, -34],
  shadowSize: [0, 0],
});

// Component for displaying and setting a location marker on the map
export default function GeoMarker({ marker, setMarker }: GeoMarkerProps) {
  // Handle map click events to set marker position
  useMapEvents({
    click(e) {
      setMarker({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });

  // If no marker is set, render nothing
  if (!marker) return null;

  // Render the marker at the specified position
  const position: LatLngLiteral = { lat: marker.lat, lng: marker.lng };
  return <Marker position={position} icon={geoMarkerIcon} />;
}
