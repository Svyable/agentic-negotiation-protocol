# OpenANP — Open Agentic Negotiation Protocol

**Logic without naivety. Leverage without lawlessness. Coordination without surrendering authority.**

OpenANP is an independent, open-source protocol experiment for negotiating across organizational boundaries. It gives autonomous agents a *constitutional layer*: machines may argue, make concessions, and coordinate, but only within a principal's explicit delegated mandate; final terms require independent confirmation and human approval.

> **Pre-alpha research software.** The reference engine is in-memory, not a secure network service. There is no identity verification, signing, settlement, order routing, durable ledger, or execution path. **Never use it for live trades, payments, or legally binding transactions.**

## Quick start

Requires Python 3.10+. No runtime dependencies.

```sh
python -m unittest discover -s tests -v
python -m examples.demo
```

The demonstration negotiates a *fictional* Treasury-bill quote. It performs successive offers, counters, hash-bound acceptance, bilateral confirmation, and separate human-approval *simulations*. The final result is `APPROVED_NOT_EXECUTED` — no trade is placed.

## Three pillars

| Pillar | Operational question | OpenANP mechanism |
| --- | --- | --- |
| **LOGOS** — Plato | Is this offer internally consistent, justified, and permitted? | Explicit string-typed terms, exact Decimal mandate checks, claim/premise objects, deterministic accept/confirm checks |
| **KRATOS** — strategic agency | What can this principal concede, and on whose authority? | Counterparty allowlists, private reservation boundaries, back-loaded bounded concession strategy, hard round budget |
| **SYMPHONIA** — Kissinger-style coordination | Can two independent institutions maintain one reality without ceding control? | Alternating offers, stale-offer rejection, dual term confirmation, dual human approval, hash-chained audit trail |

The quoted philosophical and diplomatic references are metaphors, not endorsements. Textual premises are **not** verified as true by the engine; authorization checks are deterministic.

## Shape of a negotiation

```text
A OFFER ─► B COUNTER ─► A COUNTER ─► B COUNTER
                                           │
                                      A ACCEPT
                                           │
                      B CONFIRM ◄──── A CONFIRM
                          │                │
                          └── exact hash ──┘
                                  │
                           AWAITING_APPROVAL
                                  │
                    A HUMAN APPROVE + B HUMAN APPROVE
                                  │
                         APPROVED_NOT_EXECUTED
```

Every event records sequence number, previous event hash, terms digest where applicable, actor, timestamp and message. `verify_transcript` detects local transcript modification; **it is not an identity/authenticity proof**. Mandates and reservation values remain local; only voluntary argument text goes into the transcript.

## What is implemented now

- Bilateral state machine: `OPEN`, `NEGOTIATING`, `AWAITING_CONFIRMATION`, `AWAITING_APPROVAL`, `APPROVED`, `TERMINATED`.
- All-field allowlist mandates with exact-value constraints and canonical decimal ranges; no floating-point price processing.
- Structured claim/premise/concession explanations and a private bounded-concession policy.
- Offer hash binding, alternating turns, a finite offer budget, reciprocal participant authorization, term-digest agreement, two independent human approval gates.
- Tamper-evident (not authenticated) event hashes, a JSON event schema, a readable v0.1 specification, demo, and unit tests.

## Not implemented / roadmap

1. **Authentication and cryptographic receipts:** authenticated agents and humans; signed mandates, approvals and bilateral records; key rotation, revocation, replay/nonce protection and trusted timestamps.
2. **Transport/interoperability:** A2A capability extension, optional MCP interfaces, version negotiation, secure session relay, persistence, retry/idempotency.
3. **Policy and strategy:** external policy-as-code, deadline/timeout enforcement, multi-issue bundles, conditional promises, coalition/multiparty negotiation, evidence attestation, privacy-safe constraint proofs.
4. **Conformance:** cross-language golden vectors, security fuzzing, Byzantine/disconnected peers, contract verification and external audits.

The protocol **does not** assert that both parties share objectives. It structures disagreement, keeps private constraints private, and requires each principal to authorize the terms it ultimately accepts.

## Specifications and examples

- [v0.1 draft specification](spec/openanp-0.1.md)
- [Event JSON Schema](spec/event.schema.json)
- [In-memory protocol engine](openanp/core.py)
- [Private-side concession strategy](openanp/strategy.py)
- [Treasury-bill simulation](examples/demo.py)
- [Security expectations](SECURITY.md)

## Relationship to BNY's announcement and other protocols

This project was motivated by BNY and Microsoft's [November 17, 2026 announcement](https://www.bny.com/corporate/global/en/about-us/newsroom/press-release/bny-and-microsoft-complete-first-agentic-negotiation-of-a-us-treasury-trade.html), which describes authorized agents, deterministic controls, independent confirmation of matching terms, and final human trader approval. **BNY's Agentic Negotiation Protocol is patent pending.** OpenANP is not derived from source code or a specification for BNY's system; it is **not affiliated with, endorsed by, or compatible with BNY's implementation**. The demonstration is fictional.

Related open projects deserve explicit recognition: [A2A](https://github.com/a2aproject/A2A) for agent communication, [A2CN](https://github.com/A2CN-protocol/A2CN) for commercial negotiation, [Concordia](https://github.com/eriknewton/concordia-protocol) for structured negotiation, and [MCP](https://modelcontextprotocol.io/) for tools. We should compose with these where practical, not pretend to have invented the whole category.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). The project is released under the [MIT License](LICENSE).