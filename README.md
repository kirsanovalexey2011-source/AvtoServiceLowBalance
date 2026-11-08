# AutoFlow

Customer retention platform for automotive businesses.

AutoFlow helps automotive businesses identify customers due for follow-up, manage consent-aware return workflows, and measure repeat visits attributable to customer outreach.

## Product focus
The first release focuses on independent automotive service shops. The architecture is intended to support other automotive business types after validation.

## Status
Initial repository bootstrap. See `docs/` for product requirements, market research, interview guide, roadmap, and security checklist.

## Planned stack
- Python 3.12+
- FastAPI
- SQLAlchemy 2
- PostgreSQL (SQLite for local development)
- Pytest

## Safety
Do not use real customer data in development. The first MVP creates message drafts for staff review; it does not send unattended bulk messages. Complete legal and privacy review before processing real personal data.
