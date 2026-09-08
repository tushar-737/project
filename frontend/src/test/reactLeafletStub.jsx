/* react-leaflet stub - renders plain <div> placeholders in jsdom tests. */
import React from 'react';

const wrap =
  (tag) =>
  ({ children, ...rest }) =>
    React.createElement(tag, { 'data-stub': '1', ...rest }, children);

export const MapContainer = wrap('div');
export const TileLayer = () => null;
export const Marker = ({ children }) => React.createElement('div', { 'data-role': 'marker' }, children);
export const CircleMarker = () => null;
export const Polyline = () => null;
export const Popup = ({ children }) => React.createElement('div', { 'data-role': 'popup' }, children);
export const Tooltip = () => null;
export const useMap = () => ({ flyTo: () => {}, openPopup: () => {} });
export const useMapEvents = () => null;
