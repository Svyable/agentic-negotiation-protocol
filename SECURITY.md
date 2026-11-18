# Security policy

OpenANP v0.1 is an **in-memory prototype**, not a trusted execution service. Hash chaining checks accidental/local history modification but does not authenticate participants, prove human approval, or stop a compromised process rewriting its own log.

**Do not expose this reference engine directly to untrusted remote callers.** Do not connect it to live trade, money, contract or settlement systems; no approval here constitutes a verifiable signature.

For security reports, prefer GitHub's private vulnerability reporting for this repository if enabled; otherwise open a minimal issue without exploitable details and request a private contact channel. Never publish credentials, customer information or proof-of-concept exploits involving real institutions.

Threats to address before real deployments include impersonation, forged human approvals, replay and concurrent messages, mandate changes, policy injection via reasons, leaked reservation prices, clock tampering, nonrepudiation, revocation, sanctions/regulatory checks and external custody of the audit trail.

See [spec/openanp-0.1.md](spec/openanp-0.1.md#8-limitations-and-adversarial-model).