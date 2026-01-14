
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import {Loader} from '@googlemaps/js-api-loader';
import hljs from 'highlight.js';
import {html, LitElement, PropertyValueMap} from 'lit';
import {customElement, query, state} from 'lit/decorators.js';
import {unsafeSVG} from 'lit/directives/unsafe-svg.js';
import {Marked} from 'marked';
import {markedHighlight} from 'marked-highlight';

import {MapParams, GridAnalysis, H3Cell} from './mcp_maps_server';
import {computeFinalColor, divergingColor, rgbToRgba, contextAdaptiveColor} from './color_math';
import {apiClient, ContextSpaceAnalysisRequest} from './api_client';

export const marked = new Marked(
  markedHighlight({
    async: true,
    emptyLangClass: 'hljs',
    langPrefix: 'hljs language-',
    highlight(code, lang, info) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, {language}).value;
    },
  }),
);

const ICON_BUSY_STR = `<svg class="rotating" xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="currentColor"><path d="M480-80q-82 0-155-31.5t-127.5-86Q143-252 111.5-325T80-480q0-83 31.5-155.5t86-127Q252-817 325-848.5T480-880q17 0 28.5 11.5T520-840q0 17-11.5 28.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-17 11.5-28.5T840-520q17 0 28.5 11.5T880-480q0 82-31.5 155t-86 127.5q-54.5 54.5-127 86T480-80Z" /></svg>`;

export enum ChatState { IDLE, GENERATING, THINKING, EXECUTING }

// Google Maps API Key
const USER_PROVIDED_GOOGLE_MAPS_API_KEY: string = 'AIzaSyAJPTwj4S8isr4b-3NtqVSxk450IAS1lOQ';

const EXAMPLE_PROMPTS = [
  "Analyze flood risk in Jakarta in 2030",
  "Detailed neighborhood analysis of Rotterdam",
  "High-resolution heat assessment for Phoenix",
  "Show me detailed grid for Lagos",
  "Plan adaptation for New York (City Scale)"
];

type LayerMode = 'composite' | 'hazard' | 'exposure' | 'vulnerability';

@customElement('gdm-map-app')
export class MapApp extends LitElement {
  @query('#anchor') anchor?: HTMLDivElement;
  @query('#mapContainer') mapContainerElement?: HTMLElement;
  @query('#messageInput') messageInputElement?: HTMLInputElement;

  @state() chatState = ChatState.IDLE;
  @state() messages: HTMLElement[] = [];
  @state() mapError = '';
  @state() selectedCell?: H3Cell; 
  @state() currentGridAnalysis?: GridAnalysis; 
  @state() activeLayer: LayerMode = 'composite';

  private initialPrompt = '';
  private map?: any;
  private geocoder?: any;
  private Marker3DElement?: any;
  private Polygon3DElement?: any;
  private hexPolygons: any[] = [];

  sendMessageHandler?: CallableFunction;
  useBackendAPI: boolean = false; // Toggle for backend API usage

  constructor() {
    super();
    this.initialPrompt = "";
  }

  createRenderRoot() { return this; }

  protected firstUpdated(_changedProperties: PropertyValueMap<any>): void {
    this.loadMap();
  }

  async loadMap() {
    const loader = new Loader({
      apiKey: USER_PROVIDED_GOOGLE_MAPS_API_KEY,
      version: 'beta',
      libraries: ['geocoding', 'maps3d'],
    });

    try {
      await loader.load();
      const maps3dLibrary = await (window as any).google.maps.importLibrary('maps3d');
      this.Marker3DElement = maps3dLibrary.Marker3DElement;
      this.Polygon3DElement = maps3dLibrary.Polygon3DElement;
      this.initializeMap();
    } catch (error) {
      this.mapError = 'Could not load Google Maps.';
    }
  }

  initializeMap() {
    if (!this.mapContainerElement) return;
    this.map = this.mapContainerElement;
    if ((window as any).google && (window as any).google.maps) {
      this.geocoder = new (window as any).google.maps.Geocoder();
    }
  }

  setChatState(state: ChatState) { this.chatState = state; }

  private _clearMapElements() {
    this.hexPolygons.forEach(p => {
        if (p && p.parentElement) p.parentElement.removeChild(p);
    });
    this.hexPolygons = [];
    this.selectedCell = undefined;
  }

  private getRiskColor(score: number): {r:number, g:number, b:number, hex: string} {
    // Use mathematical diverging color transformation
    const color = divergingColor(score, 0, 100, 50, true);
    const hex = "#" + [color.r, color.g, color.b].map(x => {
      const hex = x.toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    }).join('');
    return {r: color.r, g: color.g, b: color.b, hex};
  }

  private getColorForLayer(cell: H3Cell, layer: LayerMode): string {
    // Use mathematical color computation with context adaptation
    const geography = cell.tensor.dimensions.geography;
    
    if (geography.waterBody) {
        return 'rgba(33, 150, 243, 0.3)'; // Constant blue for water
    }

    let score = 0;
    
    switch (layer) {
      case 'composite':
        score = cell.tensor.scores.totalRisk;
        break;
      case 'hazard':
        score = cell.tensor.scores.hazard;
        break;
      case 'exposure':
        score = cell.tensor.scores.exposure;
        break;
      case 'vulnerability':
        score = cell.tensor.scores.vulnerability;
        break;
    }
    
    // Use mathematical diverging color
    let baseColor = divergingColor(score, 0, 100, 50, true);
    
    // Apply context-adaptive adjustments
    baseColor = contextAdaptiveColor(
      baseColor,
      geography.landUse || 'Unknown',
      geography.waterBody || false
    );
    
    // Compute alpha based on uncertainty (if available)
    const uncertainty = 0.0; // Would come from tensor in real implementation
    const alpha = 0.8 * (1 - uncertainty * 0.5);
    
    return rgbToRgba(baseColor, alpha);
  }

  private async _renderH3Grid(location: string, analysis: GridAnalysis) {
    if (!this.map || !this.Polygon3DElement) return;
    this._clearMapElements();
    this.currentGridAnalysis = analysis;

    // Use Grid Center from Server (Syncs perfectly)
    let centerLat = analysis.gridCenter.lat;
    let centerLng = analysis.gridCenter.lng;

    // Camera Positioning
    let range = 6000;
    let tilt = 55;
    if (analysis.scale === 'neighborhood') { range = 2000; tilt = 65; }
    if (analysis.scale === 'region') { range = 40000; tilt = 35; }

    (this.map as any).flyCameraTo({
      endCamera: {
        center: {lat: centerLat, lng: centerLng, altitude: 0},
        heading: 0,
        tilt: tilt,
        range: range,
      },
      durationMillis: 2000,
    });

    // Render Polygons
    analysis.cells.forEach(cell => {
        const isWater = cell.tensor.dimensions.geography.waterBody;
        const isUrban = cell.tensor.dimensions.geography.landUse === 'Urban';
        const isSuburban = cell.tensor.dimensions.geography.landUse === 'Suburban';
        
        const poly = new this.Polygon3DElement();
        
        // Use RELATIVE_TO_GROUND to ensure visibility over terrain
        poly.altitudeMode = 'RELATIVE_TO_GROUND';

        // Physical Extrusion Logic with Terrain Adaptation
        let extrusionHeight = 0;
        const elevation = cell.tensor.dimensions.geography?.elevation || 0;
        
        if (!isWater) {
             // Base height from elevation (terrain adaptation)
             const baseHeight = elevation * 0.1; // Scale elevation to meters
             
             // Risk-based extrusion
             const riskExtrusion = cell.tensor.scores.totalRisk * 2;
             
             if (isUrban) {
                 extrusionHeight = baseHeight + 150 + riskExtrusion * 1.5; 
             } else if (isSuburban) {
                 extrusionHeight = baseHeight + 50 + riskExtrusion * 1.0;
             } else {
                 extrusionHeight = baseHeight + 20 + riskExtrusion * 0.5;
             }
        }
        
        // Coordinates - Map altitude to the extrusion height with terrain adaptation
        const realCoords = cell.boundary.map(pt => ({
            lat: pt.lat, 
            lng: pt.lng,
            altitude: extrusionHeight
        }));

        poly.outerCoordinates = realCoords;
        poly.extruded = !isWater; // Only extrude land
        
        // Apply Dynamic Layer Color
        poly.fillColor = this.getColorForLayer(cell, this.activeLayer);
        
        // Stroke styling
        if (isWater) {
            poly.strokeColor = 'rgba(33, 150, 243, 0.5)';
            poly.strokeWidth = 1.0;
        } else {
            poly.strokeColor = 'rgba(255,255,255, 0.4)';
            poly.strokeWidth = 1.5;
        }

        // Click Listener
        poly.addEventListener('click', () => {
          this.selectedCell = cell;
        });

        (this.map as any).appendChild(poly);
        this.hexPolygons.push(poly);
    });
  }

  // Called when toggling layers
  private _updateLayerVisualization() {
    if (!this.currentGridAnalysis || !this.hexPolygons.length) return;
    
    this.currentGridAnalysis.cells.forEach((cell, index) => {
       if (this.hexPolygons[index]) {
          this.hexPolygons[index].fillColor = this.getColorForLayer(cell, this.activeLayer);
       }
    });
  }

  async handleMapQuery(params: MapParams) {
    if (params.gridAnalysis && params.location) {
      this._renderH3Grid(params.location, params.gridAnalysis);
    } else if (params.location) {
       if (!this.map || !this.geocoder) return;
       this.geocoder.geocode({address: params.location}, (r:any) => {
         if(r && r[0]) {
             const l = r[0].geometry.location;
             (this.map as any).flyCameraTo({endCamera:{center:{lat:l.lat(), lng:l.lng(), altitude:0}, range:10000}});
         }
       });
    }
  }

  addMessage(role: string, message: string) {
    const div = document.createElement('div');
    div.classList.add('turn', `role-${role.trim()}`);
    
    const thinkingDetails = document.createElement('details');
    thinkingDetails.classList.add('thinking');
    thinkingDetails.style.display = 'none'; 
    thinkingDetails.innerHTML = `<summary>${ICON_BUSY_STR} Processing...</summary><div class="thinking-content"></div>`;
    div.appendChild(thinkingDetails);
    
    const textElement = document.createElement('div');
    textElement.className = 'text';
    textElement.innerHTML = message;
    div.appendChild(textElement);
    this.messages = [...this.messages, div];
    this.scrollToTheEnd();
    return {thinkingContainer: thinkingDetails, thinkingElement: thinkingDetails.querySelector('.thinking-content')!, textElement};
  }

  scrollToTheEnd() { this.anchor?.scrollIntoView({behavior: 'smooth', block: 'end'}); }

  async sendMessageAction() {
    if (this.chatState !== ChatState.IDLE || !this.messageInputElement) return;
    const msg = this.messageInputElement.value.trim();
    if (!msg) return;
    this.messageInputElement.value = '';
    
    const {textElement, thinkingContainer} = this.addMessage('user', '...');
    textElement.innerHTML = await marked.parse(msg);
    if (this.sendMessageHandler) await this.sendMessageHandler(msg, 'user');
  }

  private renderMetricBar(label: string, value: number, colorClass: string) {
    return html`
      <div class="metric-row">
        <span class="metric-label">${label}</span>
        <div class="metric-bar-container">
           <div class="metric-bar ${colorClass}" style="width: ${value}%"></div>
        </div>
        <span class="metric-value">${value.toFixed(0)}</span>
      </div>
    `;
  }

  private renderWelcomeScreen() {
    return html`
      <div class="welcome-screen">
        <h3>Global Context Space</h3>
        <p>Initialize a context simulation by selecting a scenario below:</p>
        <div class="suggestion-chips">
          ${EXAMPLE_PROMPTS.map(p => html`
            <button @click=${() => { 
               if(this.messageInputElement) this.messageInputElement.value = p; 
               this.sendMessageAction();
            }}>${p}</button>
          `)}
        </div>
      </div>
    `;
  }

  private renderSystemMonitor() {
    return html`
      <div class="system-monitor">
         <div class="monitor-header">
           <span class="blink">●</span> SYSTEM INFERENCE RUNNING
         </div>
         <div class="monitor-grid">
            <div class="monitor-row">
               <span>Satellite Uplink</span>
               <div class="progress"><div class="fill" style="width: 100%; animation: load 1s infinite;"></div></div>
            </div>
            <div class="monitor-row">
               <span>Climate Models (IPCC)</span>
               <div class="progress"><div class="fill" style="width: 80%; animation: load 2s infinite;"></div></div>
            </div>
            <div class="monitor-row">
               <span>Socio-Econ Tensor</span>
               <div class="progress"><div class="fill" style="width: 60%; animation: load 1.5s infinite;"></div></div>
            </div>
            <div class="monitor-log">
               > Initializing H3 Grid...<br>
               > Calculating Hazard Vectors...<br>
               > Synthesizing Action Plans...
            </div>
         </div>
      </div>
    `;
  }

  render() {
    return html`<div class="gdm-map-app">
      <div class="main-container">
        <!-- Default UI Hidden for cleaner look -->
        <gmp-map-3d id="mapContainer" mode="hybrid" center="0,0,10000000" range="20000000" default-ui-hidden="true"></gmp-map-3d>

        <!-- MAP LAYER CONTROL -->
        ${this.currentGridAnalysis ? html`
          <div class="layer-control">
             <h3>Map Layers</h3>
             <button class="${this.activeLayer === 'composite' ? 'active' : ''}" @click=${() => { this.activeLayer = 'composite'; this._updateLayerVisualization(); }}>Composite Risk</button>
             <button class="${this.activeLayer === 'hazard' ? 'active' : ''}" @click=${() => { this.activeLayer = 'hazard'; this._updateLayerVisualization(); }}>Hazard (Red)</button>
             <button class="${this.activeLayer === 'exposure' ? 'active' : ''}" @click=${() => { this.activeLayer = 'exposure'; this._updateLayerVisualization(); }}>Exposure (Org)</button>
             <button class="${this.activeLayer === 'vulnerability' ? 'active' : ''}" @click=${() => { this.activeLayer = 'vulnerability'; this._updateLayerVisualization(); }}>Vulnerability (Grn)</button>
          </div>
        ` : ''}

        <!-- CELL INSPECTION PANEL -->
        ${this.selectedCell ? html`
          <div class="risk-panel-overlay">
             <div class="risk-panel-header">
               <h2>Context Space: ${this.selectedCell.tensor.dimensions.geography.waterBody ? 'Water Body' : this.selectedCell.tensor.dimensions.geography.landUse}</h2>
               <button class="close-btn" @click=${() => this.selectedCell = undefined}>×</button>
             </div>
             
             <div class="tensor-summary">
                <div class="risk-badge" style="background-color: ${this.getRiskColor(this.selectedCell.tensor.scores.totalRisk).hex}">
                  RISK SCORE: ${this.selectedCell.tensor.scores.totalRisk.toFixed(0)}
                </div>
                <div class="scenario-tag">${this.currentGridAnalysis?.scenario}</div>
             </div>

             <div class="tensor-dimensions">
                <h3>Context Tensor Dimensions</h3>
                ${this.renderMetricBar("Hazard", this.selectedCell.tensor.scores.hazard, "bar-hazard")}
                ${this.renderMetricBar("Exposure", this.selectedCell.tensor.scores.exposure, "bar-exposure")}
                ${this.renderMetricBar("Vulnerability", this.selectedCell.tensor.scores.vulnerability, "bar-vuln")}
             </div>

             <div class="key-metrics-grid">
                <div class="kpi"><span>Pop Density</span> <strong>${this.selectedCell.tensor.dimensions.socio.popDensity.toFixed(0)}</strong></div>
                <div class="kpi"><span>Infrastructure</span> <strong>${this.selectedCell.tensor.dimensions.infrastructure.roadDensity.toFixed(0)}</strong></div>
                <div class="kpi"><span>Governance</span> <strong>${this.selectedCell.tensor.dimensions.vulnerability.governance.toFixed(0)}</strong></div>
             </div>

             <h3>Recommended Interventions</h3>
             <div class="actions-list">
               ${this.selectedCell.actions.map(action => html`
                 <div class="action-card">
                    <div class="action-head">
                       <span class="icon">${action.icon}</span>
                       <span class="title">${action.title}</span>
                       <span class="type-tag ${action.type.toLowerCase()}">${action.type}</span>
                    </div>
                    <div class="action-details">
                       💰 €${action.cost.toLocaleString()} • ⏱ ${action.timeline}
                    </div>
                 </div>
               `)}
             </div>
          </div>
        ` : this.currentGridAnalysis && !this.selectedCell ? html`
            <!-- Global Grid Summary (Dashboard) -->
            <div class="risk-panel-overlay minimized">
                <div class="risk-panel-header">
                   <h2>${this.currentGridAnalysis.regionName} Analysis</h2>
                </div>
                
                <div class="global-stats-grid">
                    <div class="stat-box">
                        <label>Avg Risk</label>
                        <div class="value" style="color: ${this.getRiskColor(this.currentGridAnalysis.globalStats.avgRisk).hex}">
                           ${this.currentGridAnalysis.globalStats.avgRisk.toFixed(0)}
                        </div>
                    </div>
                    <div class="stat-box">
                        <label>Pop. Affected</label>
                        <div class="value">${(this.currentGridAnalysis.globalStats.affectedPopulation / 1000000).toFixed(1)}M</div>
                    </div>
                    <div class="stat-box">
                        <label>Est. Cost</label>
                        <div class="value">€${(this.currentGridAnalysis.globalStats.totalCost / 1000000).toFixed(0)}M</div>
                    </div>
                </div>

                <div class="tensor-summary" style="margin-top: 10px;">
                   <div class="scenario-tag">${this.currentGridAnalysis.scenario}</div>
                   <div class="scenario-tag">${this.currentGridAnalysis.year}</div>
                </div>
                
                <p style="font-size: 0.85rem; color: #666; margin-top: 10px;">
                  High-fidelity Context Space loaded (${this.currentGridAnalysis.scale}). 
                  Click on any hexagonal cell to inspect local data.
                </p>
            </div>
        ` : ''}

      </div>
      <div class="sidebar">
        <div class="selector"><button class="selected-tab">Context Space System</button></div>
        
        <!-- SYSTEM MONITOR (Visible when thinking) -->
        ${(this.chatState === ChatState.THINKING || this.chatState === ChatState.GENERATING) ? this.renderSystemMonitor() : ''}

        <div class="chat-flex">
           <div class="chat-messages">
             ${this.messages.length === 0 ? this.renderWelcomeScreen() : this.messages}
             <div id="anchor"></div>
           </div>
           <div class="footer">
             <div id="inputArea">
               <input id="messageInput" @keydown=${(e:any) => e.key === 'Enter' && this.sendMessageAction()} placeholder="Analyze a location..." />
               <button id="sendButton" @click=${() => this.sendMessageAction()}>➤</button>
             </div>
           </div>
        </div>
      </div>
    </div>`;
  }
}
