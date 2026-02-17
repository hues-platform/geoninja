/**
 * Satellite imagery base layer.
 *
 * Wrapped in a `LayersControl.BaseLayer` so users can switch basemaps.
 */
import { LayersControl, TileLayer } from "react-leaflet";

export default function SatBaseLayer({ active }: { active?: boolean }) {
  return (
    <LayersControl.BaseLayer checked={active} name="Satellite Imagery">
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and others"
      />
    </LayersControl.BaseLayer>
  );
}
