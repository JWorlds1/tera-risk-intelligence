/**
 * Color Math - Mathematische Farbfunktionen für kontext-basierte polygonale Färbung
 * Implementiert RGB-Interpolation, divergierende Transformation, polygonale Gradienten, CIELAB
 */

export interface RGB {
  r: number;
  g: number;
  b: number;
}

export interface RGBA extends RGB {
  a: number;
}

export interface CIELAB {
  l: number; // Lightness (0-100)
  a: number; // Green-Red axis (-128 to 127)
  b: number; // Blue-Yellow axis (-128 to 127)
}

// Standard diverging palette (ColorBrewer)
export const DEFAULT_PALETTE = {
  low: { r: 44, g: 162, b: 95 } as RGB,      // #2ca25f (Green)
  mid: { r: 255, g: 255, b: 191 } as RGB,    // #ffffbf (Yellow)
  high: { r: 222, g: 45, b: 38 } as RGB,     // #de2d26 (Red)
  breakpoint: 50.0
};

// Context-adaptive colors
export const WATER_COLOR: RGB = { r: 33, g: 150, b: 243 }; // Blue for water bodies

/**
 * Linear interpolation between two colors
 */
export function interpolateColor(color1: RGB, color2: RGB, t: number): RGB {
  t = Math.max(0, Math.min(1, t)); // Clamp to 0-1
  return {
    r: Math.round(color1.r + (color2.r - color1.r) * t),
    g: Math.round(color1.g + (color2.g - color1.g) * t),
    b: Math.round(color1.b + (color2.b - color1.b) * t)
  };
}

/**
 * Normalize value to 0-1 range
 */
export function normalizeValue(
  value: number,
  min: number,
  max: number,
  method: 'min_max' | 'sigmoid' = 'min_max'
): number {
  if (max === min) return 0.5;
  
  if (method === 'min_max') {
    return (value - min) / (max - min);
  } else if (method === 'sigmoid') {
    const mean = (min + max) / 2;
    const stdDev = (max - min) / 4;
    if (stdDev === 0) return 0.5;
    const normalized = (value - mean) / stdDev;
    return 1 / (1 + Math.exp(-normalized));
  }
  
  return 0.5;
}

/**
 * Diverging color transformation with breakpoint
 */
export function divergingColor(
  score: number,
  min: number = 0,
  max: number = 100,
  breakpoint: number = 50,
  useSigmoid: boolean = true
): RGB {
  // Normalize score to 0-100
  const normalized = normalizeValue(score, min, max) * 100;
  
  // Center at breakpoint
  let t = (normalized - breakpoint) / breakpoint;
  
  // Apply sigmoid for smoother transition
  if (useSigmoid) {
    t = 1 / (1 + Math.exp(-t * 2));
  } else {
    t = Math.max(-1, Math.min(1, t)) * 0.5 + 0.5;
  }
  
  // Interpolate based on position relative to breakpoint
  if (normalized <= breakpoint) {
    // Green to Yellow
    const tLocal = normalized / breakpoint;
    return interpolateColor(DEFAULT_PALETTE.low, DEFAULT_PALETTE.mid, tLocal);
  } else {
    // Yellow to Red
    const tLocal = (normalized - breakpoint) / (100 - breakpoint);
    return interpolateColor(DEFAULT_PALETTE.mid, DEFAULT_PALETTE.high, tLocal);
  }
}

/**
 * Convert RGB to hex string
 */
export function rgbToHex(color: RGB): string {
  return `#${[color.r, color.g, color.b].map(x => {
    const hex = x.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }).join('')}`;
}

/**
 * Convert RGB to RGBA string
 */
export function rgbToRgba(color: RGB, alpha: number = 1.0): string {
  return `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`;
}

/**
 * Convert RGB to CIELAB color space
 */
export function rgbToCIELAB(color: RGB): CIELAB {
  // Convert RGB to XYZ (using sRGB)
  let r = color.r / 255;
  let g = color.g / 255;
  let b = color.b / 255;
  
  // Apply gamma correction
  r = r > 0.04045 ? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92;
  g = g > 0.04045 ? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92;
  b = b > 0.04045 ? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92;
  
  // Convert to XYZ (D65 illuminant)
  const x = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) / 0.95047;
  const y = (r * 0.2126729 + g * 0.7151522 + b * 0.0721750) / 1.00000;
  const z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) / 1.08883;
  
  // Convert XYZ to CIELAB
  const fx = x > 0.008856 ? Math.pow(x, 1/3) : (7.787 * x + 16/116);
  const fy = y > 0.008856 ? Math.pow(y, 1/3) : (7.787 * y + 16/116);
  const fz = z > 0.008856 ? Math.pow(z, 1/3) : (7.787 * z + 16/116);
  
  return {
    l: 116 * fy - 16,
    a: 500 * (fx - fy),
    b: 200 * (fy - fz)
  };
}

/**
 * Convert CIELAB to RGB
 */
export function cielabToRGB(lab: CIELAB): RGB {
  // Convert CIELAB to XYZ
  const fy = (lab.l + 16) / 116;
  const fx = lab.a / 500 + fy;
  const fz = fy - lab.b / 200;
  
  const x = (fx > 0.206897 ? Math.pow(fx, 3) : (fx - 16/116) / 7.787) * 0.95047;
  const y = (fy > 0.206897 ? Math.pow(fy, 3) : (fy - 16/116) / 7.787) * 1.00000;
  const z = (fz > 0.206897 ? Math.pow(fz, 3) : (fz - 16/116) / 7.787) * 1.08883;
  
  // Convert XYZ to RGB (sRGB)
  let r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314;
  let g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560;
  let b = x * 0.0556434 + y * -0.2040259 + z * 1.0572252;
  
  // Apply gamma correction
  r = r > 0.0031308 ? 1.055 * Math.pow(r, 1/2.4) - 0.055 : 12.92 * r;
  g = g > 0.0031308 ? 1.055 * Math.pow(g, 1/2.4) - 0.055 : 12.92 * g;
  b = b > 0.0031308 ? 1.055 * Math.pow(b, 1/2.4) - 0.055 : 12.92 * b;
  
  return {
    r: Math.round(Math.max(0, Math.min(255, r * 255))),
    g: Math.round(Math.max(0, Math.min(255, g * 255))),
    b: Math.round(Math.max(0, Math.min(255, b * 255)))
  };
}

/**
 * Interpolate colors in CIELAB space for perceptually uniform transitions
 */
export function interpolateColorCIELAB(color1: RGB, color2: RGB, t: number): RGB {
  t = Math.max(0, Math.min(1, t));
  
  const lab1 = rgbToCIELAB(color1);
  const lab2 = rgbToCIELAB(color2);
  
  const labInterp: CIELAB = {
    l: lab1.l + (lab2.l - lab1.l) * t,
    a: lab1.a + (lab2.a - lab1.a) * t,
    b: lab1.b + (lab2.b - lab1.b) * t
  };
  
  return cielabToRGB(labInterp);
}

/**
 * Compute radial gradient color for polygon
 */
export function computeRadialGradient(
  centerColor: RGB,
  edgeColor: RGB,
  distanceFromCenter: number,
  radius: number
): RGB {
  if (radius === 0) return centerColor;
  
  const intensity = 1 - (distanceFromCenter / radius);
  const clampedIntensity = Math.max(0, Math.min(1, intensity));
  
  return interpolateColor(edgeColor, centerColor, clampedIntensity);
}

/**
 * Compute neighbor interpolation for smooth color transitions
 */
export function computeNeighborInterpolation(
  cellColor: RGB,
  neighborColors: Array<{ color: RGB; distance: number }>,
  influenceRadius: number = 1.0
): RGB {
  if (neighborColors.length === 0) return cellColor;
  
  let totalWeight = 0;
  let weightedR = 0;
  let weightedG = 0;
  let weightedB = 0;
  
  for (const { color, distance } of neighborColors) {
    if (distance > influenceRadius) continue;
    
    // Weight inversely proportional to distance
    const weight = 1.0 / (1.0 + distance);
    totalWeight += weight;
    
    weightedR += color.r * weight;
    weightedG += color.g * weight;
    weightedB += color.b * weight;
  }
  
  if (totalWeight === 0) return cellColor;
  
  // Blend with original color (50/50)
  return {
    r: Math.round((weightedR / totalWeight + cellColor.r) / 2),
    g: Math.round((weightedG / totalWeight + cellColor.g) / 2),
    b: Math.round((weightedB / totalWeight + cellColor.b) / 2)
  };
}

/**
 * Context-adaptive color based on land use and geography
 */
export function contextAdaptiveColor(
  baseColor: RGB,
  landUse: string,
  isWaterBody: boolean
): RGB {
  // Water bodies: constant blue
  if (isWaterBody) {
    return WATER_COLOR;
  }
  
  // Urban areas: boost red/orange
  if (landUse === 'Urban') {
    return {
      r: Math.min(255, baseColor.r + 10),
      g: Math.max(0, baseColor.g - 5),
      b: Math.max(0, baseColor.b - 5)
    };
  }
  
  // Rural areas: boost green
  if (landUse === 'Rural' || landUse === 'Agriculture' || landUse === 'Forest') {
    return {
      r: Math.max(0, baseColor.r - 5),
      g: Math.min(255, baseColor.g + 10),
      b: Math.max(0, baseColor.b - 5)
    };
  }
  
  return baseColor;
}

/**
 * Compute uncertainty alpha channel
 */
export function computeUncertaintyAlpha(
  uncertaintyScore: number,
  baseAlpha: number = 0.8
): number {
  // Higher uncertainty = lower alpha (more transparent)
  return baseAlpha * (1 - uncertaintyScore * 0.5);
}

/**
 * Weighted combination of tensor dimensions
 */
export function weightedContextCombination(
  tensor: any, // ContextTensor from mcp_maps_server
  layerMode: 'composite' | 'hazard' | 'exposure' | 'vulnerability' = 'composite'
): number {
  // Default weights based on layer mode
  let weights: Record<string, number> = {};
  
  if (layerMode === 'hazard') {
    weights = { climate: 0.6, geography: 0.4 };
  } else if (layerMode === 'exposure') {
    weights = { socioeconomic: 0.5, infrastructure: 0.5 };
  } else if (layerMode === 'vulnerability') {
    weights = { vulnerability: 1.0 };
  } else { // composite
    weights = {
      climate: 0.2,
      geography: 0.15,
      socioeconomic: 0.2,
      infrastructure: 0.15,
      vulnerability: 0.3
    };
  }
  
  // Extract dimension values (simplified - would use actual tensor structure)
  const dims = tensor.dimensions || {};
  let weightedSum = 0;
  let totalWeight = 0;
  
  // This is a simplified version - actual implementation would extract real values
  for (const [dim, weight] of Object.entries(weights)) {
    // Placeholder: would extract actual values from tensor
    const value = 50; // Default value
    weightedSum += value * weight;
    totalWeight += weight;
  }
  
  return totalWeight > 0 ? weightedSum / totalWeight : 50;
}

/**
 * Compute final color for a cell with all transformations
 */
export function computeFinalColor(
  tensor: any, // ContextTensor
  layerMode: 'composite' | 'hazard' | 'exposure' | 'vulnerability' = 'composite',
  uncertainty: number = 0.0,
  useCIELAB: boolean = false
): RGBA {
  // Compute base score
  const score = weightedContextCombination(tensor, layerMode);
  
  // Compute diverging color
  let baseColor = divergingColor(score);
  
  // Apply context-adaptive adjustments
  const geography = tensor.dimensions?.geography || {};
  baseColor = contextAdaptiveColor(
    baseColor,
    geography.landUse || 'Unknown',
    geography.waterBody || false
  );
  
  // Compute alpha based on uncertainty
  const alpha = computeUncertaintyAlpha(uncertainty);
  
  return {
    ...baseColor,
    a: alpha
  };
}


