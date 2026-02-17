/**
 * Camera follow behavior for search-driven marker updates.
 *
 * When the marker is set via a search interaction (text search or coordinate
 * entry), this component pans the map to the marker while keeping the current
 * zoom level.
 *
 * Marker changes from direct map clicks are intentionally ignored to avoid
 * “jumping” the view while the user is exploring.
 */

import { useEffect } from "react";
import { useMap } from "react-leaflet";
import { useAppStore } from "../process/appStore";

export default function MapCameraFollower() {
  const map = useMap();

  const marker = useAppStore((state) => state.marker);
  const markerRevision = useAppStore((state) => state.markerRevision);
  const lastMarkerChange = useAppStore((state) => state.lastMarkerChange);

  useEffect(() => {
    if (!marker) return;
    if (!lastMarkerChange) return;
    const { source } = lastMarkerChange;
    if (source != "searchText" && source != "searchCoords") return;

    const currentZoom = map.getZoom();

    // Keep zoom, move center to marker
    map.setView([marker.lat, marker.lng], currentZoom, { animate: true });
  }, [marker, markerRevision, lastMarkerChange, map]);

  return null;
}
