/**
 * Gradual Fine-Granular Animation Engine
 * Provides smooth, sequential animations for H3 grid polygons
 */

export interface AnimationConfig {
  duration?: number;        // Animation duration in ms
  staggerDelay?: number;     // Delay between each polygon animation (ms)
  easing?: (t: number) => number; // Easing function
  batchSize?: number;        // Number of polygons to animate simultaneously
}

export interface AnimatedPolygon {
  element: any;             // Google Maps Polygon3DElement
  targetHeight: number;
  targetColor: string;
  targetAlpha: number;
  startHeight: number;
  startColor: string;
  startAlpha: number;
  startTime: number;
}

export class GradualAnimationEngine {
  private activeAnimations: Map<any, AnimatedPolygon> = new Map();
  private animationFrameId: number | null = null;
  private config: Required<AnimationConfig>;

  constructor(config: AnimationConfig = {}) {
    this.config = {
      duration: config.duration ?? 1200,        // 1.2s per polygon
      staggerDelay: config.staggerDelay ?? 30,   // 30ms between polygons
      easing: config.easing ?? this.easeOutCubic,
      batchSize: config.batchSize ?? 5,          // 5 polygons at once
    };
  }

  /**
   * Easing functions for smooth animations
   */
  private easeOutCubic(t: number): number {
    return 1 - Math.pow(1 - t, 3);
  }

  private easeInOutQuad(t: number): number {
    return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  private easeOutExpo(t: number): number {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  /**
   * Interpolate between two RGB colors
   */
  private interpolateColor(
    startColor: string,
    endColor: string,
    t: number
  ): string {
    // Parse rgba strings like "rgba(255, 0, 0, 0.8)"
    const parseRGBA = (color: string): [number, number, number, number] => {
      const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
      if (match) {
        return [
          parseInt(match[1]),
          parseInt(match[2]),
          parseInt(match[3]),
          match[4] ? parseFloat(match[4]) : 1.0,
        ];
      }
      // Fallback: try hex color
      const hex = color.replace('#', '');
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      return [r, g, b, 1.0];
    };

    const [r1, g1, b1, a1] = parseRGBA(startColor);
    const [r2, g2, b2, a2] = parseRGBA(endColor);

    const r = Math.round(r1 + (r2 - r1) * t);
    const g = Math.round(g1 + (g2 - g1) * t);
    const b = Math.round(b1 + (b2 - b1) * t);
    const a = a1 + (a2 - a1) * t;

    return `rgba(${r}, ${g}, ${b}, ${a})`;
  }

  /**
   * Animate a single polygon with gradual transitions
   */
  private animatePolygon(anim: AnimatedPolygon, currentTime: number): boolean {
    const elapsed = currentTime - anim.startTime;
    const progress = Math.min(elapsed / this.config.duration, 1);
    const easedProgress = this.config.easing(progress);

    // Interpolate height
    const currentHeight = anim.startHeight + (anim.targetHeight - anim.startHeight) * easedProgress;
    
    // Interpolate color
    const currentColor = this.interpolateColor(anim.startColor, anim.targetColor, easedProgress);
    
    // Interpolate alpha
    const currentAlpha = anim.startAlpha + (anim.targetAlpha - anim.startAlpha) * easedProgress;

    // Update polygon properties
    try {
      // Update altitude for all boundary points
      // Google Maps 3D Polygons require updating the entire outerCoordinates array
      if (anim.element.outerCoordinates && Array.isArray(anim.element.outerCoordinates)) {
        const updatedCoords = anim.element.outerCoordinates.map((coord: any) => ({
          lat: coord.lat,
          lng: coord.lng,
          altitude: currentHeight,
        }));
        // Create a new array to trigger update
        anim.element.outerCoordinates = updatedCoords;
      }

      // Update color with current alpha
      const colorMatch = currentColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
      if (colorMatch) {
        const r = parseInt(colorMatch[1]);
        const g = parseInt(colorMatch[2]);
        const b = parseInt(colorMatch[3]);
        anim.element.fillColor = `rgba(${r}, ${g}, ${b}, ${currentAlpha})`;
      } else {
        // Fallback: try to preserve existing color format
        const existingColor = anim.element.fillColor || currentColor;
        const existingMatch = existingColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (existingMatch) {
          const r = parseInt(existingMatch[1]);
          const g = parseInt(existingMatch[2]);
          const b = parseInt(existingMatch[3]);
          anim.element.fillColor = `rgba(${r}, ${g}, ${b}, ${currentAlpha})`;
        } else {
          anim.element.fillColor = currentColor;
        }
      }
    } catch (error) {
      console.warn('Animation update error:', error);
      return false; // Remove from active animations
    }

    // Return true if animation is complete
    return progress >= 1;
  }

  /**
   * Main animation loop using requestAnimationFrame
   */
  private animationLoop = (currentTime: number) => {
    const completed: any[] = [];

    // Animate all active polygons
    this.activeAnimations.forEach((anim, element) => {
      if (this.animatePolygon(anim, currentTime)) {
        completed.push(element);
      }
    });

    // Remove completed animations
    completed.forEach(element => {
      this.activeAnimations.delete(element);
    });

    // Continue animation loop if there are active animations
    if (this.activeAnimations.size > 0) {
      this.animationFrameId = requestAnimationFrame(this.animationLoop);
    } else {
      this.animationFrameId = null;
    }
  };

  /**
   * Start gradual animation for a batch of polygons
   */
  public animatePolygons(
    polygons: Array<{
      element: any;
      targetHeight: number;
      targetColor: string;
      targetAlpha: number;
    }>
  ): void {
    // Stop any existing animations
    this.stop();

    const startTime = performance.now();
    let delayOffset = 0;

    // Create staggered animations
    polygons.forEach((poly, index) => {
      const anim: AnimatedPolygon = {
        element: poly.element,
        targetHeight: poly.targetHeight,
        targetColor: poly.targetColor,
        targetAlpha: poly.targetAlpha,
        startHeight: 0, // Start from ground
        startColor: this.extractColor(poly.element.fillColor || 'rgba(200, 200, 200, 0.1)'),
        startAlpha: 0.1, // Start nearly transparent
        startTime: startTime + delayOffset,
      };

      this.activeAnimations.set(poly.element, anim);
      
      // Stagger delay: increase delay for each polygon
      delayOffset += this.config.staggerDelay;
    });

    // Start animation loop if not already running
    if (this.animationFrameId === null) {
      this.animationFrameId = requestAnimationFrame(this.animationLoop);
    }
  }

  /**
   * Extract color from element or return default
   */
  private extractColor(color: string | undefined): string {
    if (!color) return 'rgba(200, 200, 200, 0.1)';
    return color;
  }

  /**
   * Animate color change for existing polygons (e.g., layer switching)
   */
  public animateColorTransition(
    polygons: Array<{
      element: any;
      targetColor: string;
      targetAlpha: number;
    }>
  ): void {
    const startTime = performance.now();
    let delayOffset = 0;

    polygons.forEach((poly) => {
      const currentColor = this.extractColor(poly.element.fillColor);
      const currentAlpha = this.extractAlpha(poly.element.fillColor);
      const currentHeight = this.getCurrentHeight(poly.element);

      const anim: AnimatedPolygon = {
        element: poly.element,
        targetHeight: currentHeight, // Keep height constant
        targetColor: poly.targetColor,
        targetAlpha: poly.targetAlpha,
        startHeight: currentHeight,
        startColor: currentColor,
        startAlpha: currentAlpha,
        startTime: startTime + delayOffset,
      };

      this.activeAnimations.set(poly.element, anim);
      delayOffset += this.config.staggerDelay / 2; // Faster for color transitions
    });

    if (this.animationFrameId === null) {
      this.animationFrameId = requestAnimationFrame(this.animationLoop);
    }
  }

  /**
   * Extract alpha from color string
   */
  private extractAlpha(color: string): number {
    const match = color.match(/rgba?\([^)]+,\s*([\d.]+)\)/);
    return match ? parseFloat(match[1]) : 1.0;
  }

  /**
   * Get current height from polygon coordinates
   */
  private getCurrentHeight(element: any): number {
    if (element.outerCoordinates && element.outerCoordinates.length > 0) {
      return element.outerCoordinates[0].altitude || 0;
    }
    return 0;
  }

  /**
   * Stop all animations
   */
  public stop(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.activeAnimations.clear();
  }

  /**
   * Update animation configuration
   */
  public updateConfig(config: Partial<AnimationConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Check if animations are currently running
   */
  public isAnimating(): boolean {
    return this.activeAnimations.size > 0;
  }
}

