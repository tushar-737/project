/** Leaflet stub used by vitest (jsdom cannot run the real Leaflet). */
export default {
  divIcon: () => ({ _stub: true }),
  map: () => ({ remove: () => {}, flyTo: () => {}, fitBounds: () => {}, on: () => {} }),
  marker: () => ({ addTo: () => {}, remove: () => {} }),
  tileLayer: () => ({ addTo: () => {} }),
};
