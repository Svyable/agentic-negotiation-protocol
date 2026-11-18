# OpenANP/0.1 — Draft negotiation control profile

**Status:** EXPERIMENTAL / NON-NORMATIVE REFERENCE IMPLEMENTATION  
**Scope:** bilateral, in-memory, human-approval-gated, transport-neutral  
**MUST NOT:** treat approval as execution, settlement, or a legally binding signature

## 1. Objective and boundary

This is a first, independently designed profile for agents that bargain on behalf of separate principals. The protocol models **authority** (what an agent may offer or accept), **argument** (what an agent says and why), **strategy** (private concession planning), **coordination** (synchronized terms), and **accountability** (human decisions and audit evidence).

The reference engine accepts only local method calls. It does **not** authenticate callers, verify institutional identity, transmit messages, or claim interoperability with BNY's separately announced patent-pending ANP. Other open projects, including A2CN and Concordia, already address related problems. Future implementations should map this profile onto existing standards rather than proliferate incompatible transports.

## 2. Roles and private mandates

Exactly two different `principal` identifiers participate. Each must list the other in its `counterparties` allowlist. Each has one or more designated `approvers`.

A **Mandate** is local, NOT a protocol message. It specifies:

- `numeric`: required term name -> inclusive `[min,max]` strings, compared as exact decimal numbers.
- `choices`: required term name -> nonempty list of exact allowed strings.
- All offered terms MUST exactly match the union of mandate fields. Unknown/unconstrained fields MUST fail.
- All term names and values MUST be nonempty strings. Numeric strings MUST match `-?(0|[1-9][0-9]*)(\\.[0-9]+)?`; no floats, exponent, NaN, infinities.
- The local principal MUST validate an offer before proposing it and MUST revalidate its own mandate before accepting or confirming another principal's offer.

Counterparty mandates, reservation prices, strategy parameters and internal policy failures SHOULD remain private. The engine has no confidential-computation or secure enclaves.

## 3. Structured argument

Each offer or counter carries an `argument`:

```json
{
  "claim": "Can close at this price if settlement remains unchanged",
  "premises": ["Settlement matches the previously discussed schedule"],
  "concession": "Improved price in exchange for prompt confirmation"
}
```

A claim requires a 1–240-character sentence, 1–8 premise strings (1–240 characters each) and an optional concession string (at most 240 characters). This grammar makes rationale legible but DOES NOT prove the truth of premises. Future versions may add evidence hashes, challenge/response and logic-carrying authorization proofs; until then any such assertions are advisory.

## 4. Terms and hashes

A term package is a nonempty JSON object whose keys and values are nonempty strings. Amounts use decimal strings. To compute a terms digest:

```text
terms_hash = lowerhex(SHA-256(UTF-8(json.dumps(terms,
    sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False))))
```

This is **Python-style canonical JSON for a constrained subset**, not a claim of RFC 8785/JCS interoperability. Cross-language implementations MUST use conformance test vectors before treating hashes as interoperable.

Every event includes `session_id`, positive sequential `seq`, `kind`, `actor`, `data`, UTC `at`, `previous_hash`, and its `hash`. The first `previous_hash` is 64 ASCII zeros. Each event hash uses the same SHA-256 canonicalization over all fields **except** `hash`. This gives local tamper evidence only: absent signatures, trusted clocks, independent witnesses, and immutable custody, a controlling process can rewrite history.

See `event.schema.json` for the event skeleton.

## 5. State machine

| State | Allowed acts | Next state |
| --- | --- | --- |
| OPEN | first OFFER / TERMINATE | NEGOTIATING / TERMINATED |
| NEGOTIATING | COUNTER by the other actor, ACCEPT by the other actor, TERMINATE | NEGOTIATING / AWAITING_CONFIRMATION / TERMINATED |
| AWAITING_CONFIRMATION | one CONFIRM per principal, exact accepted digest; TERMINATE | AWAITING_APPROVAL after both / TERMINATED |
| AWAITING_APPROVAL | APPROVE by a locally authorized approver for each principal; TERMINATE | APPROVED after both / TERMINATED |
| APPROVED | receipt only | terminal, **not executed** |
| TERMINATED | none | terminal |

The initiating agent cannot accept its own offer. Counteroffers MUST alternate actors; stale offers MUST fail hash checks. Each proposal checks the proposing party's own mandate. Acceptance MUST carry the hash of the most recent outstanding offer and validate the accepting party's mandate. Independent confirmation MUST submit the **entire exact terms object**; merely asserting a digest is insufficient. Both approvals MUST bind the same digest, and an approver MUST appear in the authorizing principal's private mandate. Every failed check rejects the transition without adding a successful event.

The `max_offers` session limit counts all OFFER/COUNTER messages, defaults to 12, and never authorizes an extra offer. Higher-level coordinators SHOULD escalate, terminate, or let humans renegotiate a mandate when exhausted. A terminal `APPROVED` receipt is evidence of the simulation's state only; it MUST NOT itself invoke an order, transfer, payment, or contract API.

## 6. Event kinds and data

- `OFFER` / `COUNTER`: `terms`, `terms_hash`, `argument`, `replaces` (previous terms digest or null).
- `ACCEPT`, `CONFIRM`: `terms_hash`.
- `APPROVE`: `approver`, `terms_hash`, `notice`.
- `TERMINATE`: `reason`.

Receipts return `protocol`, `session_id`, `status=APPROVED_NOT_EXECUTED`, `terms`, `terms_hash`, `human_approvals`, `transcript_head_hash`, and `event_count`. A receipt is not a signature.

## 7. Strategy is advisory and private

The included `ConcessionPolicy` is a deterministic, back-loaded schedule:

```text
quote(r) = aspiration + (reservation - aspiration) × (r/(rounds−1))²
```

Quotations use Decimal and configurable round-to-even quantization. This is only one bargaining policy, not the protocol definition. It reveals no counterpart's preferences and cannot override a mandate. A real agent should reason about BATNA, non-price terms, external evidence, authority and de-escalation; none of those claims are machine-verified here.

## 8. Limitations and adversarial model

The reference layer **does not** solve impersonation, message delivery, nonce replay over a network, stolen credentials, authenticity of human approval, compromised mandates, legal enforceability, sanctions checks, market manipulation, regulated trade compliance, concurrency, persistent audit custody, crash recovery, Byzantine peers, deadlines or external price validity.

No model output may be treated as an approval, identity proof, price feed, regulatory determination or execution instruction. Do not transmit sensitive mandate details inside free text. Production implementations require a professional security review, persistent audit and independent controls before any real-value use.

## 9. Compatibility and evolution

The JSON event skeleton is descriptive for this reference implementation, not a standard wire specification. Future work: authenticated and signed envelope; signed mandate commitments and revocations; version/capability negotiation; persistent session store; A2A profile plus MCP tool mapping; independent bilateral receipt co-signing; conformance corpus; N-party coalition and veto rules. Breaking changes require a new protocol version.

## 10. Provenance

The design takes inspiration from public accounts of BNY/Microsoft's November 17, 2026 Treasury-bill pilot; [BNY's announcement](https://www.bny.com/corporate/global/en/about-us/newsroom/press-release/bny-and-microsoft-complete-first-agentic-negotiation-of-a-us-treasury-trade.html) reports a proprietary/patent-pending protocol. This document is independently authored, is not BNY's ANP, and makes no interoperability claims. Compare [A2A](https://github.com/a2aproject/A2A), [A2CN](https://github.com/A2CN-protocol/A2CN), and [Concordia](https://github.com/eriknewton/concordia-protocol) before designing extensions.