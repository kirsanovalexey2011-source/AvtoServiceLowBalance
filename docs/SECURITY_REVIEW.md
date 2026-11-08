# Security review — AutoFlow MVP

Date: 8 November 2026
Scope: source-level review of the current MVP branch and automated CI checks. This is not a penetration test and does not certify the service as secure.

## Implemented safeguards
- Passwords are stored as Argon2id hashes; plaintext passwords are not persisted.
- Session tokens are signed and time-limited; cookies are HttpOnly and SameSite=Lax, Secure in production.
- Login and registration are rate-limited per client IP.
- Unsafe browser requests with a mismatched Origin are rejected.
- Baseline response headers: nosniff, frame denial, referrer policy and restricted permissions policy.
- API responses are marked no-store to reduce accidental caching of customer data.
- Customer, vehicle, visit, consent and deferred-service operations are scoped to the authenticated organization.
- Latest consent event wins; a later refusal suppresses marketing drafts.
- Pydantic limits input lengths and numeric ranges; monetary columns have non-negative checks.
- Production configuration rejects the development secret and SQLite.
- Alembic migrations are included; CI applies migrations against a fresh SQLite database.

## Automated checks
- Bandit scans application Python code.
- pip-audit checks pinned/resolved requirements for known advisories.
- pytest covers registration/login, duplicate email, validation, client/visit workflow, consent refusal, tenant isolation, cross-origin requests and deferred-service recovery.
- CI extracts embedded dashboard JavaScript and runs Node syntax validation.

## Findings fixed during this review
1. A later marketing refusal could be ignored if the query selected only granted consent rows. The query now selects the latest event first, then checks its state.
2. Old overdue visits could keep a customer in the return queue after a newer visit. Queue and dashboard now evaluate each customer's latest visit.
3. A tenant-scoped customer could expose a vehicle record belonging to another tenant through a nested relationship. Nested vehicle output is filtered by organization.
4. Production could start with the known development signing key or SQLite. Production settings now reject both.
5. Authentication endpoints had no rate limiting. Login and registration now have per-IP limits.
6. The CI dependency audit identified a vulnerable pytest release. The test dependency was upgraded to a patched release.

## Remaining risks / required before real customer data
- Sessions are stateless signed cookies; logging out removes the browser cookie but does not revoke a copied token server-side before expiry.
- No MFA, email verification, password reset, role/permission matrix or admin audit trail yet.
- No dedicated CSRF token mechanism; Origin checks and SameSite cookies are defense-in-depth, not a substitute for a full deployment review.
- No verified backup/restore process, production monitoring, alerting or incident-response process.
- PostgreSQL deployment, TLS termination, secret management and production migration rehearsal have not been validated here.
- Consent evidence is a user-entered reference, not independently verified proof. Legal basis, consent wording, retention, opt-out and data-subject rights require legal review.
- No external penetration test, dynamic scanner, fuzzing or threat-model review has been performed.

Do not treat the current MVP as production-ready. Use synthetic data only until the remaining controls are implemented and independently reviewed.
