
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import {McpServer} from '@modelcontextprotocol/sdk/server/mcp.js';
import {Transport} from '@modelcontextprotocol/sdk/shared/transport.js';
import {z} from 'zod';

// --- DATA STRUCTURES ---

export interface ActionItem {
  id: string;
  icon: string;
  title: string;
  measures: string[];
  cost: number;
  timeline: string;
  type: 'Mitigation' | 'Adaptation';
}

export interface ContextTensor {
  dimensions: {
    climate: { temp: number; precip: number; extremeEvents: number }; // 0-100 normalized
    geography: { elevation: number; landUse: 'Urban' | 'Rural' | 'Suburban' | 'Waterbody'; coastal: boolean; waterBody: boolean };
    socio: { popDensity: number; gdpIndex: number };
    infrastructure: { roadDensity: number; waterAccess: number };
    vulnerability: { socialIndex: number; governance: number };
  };
  scores: {
    hazard: number;
    exposure: number;
    vulnerability: number;
    totalRisk: number; // Hazard * Exposure * Vulnerability
  };
}

export interface H3Cell {
  id: string; // Simulated H3 Index
  center: { lat: number; lng: number };
  boundary: { lat: number; lng: number; altitude: number }[];
  tensor: ContextTensor;
  actions: ActionItem[]; // Top 3 recommended actions for this specific cell
}

export interface GridAnalysis {
  regionName: string;
  scenario: string;
  year: number;
  scale: string;
  cells: H3Cell[];
  gridCenter: { lat: number; lng: number };
  globalStats: {
    avgRisk: number;
    affectedPopulation: number;
    totalCost: number;
  };
}

export interface MapParams {
  location?: string;
  origin?: string;
  destination?: string;
  gridAnalysis?: GridAnalysis;
}

// --- ACTION DATABASE SIMULATION ---

const ACTION_DB: ActionItem[] = [
  { id: 'ADAPT-001', type: 'Adaptation', icon: '🌊', title: 'Coastal Defense System', measures: ['Mangrove restoration', 'Sea walls construction'], cost: 5000000, timeline: '2-5 Years' },
  { id: 'ADAPT-002', type: 'Adaptation', icon: '🚰', title: 'Drought Resilience', measures: ['Community boreholes', 'Drip irrigation subsidies'], cost: 200000, timeline: '6-12 Months' },
  { id: 'ADAPT-003', type: 'Adaptation', icon: '❄️', title: 'Heat Action Plan', measures: ['Cool roofing retrofits', 'Public cooling centers'], cost: 150000, timeline: '0-6 Months' },
  { id: 'MITIG-001', type: 'Mitigation', icon: '⚡', title: 'Grid Decentralization', measures: ['Solar micro-grids', 'Battery storage units'], cost: 1200000, timeline: '1-3 Years' },
  { id: 'ADAPT-004', type: 'Adaptation', icon: '🌾', title: 'Food Security Net', measures: ['Strategic grain reserves', 'Cash transfer program'], cost: 800000, timeline: '0-3 Months' },
  { id: 'ADAPT-005', type: 'Adaptation', icon: '🏙️', title: 'Urban Flood Mgmt', measures: ['Permeable pavement', 'Canal dredging'], cost: 3000000, timeline: '2-4 Years' },
  { id: 'ADAPT-006', type: 'Adaptation', icon: '🌳', title: 'Reforestation Buffer', measures: ['Planting native species', 'Soil erosion control'], cost: 450000, timeline: '1-5 Years' },
  { id: 'MITIG-002', type: 'Mitigation', icon: '🚤', title: 'Water Transport Upgrade', measures: ['Electric ferries', 'Canal logistics'], cost: 1000000, timeline: '1-3 Years' }
];

// --- MATH & GEOMETRY HELPERS ---

// Basic Pseudo-Random Noise
function pseudoNoise(x: number, y: number, seed: number = 1): number {
  return (Math.sin(x * 12.9898 + y * 78.233) * 43758.5453 + seed) % 1;
}

// Regular Hexagon Boundary Generator (Restored for Stability)
function getHexagonBoundary(centerLat: number, centerLng: number, radiusMeters: number): { lat: number; lng: number; altitude: number }[] {
  const coords = [];
  const R = 6378137; // Earth radius
  
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i; // 60 degrees in radians
    
    const dLat = (radiusMeters / R) * (180 / Math.PI) * Math.sin(angle);
    const dLng = (radiusMeters / (R * Math.cos((Math.PI * centerLat) / 180))) * (180 / Math.PI) * Math.cos(angle);
    
    coords.push({ lat: centerLat + dLat, lng: centerLng + dLng, altitude: 0 });
  }
  coords.push(coords[0]); // Close loop
  return coords;
}

// Generate a Rectangular Grid (better for screens) based on lat/lng bbox
async function generateRectangularHexGrid(location: string, scale: string): Promise<{cells: {lat: number, lng: number}[], center: {lat:number, lng:number}}> {
  
  const MOCK_LOCATIONS: {[key:string]: {lat: number, lng: number}} = {
    "jakarta": {lat: -6.2088, lng: 106.8456},
    "lagos": {lat: 6.5244, lng: 3.3792},
    "rotterdam": {lat: 51.9225, lng: 4.47917},
    "netherlands": {lat: 52.1326, lng: 5.2913}, // Centroid
    "phoenix": {lat: 33.4484, lng: -112.0740},
    "dhaka": {lat: 23.8103, lng: 90.4125},
    "new york": {lat: 40.7128, lng: -74.0060},
    "london": {lat: 51.5074, lng: -0.1278},
    "paris": {lat: 48.8566, lng: 2.3522},
    "tokyo": {lat: 35.6762, lng: 139.6503},
    "sydney": {lat: -33.8688, lng: 151.2093},
    "berlin": {lat: 52.5200, lng: 13.4050},
    "munich": {lat: 48.1351, lng: 11.5820},
    "rio": {lat: -22.9068, lng: -43.1729},
    "cairo": {lat: 30.0444, lng: 31.2357},
    "mumbai": {lat: 19.0760, lng: 72.8777},
    "hamburg": {lat: 53.5511, lng: 9.9937},
    "singapore": {lat: 1.3521, lng: 103.8198},
    "dubai": {lat: 25.2048, lng: 55.2708},
    "istanbul": {lat: 41.0082, lng: 28.9784},
    "shanghai": {lat: 31.2304, lng: 121.4737},
    "los angeles": {lat: 34.0522, lng: -118.2437},
    "buenos aires": {lat: -34.6037, lng: -58.3816},
    "mexico city": {lat: 19.4326, lng: -99.1332},
    "bangkok": {lat: 13.7563, lng: 100.5018},
    "seoul": {lat: 37.5665, lng: 126.9780}
  };
  
  const key = Object.keys(MOCK_LOCATIONS).find(k => location.toLowerCase().includes(k));
  // Default to a generic location if not found, but we really rely on geocoding in a real app.
  const center = key ? MOCK_LOCATIONS[key] : {lat: -6.2088, lng: 106.8456}; 
  
  // GRANULARITY SETTINGS
  let radius = 250; 
  let gridWidth = 20;
  let gridHeight = 20;

  if (scale === 'neighborhood') { radius = 60; gridWidth = 28; gridHeight = 28; } // Denser, finer for detailed view
  if (scale === 'city') { radius = 180; gridWidth = 24; gridHeight = 24; } // Balanced city view
  if (scale === 'region') { radius = 1200; gridWidth = 18; gridHeight = 18; } // Overview

  const points = [];
  const R = 6378137;

  const dx = radius * Math.sqrt(3);
  const dy = radius * 1.5; 

  for (let r = -gridHeight; r <= gridHeight; r++) {
    for (let q = -gridWidth; q <= gridWidth; q++) {
      
      const yOffset = r * dy;
      // Offset every other row
      const xOffset = q * dx + (Math.abs(r) % 2) * (dx / 2);

      const dLat = (yOffset / R) * (180 / Math.PI);
      const dLng = (xOffset / (R * Math.cos((Math.PI * center.lat) / 180))) * (180 / Math.PI);

      points.push({lat: center.lat + dLat, lng: center.lng + dLng});
    }
  }

  return {cells: points, center};
}

// --- PROCEDURAL CONTEXT ENGINE ---

function fractalNoise(lat: number, lng: number, octaves: number): number {
  let value = 0;
  let amplitude = 0.5;
  let frequency = 100; 
  
  for (let i = 0; i < octaves; i++) {
    const n = Math.abs(Math.sin(lat * frequency) * Math.cos(lng * frequency));
    value += n * amplitude;
    amplitude *= 0.5;
    frequency *= 2;
  }
  return value;
}

function generateContextTensor(lat: number, lng: number, centerLat: number, centerLng: number, scale: string): ContextTensor {
  
  // Radial distance from center (simulates city center)
  const distDeg = Math.sqrt(Math.pow(lat - centerLat, 2) + Math.pow(lng - centerLng, 2));
  let scaleFactor = 0.05;
  if (scale === 'neighborhood') scaleFactor = 0.01;
  if (scale === 'region') scaleFactor = 0.2;
  
  // Normalized distance (0 at center, 1 at edge)
  const normalizedDist = Math.min(1, distDeg / scaleFactor);
  
  // 1. Terrain/Water Generation (Fractal Noise)
  // Low frequency noise for major features (Coasts)
  const macroNoise = fractalNoise(lat, lng, 2);
  // High frequency for detail (Rivers)
  const microNoise = fractalNoise(lat + 0.5, lng + 0.5, 4);
  
  // River simulation: Areas where noise is very close to a specific value (e.g. 0.5)
  const isRiver = Math.abs(microNoise - 0.5) < 0.02;
  // Coast/Ocean simulation: Areas below a threshold
  const isOcean = macroNoise < 0.25;
  
  const isWaterBody = isOcean || isRiver;

  // 2. Urban Density (Radial + Noise)
  const densityNoise = pseudoNoise(lat, lng, 50);
  // Probability decreases with distance, perturbed by noise
  const urbanProbability = (1 - normalizedDist) * 0.8 + (densityNoise * 0.2);
  
  let landUse: 'Urban' | 'Suburban' | 'Rural' | 'Waterbody' = 'Rural';
  
  if (isWaterBody) {
    landUse = 'Waterbody';
  } else if (urbanProbability > 0.6) {
    landUse = 'Urban';
  } else if (urbanProbability > 0.3) {
    landUse = 'Suburban';
  } else {
    landUse = 'Rural';
  }

  // 3. Socio-Economic Factors
  let popDensity = 0;
  let infrastructure = 0;
  
  switch(landUse) {
    case 'Urban':
      popDensity = 90 + (densityNoise * 10); 
      infrastructure = 90 + (densityNoise * 10);
      break;
    case 'Suburban':
      popDensity = 50 + (densityNoise * 20); 
      infrastructure = 60 + (densityNoise * 15);
      break;
    case 'Rural':
      popDensity = 10 + (densityNoise * 10); 
      infrastructure = 30 + (densityNoise * 10);
      break;
    case 'Waterbody':
      popDensity = 0;
      infrastructure = 10; // Ports?
      break;
  }

  // 4. Climate Base (Latitude Dependent)
  const absLat = Math.abs(lat);
  let baseTemp = 20; 
  if (absLat < 23) baseTemp = 30; // Tropical
  else if (absLat > 60) baseTemp = 5; // Polar
  if (landUse === 'Urban') baseTemp += 3; // Heat island
  
  // 5. Risk Calculation
  let hazard = 30;
  if (isWaterBody) hazard += 40; // Flood risk inherent in water cells
  if (isRiver) hazard += 20; // River banks
  if (landUse === 'Urban') hazard += 10; // Heat/Flash flood
  if (absLat < 10) hazard += 10; // Tropical storms

  // Exposure is high where people/infra are
  const exposure = (popDensity + infrastructure) / 2;
  
  // Vulnerability is inverse of infrastructure (simplified)
  const vulnerability = Math.max(10, 100 - (infrastructure * 0.7));
  
  const rawRisk = (hazard * exposure * vulnerability) / 10000;
  let totalRisk = Math.min(100, Math.pow(rawRisk, 0.6) * 100);
  
  // Flatten risk for pure water bodies (unless we care about shipping lanes, but usually low impact for adaptation)
  if (landUse === 'Waterbody') totalRisk = 15; 

  return {
    dimensions: {
      climate: { temp: baseTemp, precip: 50 + (macroNoise * 20), extremeEvents: hazard },
      geography: { elevation: isWaterBody ? 0 : 10 + (macroNoise * 50), landUse, coastal: isOcean, waterBody: isWaterBody },
      socio: { popDensity, gdpIndex: infrastructure },
      infrastructure: { roadDensity: infrastructure, waterAccess: infrastructure },
      vulnerability: { socialIndex: vulnerability, governance: 50 }
    },
    scores: {
      hazard,
      exposure,
      vulnerability,
      totalRisk
    }
  };
}

function selectActions(tensor: ContextTensor): ActionItem[] {
  const actions: ActionItem[] = [];
  
  if (tensor.dimensions.geography.waterBody) {
      actions.push(ACTION_DB.find(a => a.id === 'MITIG-002')!); 
      actions.push(ACTION_DB.find(a => a.id === 'ADAPT-005')!); 
  } else {
    if (tensor.scores.totalRisk > 70) {
       actions.push(ACTION_DB.find(a => a.id === 'ADAPT-001')!); 
       actions.push(ACTION_DB.find(a => a.id === 'ADAPT-005')!); 
    }
    if (tensor.dimensions.geography.landUse === 'Rural') {
        actions.push(ACTION_DB.find(a => a.id === 'ADAPT-006')!); 
        actions.push(ACTION_DB.find(a => a.id === 'ADAPT-004')!); 
    } else if (tensor.dimensions.geography.landUse === 'Urban') {
        actions.push(ACTION_DB.find(a => a.id === 'ADAPT-003')!); 
        actions.push(ACTION_DB.find(a => a.id === 'MITIG-001')!); 
    }
  }
  return [...new Set(actions)].slice(0, 3);
}

// --- SERVER SETUP ---

export async function startMcpGoogleMapServer(
  transport: Transport,
  mapQueryHandler: (params: MapParams) => void,
) {
  const server = new McpServer({
    name: 'Context Space Engine',
    version: '2.1.0',
  });

  server.tool(
    'view_location_google_maps',
    'View a location',
    {query: z.string()},
    async ({query}) => {
      mapQueryHandler({location: query});
      return {content: [{type: 'text', text: `Viewing ${query}`}]};
    },
  );

  server.tool(
    'directions_on_google_maps',
    'Get directions',
    {origin: z.string(), destination: z.string()},
    async ({origin, destination}) => {
      mapQueryHandler({origin, destination});
      return {content: [{type: 'text', text: `Routing...`}]};
    },
  );

  server.tool(
    'analyze_context_space',
    'Generate a granular Discrete Global Grid (H3) risk analysis.',
    {
      region_name: z.string(),
      year_offset: z.number().default(5),
      scenario: z.string().default('SSP2-4.5'),
      scale: z.enum(['neighborhood', 'city', 'region']).default('city').describe('The granularity of the analysis.')
    },
    async ({region_name, year_offset, scenario, scale}) => {
      
      const gridData = await generateRectangularHexGrid(region_name, scale);
      
      let hexRadius = 250;
      if (scale === 'neighborhood') hexRadius = 60; // Very fine granularity
      if (scale === 'city') hexRadius = 180; // Fine city granularity
      if (scale === 'region') hexRadius = 1200; // Large region

      const cells: H3Cell[] = gridData.cells.map((pt, i) => {
        const tensor = generateContextTensor(pt.lat, pt.lng, gridData.center.lat, gridData.center.lng, scale);
        const actions = selectActions(tensor);
        
        // Using standard hexagon for stability
        const boundary = getHexagonBoundary(pt.lat, pt.lng, hexRadius * 0.95);

        return {
          id: `h3-${region_name.substring(0,3)}-${i}`,
          center: pt, 
          boundary, 
          tensor,
          actions
        };
      });
      
      const landCells = cells.filter(c => c.tensor.dimensions.geography.landUse !== 'Waterbody');
      const totalRisk = landCells.reduce((acc, c) => acc + c.tensor.scores.totalRisk, 0);
      const avgRisk = landCells.length > 0 ? totalRisk / landCells.length : 0;
      const totalPop = Math.floor(cells.reduce((acc, c) => acc + (c.tensor.dimensions.socio.popDensity * 100), 0));
      const totalCost = cells.reduce((acc, c) => acc + (c.tensor.scores.totalRisk * 1000), 0);

      const highRiskCells = landCells.filter(c => c.tensor.scores.totalRisk > 75).length;
      const dominantLandUse = landCells.filter(c => c.tensor.dimensions.geography.landUse === 'Urban').length > landCells.length / 2 ? 'Urban' : 'Rural';
      
      // RICH SUMMARY FOR LLM
      const analysisSummary = `
      CONTEXT SPACE GENERATED FOR ${region_name.toUpperCase()} (${scale} scale)
      ------------------------------------------------
      SCENARIO: ${scenario} (+${year_offset} years)
      
      AGGREGATE STATS:
      - Average Risk Score: ${avgRisk.toFixed(1)} / 100
      - High Risk Cells (>75): ${highRiskCells}
      - Est. Affected Population: ${(totalPop/1000).toFixed(1)}k
      - Est. Adaptation Cost: €${(totalCost/1000000).toFixed(1)}M
      
      SPATIAL INSIGHTS:
      - Dominant Land Use: ${dominantLandUse}
      - Spatial Risk Distribution: Risk is highest in dense urban sectors and low-lying areas.
      - Vulnerability Drivers: Infrastructure gaps in suburban fringes are increasing exposure.
      
      The visual grid has been rendered on the map. Use the information above to provide a detailed analysis to the user.
      `;

      const analysis: GridAnalysis = {
        regionName: region_name,
        scenario,
        year: new Date().getFullYear() + year_offset,
        scale,
        cells,
        gridCenter: gridData.center, // Critical for Client sync
        globalStats: {
          avgRisk: avgRisk,
          affectedPopulation: totalPop,
          totalCost: totalCost
        }
      };

      mapQueryHandler({
        location: region_name, 
        gridAnalysis: analysis
      });

      return {
        content: [{type: 'text', text: analysisSummary}]
      };
    }
  );

  await server.connect(transport);
  console.log('Context Space Server running');
}
