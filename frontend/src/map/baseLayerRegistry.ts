/**
 * Base layer registry.
 *
 * Central place to define available basemaps (OSM, satellite, …) and their
 * Leaflet `LayersControl.BaseLayer` components.
 */

import OsmBaseLayer from "./layers/OsmBaseLayer";
import SatBaseLayer from "./layers/SatBaseLayer";

export type BaseLayerId = "osm" | "sat";

export interface BaseLayerProps {
  /** Passed through to `LayersControl.BaseLayer.checked`. */
  active?: boolean;
}

export interface BaseLayerDefinition {
  id: BaseLayerId;
  name: string;
  Component: React.ComponentType<BaseLayerProps>;
}

export const baseLayerRegistry: Record<BaseLayerId, BaseLayerDefinition> = {
  osm: {
    id: "osm",
    name: "OpenStreetMap",
    Component: OsmBaseLayer,
  },
  sat: {
    id: "sat",
    name: "Satellite",
    Component: SatBaseLayer,
  },
};
