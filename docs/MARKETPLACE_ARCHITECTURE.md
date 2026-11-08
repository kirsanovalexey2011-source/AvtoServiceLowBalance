# AutoFlow marketplace architecture

## Product shape
AutoFlow is a hybrid automotive-services platform with three interfaces:
- Driver marketplace: public service discovery and appointment requests.
- Partner workspace: each automotive business manages its own public profile, service catalogue and incoming bookings.
- Platform operations: a separately configured platform administrator can review partner profiles and see marketplace-wide booking operations.

The existing CRM remains in place. Existing organizations, users, customers, vehicles, service visits, consent records and deferred-service recovery are not migrated or deleted.

## Data model
- `business_profiles`: one public profile per existing organization. New profiles are unpublished until reviewed.
- `service_offerings`: services and indicative prices owned by an organization.
- `appointments`: booking requests, linked to an organization's service offering. Requests start as `pending`; partner confirms, cancels or completes them.

All partner endpoints scope reads and writes by the authenticated user's `organization_id`. Public endpoints return only active services attached to published profiles. Platform-wide endpoints require the configured `PLATFORM_ADMIN_EMAIL` account.

## First release workflow
1. Existing shop owner signs into the current AutoFlow workspace.
2. Owner creates a public business profile and service offerings.
3. Platform administrator reviews and publishes the profile.
4. Driver filters the public catalogue by city/category and submits a booking request.
5. Partner confirms or declines the request in its workspace.
6. Existing CRM can later link appointments to customers and vehicles after identity verification/consent workflows are designed.

## Launch geography
Initial target cities/areas: Saint Petersburg and Leningrad Oblast. The city and district fields are intentionally text-based for the first pilot; a normalized geo-directory and map search should follow after validating the first partner set.

## Important MVP limitations
- A booking request is not a confirmed appointment until the shop accepts it.
- Availability is not yet a live calendar; overlap checks prevent ordinary duplicate requests, but production-grade concurrent slot reservation requires transactional locking/constraints and a shop calendar.
- No online payments, SMS/email delivery, public customer accounts, ratings/reviews, maps or cancellation links yet.
- Do not import real customer records until privacy notices, consent, access logging, retention/deletion and 152-FZ requirements are reviewed.
- `PLATFORM_ADMIN_EMAIL` must be set in the server environment to the dedicated platform administrator account. Keep this value out of public repositories and never expose platform endpoints to ordinary shop accounts.
- Marketplace bookings contain customer personal data. Production rollout requires access audit logs, retention rules, encryption/backup controls and legal review.

## Next milestones
1. Partner profile/service editor and incoming-booking interface.
2. Platform admin dashboard, partner approval and booking oversight.
3. Driver accounts, saved vehicles and booking history.
4. Real availability calendar, notification delivery and appointment-to-CRM customer linking.
5. Map/geocoding, ratings with anti-abuse controls, payments and paid partner plans.
