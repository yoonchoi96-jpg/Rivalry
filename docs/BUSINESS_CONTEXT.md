# Business Context Foundation

Rivalry does not use a fixed onboarding questionnaire.

The system first gathers information it can obtain automatically, then asks only for
the missing information required for the current decision. Question depth is selected
from multiple dimensions:

- business model
- business size
- operational complexity
- geographic scope
- product breadth
- customer scale
- supply-chain complexity
- channels
- organization complexity
- decision complexity
- user role
- current goal

## Depth model

1. Business identification
2. Basic business structure
3. Current goal
4. Revenue and cost structure
5. Competition and market structure
6. Causal structure
7. Strategic decision context

The planner is intentionally deterministic at this stage. It produces a depth and
candidate topics; the future Intent Engine and Research Planner can use those outputs
to decide whether a topic should be inferred, researched, or asked.

### Non-negotiable rule

**Size is never a proxy for complexity.**

A small international importer can require deeper context than a large simple local
operation.

This module is a foundation for the Universal Engine + Industry Lens + Business Lens
architecture. Industry-specific differences should be represented as declarative
policies rather than branching the core around restaurant/cafe/ecommerce/etc.
