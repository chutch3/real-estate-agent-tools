# Product Roadmap

## Vision

A platform that makes individual real estate agents irreplaceable to their clients — by streamlining the workflows they do every day and adding intelligence and data that no one else provides. Built for independent agents and small brokerages in the Indiana/Kentucky market, designed to compete with Zillow's commoditization of agents and BrokerBay's shallow workflow tooling.

---

## What's Shipped

- **Property management** — add properties with full parcel data (ArcGIS IGIS), county boundaries, and parcel polygon overlays on the map
- **AI property chat** — ask questions about a property using uploaded documents and property details as context
- **Net sheet** — seller net proceeds calculator with real Indiana property tax proration from DLGF
- **Document management** — upload, view, and delete property documents (S3)
- **Crime heatmap** — raster tile overlay for violent and property crime (Louisville metro)
- **Social post generation** — AI-generated listing copy from property details and documents
- **Authentication** — JWT with sliding token refresh and brokerage/agent multi-tenancy
- **Dual agency validation** — listing and buyer role flags with conflict detection

---

## Phase 1 — Agent Core Workflow

The highest-priority cluster. These are the daily workflows agents spend the most time on. Nothing here requires external data dependencies.

| Issue | Feature |
|-------|---------|
| #54 | Offer wizard — structured offer entry with state/brokerage PDF templates |
| #53 | Spike: signing service evaluation (Anvil, HelloSign, DocuSign) |
| #28 | Offer matrix — listing agent side-by-side offer comparison |
| #50 | Transaction timeline — deal stage tracking from accepted offer to close |
| #45 | Comparative net sheet — seller proceeds at multiple list price scenarios |
| #46 | Buyer readiness profile — agent captures buyer criteria, pre-approval, and preferences |
| — | CMA — comparable market analysis for listing presentations *(to be created)* |
| — | AI communication drafts — templated messages for each transaction stage *(to be created)* |

---

## Phase 2 — Listing Marketing

Marketing workflow for listing agents. Social post generation is already shipped — this phase extends it into a full multi-platform marketing toolkit.

| Issue | Feature |
|-------|---------|
| — | Multi-platform social posting — publish AI-generated copy to Facebook, Instagram, X *(to be created)* |
| — | Listing description generator — MLS-ready property description from documents and property data *(to be created)* |
| — | Marketing asset management — track which platforms a listing has been posted to and when *(to be created)* |

---

## Phase 3 — Intelligence & Data

Data layers and AI features that make agents more informed than they could be manually.

| Issue | Feature |
|-------|---------|
| #11 | Flood zone overlay |
| #12 | School district boundaries and ratings |
| #10 | Zoning and parcel overlay |
| #30/#31 | Layer toggle UX — always-visible controls with availability indicators |
| #26 | Complete FIPS-driven pipeline integration |
| #37 | Indiana historical property tax — multi-year data per parcel |
| #38 | Kentucky property tax ingestion — research and pipeline |
| #39 | Property tax trend graph |
| #16 | Shareable property intelligence report |

---

## Phase 4 — Consumer Portal

Frictionless buyer/seller access to their deal — no account creation required. Reduces agent communication overhead and differentiates on transparency.

| Issue | Feature |
|-------|---------|
| #29 | Magic link token infrastructure — generate, validate, expire, revoke |
| #41 | Document sharing control — agent marks docs as consumer-visible |
| #40 | Consumer portal — seller view (net sheet, property details, shared docs) |
| #42 | Consumer portal — buyer view (properties, shared docs, offer status) |
| #43 | Magic link management UI — last accessed, revoke, regenerate |
| #44 | Consumer chat — AI Q&A scoped to shared data, visible to agent |
| #47 | Agent value report — post-NAR settlement buyer activity document |
| #48 | Equity tracker — post-close agent-branded value and tax trend link |

---

## Phase 5 — Broker Dashboard

Managing broker visibility into their brokerage. Sales feature — helps top-down adoption by brokerages. Build after frontline agent experience is complete.

| Issue | Feature |
|-------|---------|
| #32 | Managing broker role and brokerage-scoped access control |
| #33 | Agent roster — invite, view, disable agents |
| #34 | Workload dashboard — per-agent property and activity view |
| #35 | Brokerage fee templates — default net sheet line items |
| #36 | Sales metrics — sold volume and commission per agent *(blocked on #28)* |

---

## Phase 6 — Integrations

External integrations that expand the platform's data access and interoperability. All require spikes before implementation.

| Issue | Feature |
|-------|---------|
| #52 | Spike: MLS data integration — RESO API, IDX licensing, ingestion strategy |
| #51 | Spike: CRM integration — Follow Up Boss, HubSpot, or lightweight built-in |
| #49 | Spike: showing feedback integration — BrokerBay API or alternatives |

---

## Infrastructure & Quality

Engineering work that supports the platform but is not user-facing.

| Issue | Feature |
|-------|---------|
| #55 | Migrate backend and pipeline from poetry to uv |
| #25 | Add dependency injection container to pipeline |
| #23 | Responsive design and mobile compatibility |
| #24 | Audit and improve frontend testing structure |
| #2  | CI/CD setup |
| —   | Alembic migrations — replace temporary migrate_db.py once schema stabilises *(to be created)* |

---

## Parked / Needs Validation

Features that need more evidence of agent demand or a clearer data path before investment.

| Issue | Feature | Reason parked |
|-------|---------|---------------|
| #14 | Neighborhood trajectory | Needs data source definition — currently too vague |
| #13 | KY/IN cross-border comparison | Niche — validate demand with agents first |
| #17 | Encroachment detection | Complex, niche, liability risk |
| #21 | DocuSign integration | Superseded by #53/#54 |

---

## Competitive Context

| Competitor | What they own | Our angle |
|-----------|--------------|-----------|
| Zillow | Consumer discovery, AVM, lead generation | Agent-owned client relationships, financial transparency, AI that knows the deal |
| NAR / MLS | Listing inventory, forms (zipForms), transaction coordination (Dotloop) | Open architecture, agent-first tooling, no platform lock-in |
| BrokerBay | Showing scheduling, feedback collection | Intelligence layer on top of showing data; consumer portal as better seller notification |
