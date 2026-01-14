
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * This is the main entry point for the application.
 * It sets up the LitElement-based MapApp component, initializes the Google GenAI
 * client for chat interactions, and establishes communication between the
 * Model Context Protocol (MCP) client and server. The MCP server exposes
 * map-related tools that the AI model can use, and the client relays these
 * tool calls to the server.
 */

import {GoogleGenAI, mcpToTool} from '@google/genai';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {InMemoryTransport} from '@modelcontextprotocol/sdk/inMemory.js';
import {Transport} from '@modelcontextprotocol/sdk/shared/transport.js';
import {ChatState, MapApp, marked} from './map_app'; // Updated import path

import {startMcpGoogleMapServer, MapParams} from './mcp_maps_server';

/* --------- */

async function startClient(transport: Transport) {
  const client = new Client({name: 'AI Studio', version: '1.0.0'});
  await client.connect(transport);
  return client;
}

/* ------------ */

const SYSTEM_INSTRUCTIONS = `You are the architect of the **Global Climate Context-Space System**. 
Your role is to analyze any location on Earth using a rigorous Discrete Global Grid System (H3) and Multidimensional Context Tensors.

**Core Framework:**
1.  **Context Tensor:** You analyze every location across 5 dimensions: Climate, Geography, Socioeconomics, Infrastructure, and Vulnerability.
2.  **Risk Equation:** Risk = Hazard × Exposure × Vulnerability.
3.  **Scenarios:** You simulate futures based on IPCC SSP scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5).

**Operational Guidelines:**

1.  **'analyze_context_space':** Use this tool for ALL risk, climate, or future planning queries.
    *   **Input:** User asks "What is the flood risk in Jakarta in 2030?"
    *   **Action:** Call \`analyze_context_space(region_name="Jakarta", year_offset=6, scenario="SSP3-7.0", scale="city")\`.
    *   **Scale Selection:**
        *   **'neighborhood'**: Use for specific districts, small towns, or high-detail queries (approx 60m hex, high granularity).
        *   **'city'**: Use for standard city-wide analysis (approx 180m hex).
        *   **'region'**: Use for provinces, states, or large areas (approx 1.2km hex).
    *   **Output:** The tool returns a simulated H3 Hexagonal Grid where each cell has specific data.
    *   **Response:**
        *   Do NOT list every single cell in text.
        *   Summarize the *clusters* of risk (e.g., "The northern coastal cells show critical vulnerability due to subsidence...").
        *   Instruct the user to **"Click on specific hexagonal cells on the map"** to inspect the local Context Tensor and see tailored action plans.

2.  **'view_location_google_maps' & 'directions_on_google_maps':** Use ONLY for simple navigation.

**Tone:**
Scientific, precise, yet action-oriented. You are providing decision support for governments and NGOs.
`;

// Check if API key is available
const apiKey = process.env.API_KEY || '';
let ai: GoogleGenAI | null = null;

if (apiKey && apiKey.length > 0) {
  ai = new GoogleGenAI({ apiKey });
} else {
  console.warn('No Gemini API Key found. Chat functionality disabled. Set GEMINI_API_KEY in .env.local');
}

function createAiChat(mcpClient: Client) {
  if (!ai) return null;
  return ai.chats.create({
    model: 'gemini-2.5-flash',
    config: {
      systemInstruction: SYSTEM_INSTRUCTIONS,
      tools: [mcpToTool(mcpClient)],
    },
  });
}

function camelCaseToDash(str: string): string {
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
    .toLowerCase();
}

document.addEventListener('DOMContentLoaded', async (event) => {
  const rootElement = document.querySelector('#root')! as HTMLElement;

  const mapApp = new MapApp();
  // Fix: Cast to Node to satisfy TypeScript's strict appendChild signature
  rootElement.appendChild(mapApp as unknown as Node);

  const [transportA, transportB] = InMemoryTransport.createLinkedPair();

  void startMcpGoogleMapServer(
    transportA,
    (params: MapParams) => {
      mapApp.handleMapQuery(params);
    },
  );

  const mcpClient = await startClient(transportB);
  const aiChat = createAiChat(mcpClient);

  mapApp.sendMessageHandler = async (input: string, role: string) => {
    // If no AI is available, show a message
    if (!aiChat) {
      const {textElement} = mapApp.addMessage('assistant', '');
      textElement.innerHTML = '⚠️ <strong>Gemini API Key fehlt!</strong><br>Bitte setze GEMINI_API_KEY in der .env.local Datei um den Chat zu aktivieren.<br><br>Die Karten-Visualisierung funktioniert trotzdem - klicke auf die Buttons um Städte zu erkunden!';
      mapApp.setChatState(ChatState.IDLE);
      return;
    }

    console.log('sendMessageHandler', input, role);

    const {thinkingElement, textElement, thinkingContainer} = mapApp.addMessage(
      'assistant',
      '',
    );

    mapApp.setChatState(ChatState.GENERATING);
    textElement.innerHTML = '...'; // Initial placeholder

    let newCode = '';
    let thoughtAccumulator = '';

    try {
      // Outer try for overall message handling including post-processing
      try {
        // Inner try for AI interaction and message parsing
        const stream = await aiChat.sendMessageStream({message: input});

        for await (const chunk of stream) {
          for (const candidate of chunk.candidates ?? []) {
            for (const part of candidate.content?.parts ?? []) {
              if (part.functionCall) {
                console.log(
                  'FUNCTION CALL:',
                  part.functionCall.name,
                  part.functionCall.args,
                );
                const mcpCall = {
                  name: camelCaseToDash(part.functionCall.name!),
                  arguments: part.functionCall.args,
                };

                const explanation =
                  'Accessing Context-Space...\n```json\n' +
                  JSON.stringify(mcpCall, null, 2) +
                  '\n```';
                const {textElement: functionCallText, thinkingContainer: fcThinking} = mapApp.addMessage(
                  'assistant',
                  '',
                );
                fcThinking.style.display = 'none'; // Hide thinking for function calls usually
                functionCallText.innerHTML = await marked.parse(explanation);
              }

              if (part.thought) {
                mapApp.setChatState(ChatState.THINKING);
                thoughtAccumulator += part.thought; 
                thinkingElement.innerHTML = await marked.parse(thoughtAccumulator);
                
                // Logic for showing thinking container (we keep it for history, but UI uses monitor now)
                if (thinkingContainer) {
                  // thinkingContainer.style.display = 'block'; 
                }
              } else if (part.text) {
                mapApp.setChatState(ChatState.EXECUTING);
                
                newCode += part.text;
                textElement.innerHTML = await marked.parse(newCode);
              }
              mapApp.scrollToTheEnd();
            }
          }
        }
      } catch (e: unknown) {
        // Catch for AI interaction errors.
        console.error('GenAI SDK Error:', e);
        let baseErrorText: string;

        if (e instanceof Error) {
          baseErrorText = e.message;
        } else if (typeof e === 'string') {
          baseErrorText = e;
        } else if (
          e &&
          typeof e === 'object' &&
          'message' in e &&
          typeof (e as {message: unknown}).message === 'string'
        ) {
          baseErrorText = (e as {message: string}).message;
        } else {
          try {
            // Attempt to stringify complex objects
            baseErrorText = `Unexpected error: ${JSON.stringify(e)}`;
          } catch (stringifyError) {
            baseErrorText = `Unexpected error: ${String(e)}`;
          }
        }

        let finalErrorMessage = baseErrorText;
        const jsonStartIndex = baseErrorText.indexOf('{');
        const jsonEndIndex = baseErrorText.lastIndexOf('}');

        if (jsonStartIndex > -1 && jsonEndIndex > jsonStartIndex) {
          const potentialJson = baseErrorText.substring(
            jsonStartIndex,
            jsonEndIndex + 1,
          );
          try {
            const sdkError = JSON.parse(potentialJson);
            if (sdkError?.error?.message) {
              finalErrorMessage = sdkError.error.message;
            } else if (sdkError?.message) {
              finalErrorMessage = sdkError.message;
            }
          } catch (parseError) {
            console.warn('Could not parse error JSON', parseError);
          }
        }

        const {textElement: errorTextElement, thinkingContainer: errorThinking} = mapApp.addMessage('error', '');
        errorThinking.style.display = 'none';
        errorTextElement.innerHTML = await marked.parse(
          `Error: ${finalErrorMessage}`,
        );
      }
      
      if (!thoughtAccumulator && thinkingContainer) {
          thinkingContainer.style.display = 'none';
      }

      if (
        textElement.innerHTML.trim() === '...' ||
        textElement.innerHTML.trim().length === 0
      ) {
        const hasFunctionCallMessage = mapApp.messages.some((el) =>
          el.innerHTML.includes('Accessing Context-Space'),
        );
        if (!hasFunctionCallMessage) {
          textElement.innerHTML = await marked.parse('Done.');
        } else if (textElement.innerHTML.trim() === '...') {
          textElement.innerHTML = '';
        }
      }
    } finally {
      mapApp.setChatState(ChatState.IDLE);
    }
  };
});
