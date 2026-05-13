---
name: architecture-reviewer
description: Review architecture designs for best practices, trade-offs, and potential issues. Use when you need to validate a proposed architecture, identify technical debt, or ensure alignment with non‑functional requirements (performance, security, scalability, etc.).
license: MIT
compatibility: opencode
metadata:
  audience: architects
  workflow: review
---

# Architecture Reviewer

## When to Use This Skill
- You have an architecture description, diagram, or set of components and want to verify it follows established best practices.
- You need to identify potential problems before implementation (e.g., tight coupling, single points of failure, missing error handling, performance bottlenecks).
- You want a structured review that produces actionable improvement suggestions.

## How This Skill Works
1. Parse the supplied architecture (textual description, bullet list, or Mermaid diagram) into a logical model of components, interfaces, data flows, and deployment nodes.
2. Evaluate the model against a checklist of architectural quality attributes.
3. Generate a report that lists:
   - ✅ What is done well (strengths).
   - ⚠️ What needs improvement (weaknesses) with severity and suggested fixes.
   - 🔀 Trade‑off considerations if multiple valid alternatives exist.
4. Output the report in Markdown format, suitable for inclusion in TaskPlan.md, DeveloperPrompt.md, or an architecture decision record.

## Input
- **Architecture description**: A natural‑language description, list of components, or a Mermaid diagram (the skill can read Mermaid syntax to extract elements).
- **Focus areas** (optional): Comma‑separated list of qualities to emphasise, e.g., `performance,security,scalability`. If omitted, all standard categories are checked.
- **Project context** (optional): Any constraints specific to EA_trade_bot, such as “must integrate with MT5 API”, “must run inside Docker/LXD”, “end‑to‑end latency < 100ms”, “must support hot‑swap of strategies”.

## Output
- A Markdown section containing:
  - **Summary**: overall verdict (e.g., “Architecture is sound with minor improvements needed”).
  - **Strengths**: bullet list of things the design does correctly.
  - **Weaknesses**: bullet list, each with:
    - **Issue**: short description.
    - **Impact**: what could happen if not addressed.
    - **Suggestion**: concrete remediation or alternative.
  - **Trade‑offs** (if applicable): table or list comparing alternative approaches.
  - **Next steps**: optional recommended actions (e.g., “run a spike on Kafka vs. Pulsar for the event bus”).
- No files are modified; the skill returns only the review text.

## Execution Steps

### Step 1: Normalise the Input
1. If the input is a Mermaid diagram, extract:
   - Nodes → components/services.
   - Edges → interactions (data flow, calls, events).
   - Sub‑graphs → grouping or deployment zones.
2. If the input is plain text, identify:
   - **Entities** (nouns): services, modules, databases, APIs, external systems.
   - **Relationships** (verbs/phrases): sends data to, calls, reads from, writes to, triggers, subscribes to, publishes.
   - **Groups** (explicit or implied): e.g., “inside the Docker network”, “within the Kubernetes pod”.

### Step 2: Build a Logical Model
Create a simple internal representation:
- **Components**: each with a name and optional responsibilities.
- **Interfaces**: directional links between components, labelled with the type of interaction (sync/async, request/response, event stream).
- **Data stores**: databases, caches, file systems.
- **External systems**: MT5 API, exchange WebSocket, third‑party services.
- **Deployment nodes** (if derivable): Docker containers, VMs, Kubernetes pods.

### Step 3: Apply the Review Checklist
Evaluate the model against the following categories. For each, note findings, impact, and suggestions.

| Category | What to Look For | Typical Issues | Example Suggestions |
|----------|------------------|----------------|----------------------|
| **Modularity & Coupling** | Are responsibilities clearly separated? Are interfaces well‑defined? | God components, bidirectional dependencies, leaky abstractions. | Split large components; introduce façade or anti‑corruption layers; depend on interfaces, not implementations. |
| **Data Flow & Integrity** | Is data moved correctly? Are transformations documented? | Lossy conversions, missing validation, unclear ownership. | Add schema validation at boundaries; use immutable data objects where possible; document each transformation step. |
| **Error Handling & Fault Tolerance** | How are exceptions, timeouts, and external failures handled? | Swallowed exceptions, retry loops without back‑off, no circuit breaker. | Centralise error handling; add timeouts, retries with exponential back‑off; implement circuit breaker pattern for external calls (MT5, exchange APIs). |
| **Performance & Latency** | Is the critical path optimised? Are there unnecessary hops or serialisations? | Multiple JSON serialisations, synchronous calls that could be async, blocking I/O in latency‑sensitive path. | Move to binary protobuf for internal services; make non‑essential calls async; cache frequent look‑ups; co‑locate latency‑critical components. |
| **Scalability & Elasticity** | Can the system handle increased load by adding instances? | Stateful components, shared mutable caches, single‑writer bottlenecks. | Stateless services where possible; use distributed caches or partitioned databases; shard by strategy or symbol; employ load balancer. |
| **Observability** | Are metrics, logs, and traces available for key interactions? | Missing latency metrics, no error counters, no request IDs. | Export Prometheus metrics (request count, latency, error rate); enforce trace‑ID propagation; structured logging with correlation IDs. |
| **Security** | Are authentication, authorization, encryption, and input validation in place? | Hard‑coded secrets, lack of TLS, missing validation leading to injection attacks. | Use environment variables or secret manager for credentials; enforce mTLS between services; validate all external inputs; apply principle of least privilege. |
| **MT5 Integration Specifics** | Does the architecture respect MT5’s single‑threaded nature and API limits? | Blocking MT5 calls on main thread, excessive API polling, no rate‑limiting. | Offload MT5 communication to a dedicated bridge thread/process; use a queue for commands; implement API call throttling and heartbeat monitoring. |
| **Deployment & Operability** | Is the system easy to build, test, and deploy? | Manual steps, environment drift, missing health checks. | Provide Docker‑Compose or Helm chart; include readiness/liveness probes; automate with CI/CD pipeline; use configuration‑as‑code (YAML/ENV). |
| **Trade‑off Awareness** | Have major alternatives been considered and documented? | Choices made without noting pros/cons, hidden assumptions. | Add an ADR (Architecture Decision Record) for significant choices (e.g., “Use gRPC vs REST for internal service communication”). |

### Step 4: Generate the Report
Produce a Markdown section like the following template:

```markdown
### Architecture Review

**Summary:**  
[Short overall assessment.]

**Strengths:**  
- [Strength 1]  
- [Strength 2]  

**Weaknesses:**  
- **Issue:** [Description]  
  **Impact:** [What could go wrong]  
  **Suggestion:** [Concrete action]  

- **Issue:** [Description]  
  **Impact:** [What could go wrong]  
  **Suggestion:** [Concrete action]  

**Trade‑offs (if any):**  
| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| Option A | … | … | … |
| Option B | … | … | … |

**Next Steps:**  
- [Action 1]  
- [Action 2]  
```

## Quality Criteria
- The review must be **actionable**: each weakness includes a clear, specific suggestion that an architect or developer can implement.
- All feedback must be **traceable** back to the input description or diagram.
- The skill should **not** introduce new components or changes that were not implied by the input; it only evaluates and advises.
- Tone should be professional, constructive, and focused on improving the architecture, not assigning blame.

## Usage Example
> I will use the architecture-reviewer skill to check the proposed order‑execution pipeline.
>
> Input:  
> “Market data arrives via WebSocket → Pre‑processor → Strategy Engine generates signal → Risk Manager validates → Order Sender sends to MT5 → Position tracker updates. All components run as separate Docker containers on a single host, communicating via REST over HTTP.”
>
> Output:
> ```markdown
> ### Architecture Review
>
> **Summary:**  
> The pipeline captures the essential flow but couples components tightly via synchronous REST, which may affect latency and fault tolerance.
>
> **Strengths:**  
> - Clear separation of concerns (ingest, processing, risk, execution, tracking).  
> - Each component is a distinct Docker container, enabling independent scaling and deployment.
>
> **Weaknesses:**  
> - **Issue:** All inter‑component communication uses synchronous REST/HTTP.  
>   **Impact:** Adds latency (serialization, network round‑trip) and creates a cascade of failures if any container is temporarily unavailable.  
>   **Suggestion:** Replace REST with a lightweight binary protocol (e.g., gRPC or protobuf over TCP) or use an internal message bus (e.g., NATS, Redis Pub/Sub) for async communication.  
> - **Issue:** No explicit error handling or retry logic is mentioned for the MT5 API call.  
>   **Impact:** Transient MT5 errors could cause orders to be lost or duplicated.  
>   **Suggestion:** Introduce a retry mechanism with exponential back‑off and a circuit‑breaker pattern; log all failures and send alerts for manual inspection when the circuit opens.
>
> **Trade‑offs:**  
> | Option | Pros | Cons | Recommendation |
> |--------|------|------|----------------|
> | Sync REST | Simple to implement, easy to debug. | Higher latency, tight coupling, failure propagation. | Not recommended for latency‑sensitive path. |
> | Async Message Bus | Decouples components, buffers bursts, improves fault tolerance. | Requires additional infrastructure, slightly more complex monitoring. | **Recommended** for the core pipeline. |
> - **Next Steps:**  
>   1. Spike a protobuf‑based gRPC service between Strategy Engine and Risk Manager.  
>   2. Add a retry‑with‑back‑off wrapper around the MT5 Order Sender client.  
>   3. Update the sequence diagram in the architecture doc to reflect the async message bus.  
> ```