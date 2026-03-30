<!-- Risk control flow diagram for OrganBriefOptimization Phase 4 -->

# Risk Control Flow Diagram

Below is the canonical flow for content risk-control processing. It shows the sequence of components and decision points applied to LLM-generated output before storage or manual review.

```mermaid
flowchart TD
  A[LLM output] --> B[tokenization / token_manager]
  B --> C[regex scanner (sensitive/banned/watch lists)]
  C --> D[competitor filter (masking & special rules)]
  D --> E[html sanitizer (bleach)]
  E --> F[risk decision (scoring & rules)]
  F --> |HIGH risk & requires review| G[PENDING (manual review queue)]
  F --> |AUTO-REJECT| H[REJECTED (do not store)]
  F --> |AUTO-APPROVE| I[APPROVED (store sanitized content)]
  G --> J[audit log]
  H --> J
  I --> J

  style A fill:#f9f,stroke:#333,stroke-width:1px
  style J fill:#eef,stroke:#333,stroke-width:1px
```

Notes:
- Tokenization/normalization is performed first to make keyword scanning robust (NFKC normalization, case-folding, full-width/half-width mapping).
- The regex scanner consults three typed lists in config/risk_control (banned, sensitive/watch, low) and produces match outputs and preliminary scores.
- Competitor filter handles matches to competitor names: masking (default: replace with '***') and forces manual review (PENDING) rather than auto-approve.
- HTML sanitizer (bleach) is applied after masking to ensure stored HTML is safe.
- Risk decision applies deterministic rules (see docs for thresholds). Actions: APPROVED (store), REJECTED (throw away / surface rejection), PENDING (send to human review queue). All outcomes are logged to audit log with matched keywords and decision rationale.
