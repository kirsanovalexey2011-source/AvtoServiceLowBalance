# AutoFlow roadmap

## Phase 0 — discovery
- [ ] 15–20 interviews with independent repair shops.
- [ ] Verify competitor features and prices.
- [ ] Validate spreadsheet/CRM import need.
- [ ] Identify buyer and daily operator.
- [ ] Recruit 3 pilot businesses.
**Exit:** repeated pain and 3 pilot candidates.

## Phase 1 — product design
- [ ] User journeys and wireframes.
- [ ] Data dictionary and ER diagram.
- [ ] Threat model and privacy review.
- [ ] Tenant-isolation and consent model review.
- [ ] Confirm MVP scope.

## Phase 2 — core MVP
- [ ] Authentication and organization membership.
- [ ] Tenant-scoped client and vehicle CRUD.
- [ ] Service history and next-due dates.
- [ ] Search, filters and pagination.
- [ ] CSV import preview and validation.
- [ ] Audit trail.

## Phase 3 — retention workflow
- [ ] Configurable rules and due/inactive queue.
- [ ] Draft templates and consent suppression.
- [ ] Manual outcome tracking.
- [ ] Idempotent task generation.
- [ ] Retention analytics.

## Phase 4 — pilot and launch
- [ ] Security and tenant-isolation tests.
- [ ] Legal/privacy review before real personal data.
- [ ] Backups, monitoring and restore drill.
- [ ] 3–5 pilot businesses.
- [ ] Validate pricing, support and payment eligibility.

## Current status
Initial docs, FastAPI scaffold, SQLAlchemy entities and health tests are in progress. Authentication, migrations, CRUD, workflows, UI, integrations and production hardening remain outstanding.
