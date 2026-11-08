# Security and privacy checklist — not legal advice

AutoFlow may process names, phone numbers, vehicle identifiers, service history and communication preferences. Do not use real customer data during development.

Before a real-data pilot:
- [ ] Determine the legal roles and responsibilities of the business and AutoFlow with qualified legal advice.
- [ ] Identify lawful basis and purposes for each field and communication channel.
- [ ] Provide required notices and agreements.
- [ ] Assess Russian personal-data localization and cross-border transfer requirements.
- [ ] Define retention, export, correction and deletion procedures.
- [ ] Store consent evidence by purpose/channel, including timestamp, source and revocation where required.
- [ ] Separate service messages from advertising campaigns.
- [ ] Obtain legally sufficient prior consent for advertising messages where required.
- [ ] Suppress contact after opt-out; unknown consent means do not send.
- [ ] Enforce organization-level access and role permissions.
- [ ] Use HTTPS, protected backups, secret management and incident procedures.

Engineering guardrails:
- Every tenant-owned row has organization_id.
- Never trust organization_id supplied by the browser.
- Every query must be scoped to the authenticated organization.
- MVP creates drafts only; it does not send unattended bulk messages.
- Audit sensitive actions without logging unnecessary personal data.
