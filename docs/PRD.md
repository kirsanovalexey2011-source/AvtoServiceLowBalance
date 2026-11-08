# AutoFlow — Product Requirements v0.1

## Thesis
AutoFlow helps automotive businesses turn existing customer records into measurable repeat visits. It starts as a retention product, not a full workshop ERP.

## Initial segment
Independent repair shops with 1–10 work bays. The model can support car washes, tire shops, detailing studios and other automotive businesses later, after validation.

## MVP outcome
A business can add clients and vehicles, record service visits and next-due dates, see a follow-up queue, generate message drafts for staff review, record outcomes, and view repeat-visit metrics.

## In scope
- Organizations and users (authentication is a required next implementation slice).
- Clients, vehicles and service history.
- Configurable follow-up rules and due queue.
- Draft messages for manual review; no unattended bulk sending.
- Channel- and purpose-specific consent records and opt-out suppression.
- Outcomes: contacted, booked, visited, not interested, do-not-contact.
- Basic metrics: due customers, reviewed drafts, bookings, repeat visits and recorded revenue.

## Out of scope
Accounting, inventory, payroll, workshop scheduling, AI recommendations, unattended messaging, SMS integrations, payment processing and customer mobile app.

## Requirements
1. Every tenant-owned record is scoped to an organization.
2. Users manage clients and vehicles.
3. Users record visits and optional next-due dates.
4. Rules create reviewable tasks, not automatic messages.
5. Unknown, absent or revoked consent suppresses outbound contact.
6. Outcomes are recorded to measure repeat visits.
7. Export and deletion workflows are designed before real-data pilots.

## Metrics
Time to add/import first 50 clients; due-task review rate; contact-to-booking and booking-to-visit conversion; incremental repeat visits vs baseline; weekly active accounts; paid conversion and churn.

## Pricing hypothesis
Test willingness to pay around 990–1,990 RUB/month for a small single-location business. This is not validated pricing.
