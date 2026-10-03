# Rivalry AI Architecture

Rivalry uses an internal AI gateway so product code is independent of the model provider.

## Flow

User message -> AI Gateway -> Responses API -> Rivalry tools/services -> evidence -> answer.

The AI must not be the source of truth. Rivalry services and normalized data are the source of truth.

## Model routing

- Chat: low-cost model for normal conversation.
- Intelligence: stronger model for change/cause analysis.
- Expert: strongest model for strategic consulting.

Model names are configuration, not business logic.

## Tool-first principle

The AI should retrieve only the evidence needed for a question:
- today's changes
- competitor history/patterns
- review trends
- cost/market signals

Future tools can add products, prices, promotions, predictions, outcomes, and business goals.

## Safety and trust

Responses must distinguish:
1. observed facts
2. estimates
3. hypotheses
4. recommendations

Competitor cost and margin are always estimates/ranges with confidence; never present inferred values as facts.

## Cost control

Do not call the AI for deterministic database operations. Route simple chat to the cheapest suitable model and reserve stronger models for intelligence and Expert consulting. Track token usage per request and enforce plan/usage limits at the application layer.
