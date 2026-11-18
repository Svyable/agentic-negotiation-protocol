# OpenANP — Open Agentic Negotiation Protocol

An independent, open-source negotiation control layer for agents acting on behalf of different principals.

**North star:** rigorous reasoning, disciplined concessions, explicit authority, independent term confirmation, and humans in control of consequential commitments.

This repository is an independent project. It is **not** BNY's proprietary/patent-pending Agentic Negotiation Protocol, does not implement that system, and makes no compatibility claims.

The first reference implementation, specification, conformance tests, and simulation are being developed in this repository. It is deliberately transport-neutral and does not execute trades, transfers, or contracts.

## Design

- **Logic:** structured terms, deterministic mandate checks, explicit predicates, and auditable decisions.
- **Diplomacy:** counteroffers and package trades under bounded delegated authority, with private reservation positions.
- **Coordination:** two-party confirmation of exactly matching terms before separate human approvals.
- **Safety:** fail-closed authorization, replay-resistant state transitions, tamper-evident transcripts, and no execution API.

## Context

Inspired by the publicly announced [BNY/Microsoft Treasury-bill negotiation pilot](https://www.bny.com/corporate/global/en/about-us/newsroom/press-release/bny-and-microsoft-complete-first-agentic-negotiation-of-a-us-treasury-trade.html) (November 17, 2026), without copying or claiming access to its implementation. Existing related open standards include [A2A](https://github.com/a2aproject/A2A) and [A2CN](https://github.com/A2CN-protocol/A2CN). OpenANP should compose with them rather than reinvent transport, identity, or settlement.

## Status

**Pre-alpha**. Not safe for live trading, payments, legally binding transactions, or production identity verification.