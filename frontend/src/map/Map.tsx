/**
 * Leaflet map container.
 *
 * Renders the interactive map and wires it to the app store:
 * - base layer controls (OSM + satellite)
 * - a click-to-set marker (`GeoMarker`)
 * - camera-follow behavior for search-driven marker changes (`MapCameraFollower`)
 */

import { MapContainer, LayersControl } from "react-leaflet";
import GeoMarker from "../map/GeoMarker";
import { useAppStore } from "../process/appStore";
import BaseLayer from "../map/BaseLayer";
import type { BaseLayerId } from "../map/baseLayerRegistry";
import MapCameraFollower from "../map/MapCameraFollower";

const DEFAULT_CENTER: [number, number] = [47.37, 8.54]; // Zurich
const DEFAULT_ZOOM = 5; // Continent-wide scale
const WORLD_COPY_JUMP = true;
const MAP_STYLE: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  zIndex: 0,
};
const DEFAULT_BASE_LAYER: BaseLayerId = "osm";

export default function Map() {
  const marker = useAppStore((s) => s.marker);
  const setMarker = useAppStore((s) => s.setMarker);

  // Render the Leaflet map with base layer controls
  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      worldCopyJump={WORLD_COPY_JUMP}
      style={MAP_STYLE}
    >
      <LayersControl position="bottomright">
        <BaseLayer id="osm" active={DEFAULT_BASE_LAYER === "osm"} />
        <BaseLayer id="sat" active={DEFAULT_BASE_LAYER === "sat"} />
      </LayersControl>
      <GeoMarker marker={marker} setMarker={setMarker} />
      <MapCameraFollower />
    </MapContainer>
  );
}
