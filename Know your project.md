# GNSS Shield Project — Architectural Summary

**Context:** Comprehensive technical summary of the FastAPI backend, React frontend, and ML inference pipeline.

### 1. Data Flow & Backend (FastAPI)
*   **Ingestion Setup**: The system strictly uses REST API endpoints (No WebSockets). Ingestion happens through `POST /predict` (for manual JSON signal injection) and `POST /predict/file` (for batch uploads). Note: A `.xls` dataset sits in the codebase, but the file endpoint strictly parses `.csv` and `.json` files.
*   **Backend to ML Interface**: The backend utilizes a pre-trained scikit-learn Isolation Forest model loaded via `joblib` (`gnss_anti_spoofing_model.pkl`). Upon request, a preprocessing pipeline cleans and builds an exact 35-feature matrix mapped to `ALL_MODEL_FEATURES`, immediately passing it to `model.predict()` and `model.decision_function()` for synchronous inference. 
*   **Response Structure**: 
    *   Single injection returns a `predictions` array containing calculated booleans, raw decision fields, and a `features` mapping.
    *   Batch uploads return a `summary` object (count of samples, average anomaly score) and an array mapped to `timeline` representing the chronological data feed.

### 2. Frontend Architecture (React)
*   **Core UI Components**: The dashboard runs on a modern React "Bento Grid" component structure. Critical pieces include the `MainSummary` (header stats), `ActiveSatGrid` + `SatelliteCard` (signal sources), `FluidChart` (telemetry visualization), `AlertLog` (incident history), and `ModernInput` (file dropzone/sliders). **Note: No map components (like Leaflet or Mapbox) exist in the codebase.**
*   **Data Visualization Tooling**: Real-time signal points and anomalies are charted exclusively using **Recharts** (implemented as an `AreaChart` inside `FluidChart`), supported by **Framer Motion** for UI micro-animations. Client-side processing handles the timeline rendering. 
*   **Spoofed/Anomaly Alerting**: When the application parses an `is_spoofed === true` flag, the frontend automatically:
    1.  Triggers visual state changes throughout the component tree (swapping Recharts graph gradients and text tags to Red).
    2.  Pushes a "critical" incident alert asynchronously to the `AlertLog` with details on PRN/Scores.
    3.  Alters percentage widgets (e.g., Auth vs. Dropped metrics).

### 3. Performance & System Engineering
*   **State & Caching Mechanics**: **No external global state libraries (like Redux, Zustand) or explicit caching mechanisms (like Redis) are utilized.** The application purely relies on local React state hooks (`useState`) and context callbacks.
*   **Latency & Rendering Optimizations**: The team manages browser memory load between the heavy model payloads and the DOM via slicing constraints. **`useMemo`** acts as a localized optimization in the chart visualization, exclusively processing and rendering a sliding window of telemetry memory to maintain high framerates. 

### 4. Hardcoded Constants & Configurations
*   **Hardcoded API Payload Limits**: The FastApi backend safely truncates the outgoing batch timeline array specifically to a maximum of **200 data points** (`head(200)`).
*   **Alert Thresholds**: The Isolation Forest anomaly boundaries directly rely on the `-1` label for "Spoofed". The percentage-based anomaly score is derived via a static, hardcoded linear mapping: `ns = 1.0 - ((s + 0.2) / 0.4)` capped between 1.0 and 0.0. 
*   **Size Limits (Windowing)**: Both the backend rolling aggregations (for calculating rolling variance/means) and the UI `FluidChart` timeline bounds process data on hardcoded constraints — window size of **10** for ML time-series steps, and UI rendering sliced to the trailing **100** samples.
*   **Mock / Fallback Mechanisms**: 
    *   **Frontend Idle state**: The chart forcibly injects 20 samples of an animated, faked sine-wave metric (`score: 5 + Math.sin(i * 0.5) * 4`) if no actual telemetry data exists.
    *   **Default Injections**: The manual sidebar injection bounds user sliders via hardcoded assumptions (e.g., Carrier Doppler = 1500Hz, CN0 = 45).
    *   **Backend Inference Fail-safes**: If Transit Time cannot be extracted directly from timestamps, it falls back unconditionally to a constant of **$0.073$ seconds (73ms)**. Channels default to `"manual_0"`. 
