---
name: technical-decision-helper
description: Help architects compare alternatives, evaluate trade-offs, and make documented technical decisions. Use when evaluating technologies, frameworks, patterns, or architectural choices.
license: MIT
compatibility: opencode
metadata:
  audience: architects
  workflow: design
---

# Technical Decision Helper

## When to Use This Skill
- You need to choose between multiple technologies, frameworks, libraries, or architectural patterns.
- You want to evaluate trade-offs between alternatives (e.g., performance vs complexity, cost vs features).
- You need to document architectural decisions for traceability and team alignment.
- You're evaluating options for: database selection, API design, messaging systems, deployment strategies, or architectural patterns.

## How This Skill Works
1. Define the decision context (what you're deciding, constraints, goals).
2. Identify alternatives to evaluate.
3. Establish evaluation criteria based on project requirements.
4. Score or assess each alternative against each criterion.
5. Synthesize results into a recommendation with clear rationale.
6. Output a structured decision record suitable for inclusion in architecture documents.

## Input
- **Decision statement**: A clear statement of what decision needs to be made (e.g., "Choose a message queue for inter-service communication").
- **Constraints**: Hard requirements that must be met (e.g., "must support exactly-once delivery", "must have client libraries for Python").
- **Goals/Non-functional requirements**: What you're optimizing for (e.g., "low latency", "high throughput", "operational simplicity").
- **Alternatives**: List of options to evaluate (if not provided, the skill can suggest common alternatives based on the decision statement).
- **Weighting** (optional): Relative importance of each criterion if using weighted scoring.

## Output
- A structured technical decision record in Markdown format, suitable for inclusion in:
  - TaskPlan.md (as part of architecture decisions)
  - DeveloperPrompt.md (to inform implementation choices)
  - Architecture Decision Record (ADR) files
  - development_log.md (to document decisions made)
- The record includes:
  - Context and problem statement
  - Considered alternatives
  - Evaluation criteria
  - Evaluation results (scores, pros/cons, etc.)
  - Decision outcome
  - Status (proposed, accepted, superseded)
  - Consequences
  - Related decisions

## Execution Steps

### Step 1: Clarify the Decision
1. Restate the decision in clear terms: "We need to choose [X] to achieve [Y] given [Z]."
2. Identify the trigger: What event or requirement necessitated this decision?
3. Define the scope: What is in/out of scope for this decision?
4. List any hard constraints (must-haves) that eliminate certain options immediately.

### Step 2: Identify Alternatives
If alternatives aren't provided:
- Suggest common options based on the decision domain (use knowledge of popular choices in the field).
- Include both mainstream and niche options if relevant.
- Consider the "do nothing" or "maintain status quo" alternative when applicable.
- For well-trodden decisions (e.g., SQL vs NoSQL), provide a standard shortlist.

### Step 3: Define Evaluation Criteria
Derive criteria from:
- Explicit requirements in the decision statement
- Non-functional requirements (performance, security, scalability, etc.)
- Project-specific constraints (team expertise, existing infrastructure, timeline)
- Operational considerations (monitoring, debugging, deployment)
- Future flexibility and evolution paths

Common criteria categories:
- **Functional fit**: Does it meet the core requirements?
- **Performance**: Latency, throughput, scalability characteristics.
- **Operational complexity**: Setup, monitoring, maintenance, debugging.
- **Team familiarity**: Existing expertise, learning curve, hiring implications.
- **Ecosystem & support**: Community size, documentation quality, commercial support.
- **Cost**: Licensing, infrastructure, operational expenses.
- **Integration effort**: Work required to connect with existing systems.
- **Risk**: Maturity, vendor stability, security track record.
- **Future-proofing**: Alignment with industry trends, upgrade paths.

### Step 4: Evaluate Alternatives
For each alternative against each criterion:
- Use a simple scale (e.g., 1-5, or ✓/✗/△) or qualitative assessment (Strong/Moderate/Weak).
- Provide brief justification for each rating.
- Note any assumptions made during evaluation.
- Highlight disqualifying factors (if an alternative fails a hard constraint).

### Step 5: Synthesize and Recommend
- Calculate total scores if using weighted scoring (optional).
- Identify clear winners or tiers of options.
- Note any close calls or significant trade-offs.
- Formulate a recommendation with clear rationale.
- Consider if the decision can be deferred or made reversible.

### Step 6: Document the Decision
Format the output as follows:

```markdown
## Technical Decision: [Clear statement of what was decided]

**Status**: [Proposed/Accepted/Superseded]  
**Date**: [YYYY-MM-DD]  
**Deciders**: [Roles or names involved]  
**Context**:  
[Brief description of the situation triggering this decision]

### Decision Statement
[Exactly what decision was made]

### Considered Alternatives
- [Alternative 1]: [Brief description]
- [Alternative 2]: [Brief description]
- [Alternative 3]: [Brief description]  
- ... 

### Evaluation Criteria
| Criterion | Weight (if used) | Why it matters |
|-----------|------------------|----------------|
| [Criterion 1] | [Weight] | [Explanation] |
| [Criterion 2] | [Weight] | [Explanation] |
| ... | ... | ... |

### Evaluation Results
| Alternative | [Criterion 1] | [Criterion 2] | ... | Notes |
|-------------|---------------|---------------|-----|-------|
| [Alt 1] | [Rating] | [Rating] | ... | [Justification] |
| [Alt 2] | [Rating] | [Rating] | ... | [Justification] |
| [Alt 3] | [Rating] | [Rating] | ... | [Justification] |

### Decision Outcome
**Chosen alternative**: [Selected option]  
**Rationale**:  
[Clear explanation of why this option was chosen over others, referencing specific criteria]

### Consequences
- **Positive outcomes**: [Expected benefits of this choice]
- **Negative outcomes**: [Known drawbacks or costs accepted]
- **Mitigations**: [How downsides will be addressed]

### Related Decisions
- [Links or references to other decisions this depends on or affects]
- [Any follow-up decisions needed]

### Assumptions
[List any key assumptions that, if changed, would require revisiting this decision]
```

## Quality Criteria
- The decision record must be **actionable and traceable** – future team members should understand why a choice was made.
- All evaluations must be **justified** – avoid unsupported claims like "Option X is better" without explanation.
- The skill should **facilitate, not replace** judgment – it structures thinking but doesn't automate the decision.
- For well-known decisions, leverage established industry knowledge (e.g., "For high-frequency trading systems, low-latency IPC often favors shared memory over message queues").
- If insufficient information exists to make a recommendation, the skill should state what additional data is needed.

## Usage Example
> I will use the technical-decision-helper skill to choose a message queue for inter-service communication in our trading system.
>
> Input:  
> "We need to select a message queue to decouple our market data ingestion service from our strategy engine. Requirements: must handle bursts of up to 100K messages/sec during market open, provide at-least-once delivery, have Python client libraries, and integrate with our Docker-based deployment. Team has moderate experience with Redis but none with Kafka or RabbitMQ."
>
> Output:
> ```markdown
> ## Technical Decision: Message Queue for Market Data -> Strategy Engine Communication
> 
> **Status**: Accepted  
> **Date**: 2026-05-10  
> **Deciders**: Lead Architect, Senior Developer  
> **Context**: Market data bursts during open require reliable buffering between ingest and strategy services to prevent data loss during processing spikes.
> 
> ### Decision Statement
> Choose a message queue technology for communication between Market Data Ingest Service and Strategy Engine Service.
> 
> ### Considered Alternatives
> - Redis Pub/Sub (using existing Redis infrastructure)
> - Apache Kafka (industry standard for high-throughput event streaming)
> - RabbitMQ (mature, feature-rich message broker)
> - AWS SQS/SNS (if considering cloud-native, but we're on-prem)
> - ZeroMQ (low-latency, but requires more custom reliability logic)
> 
> ### Evaluation Criteria
> | Criterion | Weight | Why it matters |
> |-----------|--------|----------------|
> | Throughput & Latency | 30% | Must handle market open bursts without becoming bottleneck |
> | Operational Complexity | 20% | Team has limited DevOps bandwidth |
> | Python Client Quality | 15% | Both services are Python-based |
> | Reliability & Durability | 20% | Cannot lose market data ticks |
> | Existing Infrastructure Fit | 15% | We already run Redis for caching |
> 
> ### Evaluation Results
> | Alternative | Throughput & Latency | Operational Complexity | Python Client Quality | Reliability & Durability | Existing Infrastructure Fit | Notes |
> |-------------|----------------------|------------------------|-----------------------|--------------------------|-----------------------------|-------|
> | Redis Pub/Sub | △ (Good for bursts but limited persistence) | ✓ (Team knows it) | ✓ (redis-py is mature) | △ (No persistence by default; can lose data on restart) | ✓ (Already deployed) | Would need to enable persistence and tune for our volume |
> | Kafka | ✓✓ (Designed for high throughput) | △ (Operational overhead: Zookeeper, tuning) | ✓ (confluent-kafka-python is solid) | ✓✓ (Strong durability guarantees) | △ (New infrastructure to manage) | Overkill for our use case; adds significant ops burden |
> | RabbitMQ | ✓ (Good throughput) | ✓ (Familiar to many; good tooling) | ✓ (pika is adequate) | ✓✓ (Excellent reliability features: acks, persistence, clustering) | △ (New service to run) | Solid middle ground; more features than we need but very reliable |
> | ZeroMQ | ✓✓ (Very low latency) | ✗ (Requires building reliability layer ourselves) | ✓ (pyzmq exists) | △ (No built-in persistence; message loss on crash) | △ (New paradigm for team) | Too much DIY reliability work; not suitable for critical data path |
> 
> ### Decision Outcome
> **Chosen alternative**: Redis Pub/Sub with persistence enabled  
> **Rationale**:  
> While Kafka offers superior durability and RabbitMQ excellent reliability, Redis Pub/Sub provides the best balance for our specific context:  
> - It meets our throughput needs (easily handles 100K msg/sec with proper tuning)  
> - Leverages existing infrastructure and team knowledge (reducing operational burden)  
> - With persistence enabled (using AOF or RDB snapshots) and proper client-side handling, it provides sufficient reliability for our use case  
> - The operational simplicity outweighs the marginal gains of alternatives for our current scale  
> - We can re-evaluate if throughput requirements grow significantly beyond current projections  
> 
> ### Consequences
> - **Positive outcomes**: Faster time to implementation, lower operational overhead, team can focus on core trading logic  
> - **Negative outcomes**: Less impressive peak throughput headroom than Kafka; requires careful client-side error handling to avoid data loss  
> - **Mitigations**: Implement idempotent processing in strategy engine; add application-level sequence numbers to detect gaps; monitor Redis persistence and memory usage closely  
> 
> ### Related Decisions
> - Depends on: Decision to use Docker for containerization (provides consistent deployment environment)  
> - Related to: Future decision on market data storage technology (may influence persistence needs)  
> - Follow-up: Need to document Redis configuration and tuning parameters in our deployment docs  
> 
> ### Assumptions
> - Market open bursts will not regularly exceed 200K msg/sec for the next 12-18 months  
> - Team is willing to invest time in learning optimal Redis Pub/Sub patterns for this use case  
> - No regulatory requirement for guaranteed delivery that would necessitate stronger durability guarantees  
> ```