/** Risk vocabulary shared by UI helpers (colors, labels, thresholds). */

export const RISK_LEVELS = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'];

export const RISK_META = {
  LOW: { color: '#22c55e', bg: 'bg-emerald-100', text: 'text-emerald-700', ring: 'ring-emerald-300', label: 'Low' },
  MODERATE: { color: '#eab308', bg: 'bg-yellow-100', text: 'text-yellow-800', ring: 'ring-yellow-300', label: 'Moderate' },
  HIGH: { color: '#f97316', bg: 'bg-orange-100', text: 'text-orange-800', ring: 'ring-orange-300', label: 'High' },
  CRITICAL: { color: '#dc2626', bg: 'bg-red-100', text: 'text-red-700', ring: 'ring-red-300', label: 'Critical' },
};

export const ROAD_META = {
  OPEN: { color: '#16a34a', bg: 'bg-green-100', text: 'text-green-700', label: 'Open' },
  HIGH_RISK: { color: '#f97316', bg: 'bg-orange-100', text: 'text-orange-800', label: 'High Risk' },
  PARTIALLY_BLOCKED: { color: '#eab308', bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Partially Blocked' },
  BLOCKED: { color: '#dc2626', bg: 'bg-red-100', text: 'text-red-700', label: 'Blocked' },
};

export const PRIORITY_META = {
  'PRIORITY 1': { color: '#dc2626', bg: 'bg-red-100', text: 'text-red-700', desc: 'Immediate response' },
  'PRIORITY 2': { color: '#f97316', bg: 'bg-orange-100', text: 'text-orange-800', desc: 'Urgent response' },
  'PRIORITY 3': { color: '#eab308', bg: 'bg-yellow-100', text: 'text-yellow-800', desc: 'Monitoring required' },
};

export const SCENARIOS = ['NORMAL', 'MODERATE_RAIN', 'HEAVY_RAIN', 'EXTREME_RAIN'];

export const SCENARIO_META = {
  NORMAL: { icon: '🌤️', desc: 'Normal weather', grad: 'from-sky-500 to-cyan-400' },
  MODERATE_RAIN: { icon: '🌦️', desc: 'Moderate rain', grad: 'from-amber-400 to-yellow-500' },
  HEAVY_RAIN: { icon: '🌧️', desc: 'Heavy rain', grad: 'from-orange-500 to-red-500' },
  EXTREME_RAIN: { icon: '⛈️', desc: 'Extreme rain', grad: 'from-red-600 to-purple-700' },
};

export const REPORT_TYPES = [
  'LANDSLIDE',
  'ROAD_BLOCKAGE',
  'ROAD_CRACK',
  'SLOPE_CRACK',
  'SLOPE_MOVEMENT',
  'ROCKFALL',
  'FLOODING',
  'OTHER',
];

export const REPORT_TYPE_META = {
  LANDSLIDE: { icon: '🪨', label: 'Landslide' },
  ROAD_BLOCKAGE: { icon: '🚧', label: 'Road blockage' },
  ROAD_CRACK: { icon: '🕳️', label: 'Road crack' },
  SLOPE_CRACK: { icon: '📐', label: 'Slope crack' },
  SLOPE_MOVEMENT: { icon: '🔻', label: 'Slope movement' },
  ROCKFALL: { icon: '⛰️', label: 'Rockfall' },
  FLOODING: { icon: '🌊', label: 'Flooding' },
  OTHER: { icon: '📋', label: 'Other' },
};

export const STATES = [
  'Assam',
  'Arunachal Pradesh',
  'Meghalaya',
  'Manipur',
  'Mizoram',
  'Nagaland',
  'Tripura',
  'Sikkim',
];

/** Deterministic risk colors for charts (Recharts cells). */
export const levelColor = (level) => RISK_META[level]?.color || '#64748b';
