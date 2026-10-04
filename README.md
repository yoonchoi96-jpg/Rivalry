# Rivalry

AI-native global competitive intelligence platform.

## Product direction

Rivalry starts with conversational onboarding: understand the business, country, channels, sales/delivery platforms, source documents, competitors, priorities, and business goals. Platform-specific adapters then collect permitted data into a common model.

The intelligence loop is:

**collect → normalize → detect change → score impact → explain causes → predict → recommend → learn**

Tracked signals are designed to grow beyond price into products, promotions, reviews, ratings, customer sentiment, market signals, ingredient/input costs, property/operating costs, and other evidence that can explain *why* a competitor changed.

## Global architecture

Country and platform differences belong in adapters, not in the core intelligence engine. The core uses a platform-agnostic data model so new countries can be added without rewriting business logic.

## Plans

- **Free:** basic monitoring, up to 10 competitors.
- **Pro:** unlimited competitors plus advanced intelligence and prediction.
- **Expert:** Pro plus AI consulting and strategic decision support.

Limits advertised as unlimited still require internal usage/abuse controls.

## Repository

The repository is intentionally organized so the App Factory can reuse authentication, billing, entitlements, usage, AI, audit, adapters, intelligence engines, and testing patterns in future products.

## Getting started

```bash
pip install -e ".[test]"
cp .env.example .env
uvicorn api.main:app --reload      # API
rivalry-worker                     # job worker (needs RIVALRY_DATABASE_URL / RIVALRY_REDIS_URL)
pytest -q
```

See [docs/AUDIT.md](docs/AUDIT.md), [ARCHITECTURE.md](ARCHITECTURE.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
