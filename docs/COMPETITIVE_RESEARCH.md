# Competitive research — AutoFlow

Research snapshot: 8 November 2026. This is desk research from public product pages, not a hands-on trial of paid accounts. Vendor feature availability and pricing can vary by region and plan.

## Products reviewed

### AutoLeap — customer retention and deferred work
Official CRM page: https://autoleap.com/features/crm/

Observed product ideas:
- One customer record connects vehicles, service history and interactions.
- Maintenance reminders are driven by actual service history.
- Deferred/declined work is retained and surfaced at a later booking.
- Retention reporting connects follow-up activity with conversions and recovered revenue.

AutoFlow takeaway: model declined work as a first-class object, not just a note. Let the shop record an estimate or repair the customer declined, then track whether it was recovered.

### Tekmetric — connected shop workflow and marketing
Official marketing page: https://www.tekmetric.com/feature/crm-marketing

Observed product ideas:
- Online booking, automated reminders, scheduled campaigns and two-way texting.
- Customer communication is kept alongside calendar, repair orders and payments.
- Campaign reporting tracks scheduled activity and results.
- Their help material distinguishes marketing automations (declined service, canned job, lost customer) from transactional follow-up.

AutoFlow takeaway: separate service operations from marketing permission; keep message generation manual until consent, delivery and opt-out handling are production-ready.

### Shopmonkey — communication and approvals
Official customer communication page: https://www.shopmonkey.io/product/customer-comms

Observed product ideas:
- Two-way text/email in the customer workflow.
- Digital estimate approvals.
- Appointment reminders and confirmation/cancellation updates.
- Customer-facing communication should be tied to a real work order.

AutoFlow takeaway: future communication timeline should show the reason, channel, status and customer response, not just a generated message.

## Product positioning

AutoFlow should not attempt to replace a full shop-management suite on day one. A narrower product can sit beside existing workshop software and solve one measurable problem: **recovering work and repeat visits that otherwise get forgotten**.

Initial workflow:
1. Import or enter customer, vehicle and last visit.
2. Record the next maintenance date or a declined repair.
3. Show a prioritized return/recovery queue.
4. Require the operator to review and contact the customer through their normal channel.
5. Record response, booking, completed visit and recovered revenue.
6. Report conversion and revenue recovered.

## What not to copy

Do not copy source code, proprietary interface assets, wording, screenshots or brand elements. The features above are public product observations; AutoFlow's implementation and interface should be original.

## Sources
- AutoLeap CRM: https://autoleap.com/features/crm/
- Tekmetric CRM/Marketing: https://www.tekmetric.com/feature/crm-marketing
- Tekmetric marketing automations: https://support.tekmetric.com/hc/en-us/articles/33212380922007-Marketing-Automations
- Shopmonkey customer communications: https://www.shopmonkey.io/product/customer-comms
- Software Advice service-history overview (2026): https://www.softwareadvice.com/resources/best-auto-repair-shop-software-service-history/
