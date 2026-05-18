# WebSocket Processing Workflow

This document outlines the detailed steps and implementation details for the WebSocket processing in the project, as extracted from Gemini Code Assist analysis.

## Detailed WebSocket Processing Workflow

### 1. Initialization & Connection
- **Endpoint Selection:** `LivestreamPage.actionOnPageLoad` determines the WebSocket URL based on whether a proxy is required.
- **API Instance:** `LivestreamPageView.performViewWillAppearAction` creates an instance of `GeminiLiveAPI`.
- **WebSocket Creation:** `GeminiLiveAPI.initializeWebSocket` creates a standard `WebSocket` object (or uses a custom provider like `cueme_wsConnect` if configured).
- **Event Mapping:** `GeminiLiveAPI.setupJavascriptWebSocket` maps native WebSocket events (`onopen`, `onmessage`, `onerror`, `onclose`) to internal handler methods.

### 2. Session Setup
- **Handshake:** Once the connection opens (`webSocketOnOpen`), `LivestreamPage` sends a setup message via `sendCustomSetup()` or `sendCustomSetupForProxy()`.
- **Configuration:** This message contains the Gemini model name, `systemInstruction` (defining the AI's role and rules), and `generationConfig`.
- **Ready State:** When the server responds with `setupComplete`, the `onSetupComplete` callback is triggered, enabling the microphone and media controls.

### 3. Data Input (Streaming)
- **Video Frames:** `MediaHandler` captures camera frames as base64 images. `LivestreamPage` sends these to the WebSocket in a `realtimeInput` message:
  ```json
  {
    "realtimeInput": {
      "mediaChunks": [{ "mime_type": "image/jpeg", "data": "base64_string" }]
    }
  }
  ```
- **Periodic Prompts:** `sendPeriodicClientMessageToGeminiMMLiveAPI()` periodically sends a text prompt (e.g., "Identify equipment in the view") to Gemini to trigger analysis.

### 4. Response Handling (Output)
- **Message Parsing:** `GeminiLiveAPI.webSocketOnMessage` receives responses. It handles `serverContent` which may contain:
  - `interrupted`: Stops current TTS playback.
  - `modelTurn`: Contains text or audio parts. Text parts are accumulated in `completeturndata`.
- **Turn Completion:** When `turnComplete: true` is received, `geminiApiOnTurnComplete()` is called.
- **Data Processing:**
  - The text response (usually JSON) is cleaned and parsed.
  - It extracts equipment details (Brand, Model, Serial Number) and updates the `equipments` array.
  - `user_instructions` from the AI are added to a **TTS Play Queue** (`addToTTSPlayQueue`) to be spoken to the user.

### 5. Termination
- **Graceful Stop:** `stopMedia()` sends an "end message" (empty parts with `turn_complete: true`) to signal the end of the session.
- **Cleanup:** `performLivestreamCleanupAction()` closes the WebSocket and dismisses any active UI loading states.

---

## Pre-Connection HTTP Handshake

While WebSockets are for real-time communication, a standard HTTP call is often required *before* the upgrade.

### 1. Authentication & Security ("The Token Pattern")
The WebSocket protocol (especially in browsers) does not support custom headers (like `Authorization: Bearer ...`) during the initial handshake.
- **Problem:** Cannot safely pass a secret API key or password directly in the WebSocket URL (as it would be visible in server logs).
- **Solution:** Make a "standard" HTTP POST request first to a secure endpoint. That endpoint verifies credentials and returns a short-lived **Access Token**. You then append that token to the WebSocket URL or sub-protocol to "upgrade" the connection securely.

### 2. Specific HTTP Steps in this Project
1. **Fetching the Access Token (`getTestAccessToken`):**
   - **Endpoint:** `https://analyticsqa.cue-me.com/gcp-access/get`
   - **Payload:** Hardcoded `user_id` ("DRA") and `password`.
   - **Purpose:** Retrieves a short-lived **GCP Access Token** required to authorize the WebSocket session.
2. **Location Services (`getLocationAsync`):**
   - The app makes an asynchronous request to get the device's GPS coordinates (Latitude/Longitude) which are stored in the `UserContextProvider`.
3. **Push Notification Registration:**
   - The `initializeData()` method calls `this.pushNotifications.registerNotifications()`.

### Summary of Sequence
1. **HTTP POST:** Get Access Token (Auth).
2. **HTTP (Internal):** Register Push Notifications.
3. **Location Check:** Get Lat/Lng.
4. **WebSocket Upgrade:** Initiate `wss://` connection using the token retrieved in Step 1.
