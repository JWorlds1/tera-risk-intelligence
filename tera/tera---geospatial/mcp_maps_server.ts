
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import {McpServer} from '@modelcontextprotocol/sdk/server/mcp.js';
import {Transport} from '@modelcontextprotocol/sdk/shared/transport.js';
import {z} from 'zod';
import {h3ToGeoBoundary, geoToH3, kRing, getResolution, cellToLatLng} from 'h3-js';

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
  id: string; // Real H3 Index
  h3Index: string; // H3 hexagon index
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

// Get H3 hexagon boundary using h3-js library
function getH3HexagonBoundary(h3Index: string): { lat: number; lng: number; altitude: number }[] {
  const boundary = h3ToGeoBoundary(h3Index, true); // true = geoJson format (lat, lng)
  return boundary.map(coord => ({
    lat: coord[0],
    lng: coord[1],
    altitude: 0
  }));
}

// Get H3 resolution based on scale
function getH3Resolution(scale: string): number {
  switch (scale) {
    case 'neighborhood': return 10; // ~80m hexagons
    case 'city': return 9; // ~250m hexagons
    case 'region': return 7; // ~1.5km hexagons
    default: return 9;
  }
}

// Generate H3 Grid using real H3 library
async function generateH3Grid(location: string, scale: string): Promise<{cells: {h3Index: string, lat: number, lng: number}[], center: {lat:number, lng:number}}> {
  
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
    "mumbai": {lat: 19.0760, lng: 72.8777}
  };
  
  const key = Object.keys(MOCK_LOCATIONS).find(k => location.toLowerCase().includes(k));
  const center = key ? MOCK_LOCATIONS[key] : {lat: -6.2088, lng: 106.8456}; 
  
  const resolution = getH3Resolution(scale);
  
  // Get center H3 index
  const centerH3Index = geoToH3(center.lat, center.lng, resolution);
  
  // Determine ring size based on scale
  let ringSize = 10;
  if (scale === 'neighborhood') ringSize = 12;
  if (scale === 'city') ringSize = 10;
  if (scale === 'region') ringSize = 8;
  
  // Get all H3 indices in k-ring around center
  const h3Indices = kRing(centerH3Index, ringSize);
  
  // Convert H3 indices to lat/lng coordinates
  const cells = h3Indices.map(h3Index => {
    const [lat, lng] = cellToLatLng(h3Index);
    return { h3Index, lat, lng };
  });

  return {cells, center};
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
  
  const distDeg = Math.sqrt(Math.pow(lat - centerLat, 2) + Math.pow(lng - centerLng, 2));
  let scaleFactor = 0.05;
  if (scale === 'neighborhood') scaleFactor = 0.01;
  if (scale === 'region') scaleFactor = 0.2;
  
  const normalizedDist = Math.min(1, distDeg / scaleFactor);
  
  const terrainNoise = fractalNoise(lat, lng, 4); 
  const isWaterBody = terrainNoise < 0.2; 
  
  const densityNoise = pseudoNoise(lat, lng, 50);
  const urbanProbability = (1 - normalizedDist) + (densityNoise * 0.3);
  
  let landUse: 'Urban' | 'Suburban' | 'Rural' | 'Waterbody' = 'Rural';
  
  if (isWaterBody) {
    landUse = 'Waterbody';
  } else if (urbanProbability > 0.6) {
    landUse = 'Urban';
  } else if (urbanProbability > 0.25) {
    landUse = 'Suburban';
  } else {
    landUse = 'Rural';
  }

  const absLat = Math.abs(lat);
  let baseTemp = 20; 
  if (absLat < 23) baseTemp = 30; 
  else if (absLat > 60) baseTemp = 5; 
  if (landUse === 'Urban') baseTemp += 3;
  
  let popDensity = 0;
  let infrastructure = 0;
  
  switch(landUse) {
    case 'Urban':
      popDensity = 80 + (densityNoise * 20); 
      infrastructure = 85 + (densityNoise * 15);
      break;
    case 'Suburban':
      popDensity = 40 + (densityNoise * 30); 
      infrastructure = 60 + (densityNoise * 20);
      break;
    case 'Rural':
      popDensity = 5 + (densityNoise * 15); 
      infrastructure = 20 + (densityNoise * 20);
      break;
    case 'Waterbody':
      popDensity = 0;
      infrastructure = 5; 
      break;
  }

  let hazard = 30;
  if (isWaterBody) hazard += 50; 
  if (landUse === 'Urban') hazard += 10; 
  if (absLat < 10) hazard += 10; 

  const exposure = (popDensity + infrastructure) / 2;
  const vulnerability = Math.max(0, 100 - (infrastructure * 0.8));
  
  const rawRisk = (hazard * exposure * vulnerability) / 10000;
  let totalRisk = Math.min(100, Math.pow(rawRisk, 0.7) * 100);
  
  if (landUse === 'Waterbody') totalRisk = 10; 

  return {
    dimensions: {
      climate: { temp: baseTemp, precip: 50 + (terrainNoise * 20), extremeEvents: hazard },
      geography: { elevation: isWaterBody ? 0 : 10 + (terrainNoise * 50), landUse, coastal: isWaterBody, waterBody: landUse === 'Waterbody' },
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
      
      const gridData = await generateH3Grid(region_name, scale);

      const cells: H3Cell[] = gridData.cells.map((cell, i) => {
        const tensor = generateContextTensor(cell.lat, cell.lng, gridData.center.lat, gridData.center.lng, scale);
        const actions = selectActions(tensor);
        
        // Use real H3 boundary from h3-js library
        const boundary = getH3HexagonBoundary(cell.h3Index);
        
        // Add terrain-adapted altitude to boundary points
        const elevation = tensor.dimensions.geography.elevation || 0;
        const terrainAdaptedBoundary = boundary.map(pt => ({
          ...pt,
          altitude: elevation * 0.1 // Scale elevation to meters for 3D visualization
        }));

        return {
          id: cell.h3Index,
          h3Index: cell.h3Index,
          center: { lat: cell.lat, lng: cell.lng }, 
          boundary: terrainAdaptedBoundary, 
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
