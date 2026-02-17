/**
 * OpenStreetMap base layer.
 *
 * Wrapped in a `LayersControl.BaseLayer` so users can switch basemaps.
 */
import { LayersControl, TileLayer } from "react-leaflet";

export default function OsmBaseLayer({ active }: { active?: boolean }) {
  return (
    <LayersControl.BaseLayer checked={active} name="OpenStreetMap">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
    </LayersControl.BaseLayer>
  );
}
