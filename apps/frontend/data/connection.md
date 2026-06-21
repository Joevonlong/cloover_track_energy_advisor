# Frontend Data Connection

## Goal

Connect the frontend to the backend recommendation pipeline so the user can see the work starting, running in parallel, being monitored, moving through each layer, and producing accepted, rejected, or error results in real time.

The UI should not only show a final recommendation. The main product value is showing what is actually happening behind the scenes. This should feel like a live control room: many checks start, some run in parallel, some wait for dependencies, some retry or fall back, and the system keeps monitoring all of it until a final plan is assembled.

- the parent orchestration layer starts the run
- independent checks start in parallel when possible
- dependent layers wait for required outputs
- the user sees which workers are active, queued, blocked, completed, or failed
- the solar layer shows its internal steps while other checks may already be running
- the output moves into the battery layer and later layers
- the subsidy crawler checks database, internet, PDFs, and Supabase
- monitoring events show retries, fallback decisions, source latency, and partial results
- each layer resolves to accepted, rejected, skipped, or error
- the final recommendation is assembled from the layer outputs

## Frontend Surfaces

The connected experience needs three synchronized surfaces:

1. `ActivityFeed`
   - Text timeline of backend events.
   - Shows current source, action, status, timestamp, and details.
   - Shows parallel work clearly, for example multiple running rows grouped by layer.

2. Remotion layer animation
   - Visualizes the pipeline moving from parent layer to child layers.
   - Shows tokens/data packets flowing from one layer to the next.
   - Highlights the currently active layer and step.
   - Shows multiple active nodes at once when backend work is parallel.

3. Result/proposal UI
   - Uses completed layer outputs.
   - Shows accepted/rejected/error states for solar, battery, heat pump, EV charger, subsidy, permit, and financing.

All three surfaces should consume the same run event stream.

## Experience Principle

The user should understand that Heimwende is doing real work, not displaying a fake loading spinner.

The UI should make these facts visible:

- sources are being checked, not guessed
- several workers can run at the same time
- each worker has a clear job
- the system monitors progress and failures
- external services can be slow, missing, or partial
- failures do not always kill the run; some layers can continue with fallbacks
- the final proposal is the result of many small verified decisions

Avoid generic status text like `Analyzing...` when a specific status is available. Prefer concrete text:

- `Google Solar · Fetching roof polygon`
- `Engine · Calculating usable south-facing area`
- `Supabase · Checking subsidy catalog`
- `PDF · Reading eligibility rules`
- `Monitor · Google Solar response took 1.8s`
- `Fallback · Continuing without confirmed subsidy amount`

## Pipeline Model

The backend should emit one `run` with nested layers.

```ts
type LayerId =
  | "parent"
  | "solar"
  | "battery"
  | "heat_pump"
  | "ev_charger"
  | "subsidy"
  | "permit"
  | "financing";

type LayerStatus =
  | "queued"
  | "running"
  | "accepted"
  | "rejected"
  | "skipped"
  | "error";

type StepStatus =
  | "queued"
  | "running"
  | "ok"
  | "warn"
  | "error";
```

## Event Contract

The backend should stream events over SSE first. WebSocket can come later if bidirectional control is needed.

Endpoint:

```txt
GET /api/v1/advisor/runs/:runId/events
```

Initial run request:

```txt
POST /api/v1/advisor/recommend
```

Response should include:

```ts
interface StartRecommendationResponse {
  runId: string;
}
```

Each streamed event:

```ts
interface PipelineEvent {
  id: string;
  runId: string;
  timestamp: string;
  layerId: LayerId;
  parentLayerId?: LayerId;
  stepId?: string;
  workerId?: string;
  type:
    | "run_started"
    | "layer_started"
    | "worker_started"
    | "worker_heartbeat"
    | "worker_completed"
    | "step_started"
    | "step_progress"
    | "step_completed"
    | "dependency_waiting"
    | "dependency_resolved"
    | "monitor_notice"
    | "fallback_used"
    | "layer_completed"
    | "layer_error"
    | "run_completed"
    | "run_error";
  status: LayerStatus | StepStatus;
  title: string;
  detail?: string;
  source?: "database" | "internet" | "pdf" | "google_solar" | "supabase" | "engine" | "crawler";
  payload?: Record<string, unknown>;
}
```

Frontend mapping:

- `layerId` drives which Remotion node is highlighted.
- `stepId` drives which internal layer step is highlighted.
- `workerId` identifies parallel work inside the same layer.
- `title` and `detail` drive the activity row.
- `source` drives the activity icon.
- `status` drives the visual state.
- `payload` carries structured data for layer-specific UI.

## Parallel Work and Monitoring

The backend should emit enough events for the frontend to show concurrency honestly.

Examples of parallel work:

- parent checks cached data while starting online lookups
- solar starts Google Solar data fetch while tariff/subsidy metadata is loaded
- subsidy checks Supabase while internet search gathers updated sources
- permit and subsidy can run alongside financing pre-checks once product candidates exist
- heat pump and EV charger checks can run independently from the solar-to-battery path

The frontend should show this as multiple active workers, not as one fake sequential progress bar.

```ts
interface WorkerState {
  id: string;
  layerId: LayerId;
  label: string;
  source: PipelineEvent["source"];
  status: "queued" | "running" | "ok" | "warn" | "error";
  startedAt?: string;
  lastHeartbeatAt?: string;
  completedAt?: string;
  detail?: string;
}
```

Monitoring events should be first-class UI events.

Use monitoring for:

- external API latency
- crawler retry attempts
- missing source data
- fallback decisions
- dependency waits
- partial result warnings
- source confidence changes

Example monitor events:

```json
{
  "type": "worker_heartbeat",
  "layerId": "solar",
  "workerId": "google_solar",
  "status": "running",
  "title": "Google Solar still running",
  "detail": "Waiting for roof geometry response.",
  "source": "google_solar",
  "payload": {
    "elapsedMs": 1800
  }
}
```

```json
{
  "type": "dependency_waiting",
  "layerId": "battery",
  "parentLayerId": "solar",
  "status": "queued",
  "title": "Battery waiting for solar output",
  "detail": "Storage sizing starts after PV potential is known.",
  "source": "engine"
}
```

```json
{
  "type": "fallback_used",
  "layerId": "subsidy",
  "stepId": "pdf_read",
  "status": "warn",
  "title": "Fallback used",
  "detail": "PDF source timed out. Continuing with cached Supabase catalog.",
  "source": "pdf",
  "payload": {
    "fallback": "supabase_catalog",
    "continuable": true
  }
}
```

UI requirements:

- show a small `Running in parallel` indicator when more than one worker is active
- show worker count, for example `4 active checks`
- show queued dependencies explicitly, not as silence
- show monitoring notices in the feed with a distinct icon
- show fallback events as warnings, not hard errors
- keep completed worker rows visible long enough for the user to understand progress

## Parent Layer

The parent layer is the orchestrator. It should show what the system is checking before or while delegating to specific layers.

Parent layer steps:

```ts
const parentSteps = [
  {
    id: "database_lookup",
    label: "Looking in database",
    source: "database",
  },
  {
    id: "internet_search",
    label: "Searching the internet",
    source: "internet",
  },
  {
    id: "pdf_read",
    label: "Reading PDF documents",
    source: "pdf",
  },
  {
    id: "route_layers",
    label: "Routing data to product layers",
    source: "engine",
  },
];
```

Expected UI:

- parent node pulses while active
- current sub-step is visible in the feed
- when parent sends data to a child layer, Remotion animates a packet from `parent` to that layer
- if parent fails to gather required context, the run enters `run_error`

Example events:

```json
{
  "type": "step_started",
  "layerId": "parent",
  "stepId": "database_lookup",
  "status": "running",
  "title": "Looking in database",
  "detail": "Checking cached tariff, subsidy, permit, and site data.",
  "source": "database"
}
```

```json
{
  "type": "step_completed",
  "layerId": "parent",
  "stepId": "pdf_read",
  "status": "ok",
  "title": "PDF read complete",
  "detail": "Found subsidy rules for the household postcode.",
  "source": "pdf"
}
```

## Solar Layer

The solar layer should make the behind-the-scenes roof analysis visible.

Solar layer steps:

```ts
const solarSteps = [
  {
    id: "google_solar_crawl",
    label: "Crawling Google Solar",
    source: "google_solar",
  },
  {
    id: "roof_geometry",
    label: "Calculating roof angle, area, and usable surface",
    source: "engine",
  },
  {
    id: "orientation",
    label: "Determining roof orientation",
    source: "engine",
  },
  {
    id: "yield_estimate",
    label: "Estimating yearly PV yield",
    source: "engine",
  },
  {
    id: "solar_decision",
    label: "Deciding if solar is accepted",
    source: "engine",
  },
];
```

Important solar payload fields:

```ts
interface SolarPayload {
  roofAreaM2?: number;
  usableAreaM2?: number;
  pitchDeg?: number;
  azimuthDeg?: number;
  orientation?: "south" | "south_east" | "south_west" | "east" | "west" | "north" | "unknown";
  potentialKwp?: number;
  yearlyYieldKwh?: number;
  accepted?: boolean;
  rejectionReason?: string;
}
```

Accepted example:

```json
{
  "type": "layer_completed",
  "layerId": "solar",
  "parentLayerId": "parent",
  "status": "accepted",
  "title": "Solar accepted",
  "detail": "South-facing roof with 8.6 kWp potential.",
  "payload": {
    "orientation": "south",
    "potentialKwp": 8.6,
    "usableAreaM2": 42,
    "accepted": true
  }
}
```

Rejected example:

```json
{
  "type": "layer_completed",
  "layerId": "solar",
  "parentLayerId": "parent",
  "status": "rejected",
  "title": "Solar rejected",
  "detail": "Usable roof surface is below the minimum threshold.",
  "payload": {
    "usableAreaM2": 8,
    "accepted": false,
    "rejectionReason": "Roof area too small"
  }
}
```

Error example:

```json
{
  "type": "layer_error",
  "layerId": "solar",
  "parentLayerId": "parent",
  "status": "error",
  "title": "Google Solar lookup failed",
  "detail": "No roof data returned for the address.",
  "source": "google_solar"
}
```

## Battery Layer

The battery layer should start only after solar output exists, unless the user already has PV data.

Input:

- solar potential
- expected PV yield
- household electricity demand
- self-consumption estimate

Battery steps:

```ts
const batterySteps = [
  { id: "receive_solar_output", label: "Receiving solar output", source: "engine" },
  { id: "load_profile", label: "Building household load profile", source: "engine" },
  { id: "battery_size", label: "Calculating battery size", source: "engine" },
  { id: "battery_decision", label: "Deciding if storage is accepted", source: "engine" },
];
```

UI behavior:

- Remotion animates output from `solar` to `battery`.
- Battery node stays queued until solar is accepted or skipped with existing PV data.
- If solar is rejected and no existing PV exists, battery should become `skipped`.

## Subsidy Crawler Layer

The subsidy layer should make crawler work explicit. It should show whether the backend is checking cached data, internet sources, PDFs, and Supabase.

Subsidy steps:

```ts
const subsidySteps = [
  { id: "supabase_lookup", label: "Checking Supabase subsidy catalog", source: "supabase" },
  { id: "internet_search", label: "Searching subsidy sources online", source: "internet" },
  { id: "pdf_read", label: "Reading subsidy PDF", source: "pdf" },
  { id: "eligibility_rules", label: "Evaluating household eligibility", source: "engine" },
  { id: "subsidy_decision", label: "Calculating accepted subsidy amount", source: "engine" },
];
```

Important subsidy payload fields:

```ts
interface SubsidyPayload {
  catalogHit?: boolean;
  sourceUrl?: string;
  pdfTitle?: string;
  programName?: string;
  eligible?: boolean;
  amountEur?: number;
  rejectionReason?: string;
}
```

UI behavior:

- show `Supabase` as a distinct destination/source
- show PDF read as its own event, not hidden inside the crawler
- show accepted subsidy amount when eligibility succeeds
- show rejected state with reason when not eligible
- show warning state if source data is partial but the run can continue

## Other Layers

Future layers should follow the same model:

```ts
interface LayerDefinition {
  id: LayerId;
  label: string;
  dependsOn: LayerId[];
  steps: {
    id: string;
    label: string;
    source: PipelineEvent["source"];
  }[];
}
```

Expected dependencies:

```ts
const layerDependencies = {
  parent: [],
  solar: ["parent"],
  battery: ["solar"],
  heat_pump: ["parent"],
  ev_charger: ["parent"],
  subsidy: ["solar", "battery", "heat_pump", "ev_charger"],
  permit: ["solar", "heat_pump", "ev_charger"],
  financing: ["solar", "battery", "heat_pump", "ev_charger", "subsidy"],
};
```

## Status Rules

Use the same state language everywhere.

```ts
const statusPresentation = {
  queued: "Muted node, no spinner",
  running: "Active node, spinner, animated packet",
  accepted: "Green check",
  rejected: "Amber or red rejected badge with reason",
  skipped: "Muted skipped badge",
  error: "Red error state with retry/support detail",
};
```

Rules:

- `running` means backend work is actively happening.
- `accepted` means this layer contributes to the final proposal.
- `rejected` means the layer ran successfully but should not be offered.
- `skipped` means the layer did not run because a dependency rejected it or input was missing.
- `error` means the layer failed unexpectedly or an external source failed.

## Frontend Store Shape

The frontend should convert the event stream into a run state.

```ts
interface PipelineRunState {
  runId: string;
  status: "idle" | "running" | "completed" | "error";
  activeLayerIds: LayerId[];
  activeWorkerIds: string[];
  layers: Record<LayerId, LayerState>;
  workers: Record<string, WorkerState>;
  monitorNotices: PipelineEvent[];
  events: PipelineEvent[];
  result?: Recommendation;
}

interface LayerState {
  id: LayerId;
  status: LayerStatus;
  startedAt?: string;
  completedAt?: string;
  activeStepIds: string[];
  workerIds: string[];
  steps: Record<string, StepState>;
  output?: Record<string, unknown>;
  error?: string;
}

interface StepState {
  id: string;
  status: StepStatus;
  title: string;
  detail?: string;
  source?: PipelineEvent["source"];
  output?: Record<string, unknown>;
}
```

## Remotion Animation Mapping

The Remotion scene should be a deterministic visualization of `PipelineRunState`.

Scene objects:

- parent layer node
- child layer nodes
- animated packet between nodes
- active worker lanes inside each layer
- active step labels
- source icons: database, internet, PDF, Google Solar, Supabase, engine
- status badges
- monitor strip showing active checks, warnings, retries, and fallbacks

Animation rules:

- `layer_started`: highlight layer node and fade in step list
- `worker_started`: create an active worker lane in the layer
- `worker_heartbeat`: keep the worker lane alive and update elapsed/monitor detail
- `worker_completed`: resolve the worker lane to ok/warn/error
- `step_started`: pulse current step row
- `step_completed`: check the step row
- `dependency_waiting`: show a queued edge between dependent layers
- `dependency_resolved`: animate data packet into the unblocked layer
- `monitor_notice`: add a short-lived notice to the monitor strip
- `fallback_used`: mark the relevant branch with a warning but keep the run moving
- `layer_completed`: move packet from layer to dependent layers
- `layer_error`: shake or flash the layer node once, then hold red error state
- `run_completed`: all nodes settle, final proposal card appears

The animation should not invent state. It should render only what the backend event stream says happened.

Parallel animation requirements:

- multiple nodes can be highlighted at the same time
- multiple packet animations can run at the same time
- queued nodes should visibly wait on dependency edges
- completed branches should remain visible as evidence of work already done
- monitor notices should feel operational, not decorative

## Activity Feed Mapping

Current `ActivityFeed` can be extended from flat events to pipeline events.

Mapping:

```ts
function toActivityEvent(event: PipelineEvent): ActivityEvent {
  return {
    id: event.id,
    timestamp: formatTime(event.timestamp),
    source: event.source ? sourceLabel(event.source) : layerLabel(event.layerId),
    label: event.workerId
      ? `${workerLabel(event.workerId)} · ${event.detail ?? event.title}`
      : event.detail ?? event.title,
    status:
      event.status === "error" || event.type === "fallback_used"
        ? "warn"
        : event.status === "running"
          ? "loading"
          : event.status === "accepted" || event.status === "ok"
            ? "ok"
            : "info",
  };
}
```

The feed should always show the backend source in the row detail or icon, for example:

- `Database · Checking cached tariff data`
- `Google Solar · Crawling roof potential`
- `Engine · Calculating pitch, area, and orientation`
- `PDF · Reading subsidy eligibility`
- `Supabase · Persisting subsidy match`
- `Monitor · 4 active checks running`
- `Fallback · Continuing with cached catalog`

Feed grouping:

- newest events stay visible at top or bottom consistently
- active workers should be grouped by layer when several are running
- monitoring notices should be visually quieter than layer decisions
- accepted/rejected/error layer decisions should be visually stronger than heartbeat events
- if more than one worker is active, show a compact summary such as `4 checks running in parallel`

## Error Handling

Errors must stay visible and explain what failed.

Error UI requirements:

- show the failed layer
- show the failed step
- show source if available
- show whether the run can continue
- show fallback if used
- show final result as partial if some layers succeeded

Example partial run:

```json
{
  "type": "layer_error",
  "layerId": "subsidy",
  "status": "error",
  "title": "Subsidy crawler failed",
  "detail": "PDF source timed out. Continuing without confirmed subsidy.",
  "source": "pdf",
  "payload": {
    "continuable": true,
    "fallback": "No subsidy applied"
  }
}
```

## Implementation Order

1. Backend returns `runId` from `POST /api/v1/advisor/recommend`.
2. Backend exposes SSE endpoint for `PipelineEvent`.
3. Frontend adds `usePipelineRun(runId)` to connect to SSE.
4. Frontend stores events in `PipelineRunState`.
5. Frontend derives active workers, active layers, dependency waits, and monitor notices.
6. `ActivityFeed` renders mapped pipeline events and parallel worker groups.
7. Remotion scene renders the same `PipelineRunState`.
8. Final result UI reads completed layer outputs and final `Recommendation`.
9. Add partial-result behavior for rejected/skipped/error layers.

## Acceptance Criteria

- Starting a recommendation immediately creates a visible live run.
- The user can see that background work is real, specific, and source-based.
- Parallel checks are visible when multiple backend workers are active.
- The UI shows active, queued, blocked, completed, warning, and failed work.
- Monitoring events show latency, retries, fallbacks, and partial results.
- Parent layer shows database, internet, and PDF checks.
- Solar layer shows Google crawl, roof geometry, angle/area, orientation, and decision.
- Solar accepted/rejected/error states are visible and explain why.
- Battery layer receives solar output visually and in state.
- Subsidy layer shows Supabase, internet, and PDF activity.
- Final UI shows which products were accepted, rejected, skipped, or errored.
- Activity feed and Remotion animation never disagree because they use the same event stream.
