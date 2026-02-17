/**
 * Base-layer dispatcher.
 *
 * Selects a base layer component from `baseLayerRegistry` and renders it.
 */
import { baseLayerRegistry, type BaseLayerId } from "./baseLayerRegistry";

export default function BaseLayer({ id, active }: { id: BaseLayerId; active?: boolean }) {
  const Layer = baseLayerRegistry[id].Component;
  return <Layer active={active} />;
}
