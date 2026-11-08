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

## Marketplace extension — foundation implemented
- [x] Add organization-owned public business profiles.
- [x] Add service catalogue with categories, indicative prices and durations.
- [x] Add public marketplace search for published services.
- [x] Add customer booking requests with pending/confirmed/cancelled/completed states.
- [x] Add basic overlap checks for pending and confirmed booking requests.
- [x] Add partner endpoints for profile, services and incoming bookings.
- [x] Add platform-admin endpoints for partner review and booking oversight.
- [x] Add public catalogue page at /marketplace, partner page at /partner and operations page at /platform.
- [x] Add migration 0003_marketplace without dropping or rewriting existing customer tables.
- [x] Add marketplace API tests and embedded JavaScript syntax checks.

## Remaining before a real public launch
- [ ] Configure a dedicated PLATFORM_ADMIN_EMAIL on the server.
- [ ] Finish visual/functional browser QA on desktop and mobile.
- [ ] Add real availability calendar and transactional protection against concurrent booking races.
- [ ] Link confirmed appointments to CRM customer/vehicle records with appropriate identity checks.
- [ ] Add driver accounts, booking history and cancellation flows.
- [ ] Add notification delivery, audit logs, retention/deletion workflows and privacy/legal review.
- [ ] Validate PostgreSQL deployment, backups, monitoring and recovery.
- [ ] Recruit pilot shops in Saint Petersburg and Leningrad Oblast.
