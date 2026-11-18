"""Deterministic, transport-neutral OpenANP reference state machine.

Prototype only: event hashes are NOT authentication, authorization or signatures.
No trade execution, settlement, network, identity, or durable storage is provided.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4

VERSION = "0.1"
GENESIS_HASH = "0" * 64
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")


class ProtocolViolation(ValueError):
    """A proposed state transition or mandate check was denied."""


def canonical_json(value: object) -> str:
    """Stable UTF-8 JSON for this prototype; NOT RFC 8785 JCS."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def terms_digest(terms: Mapping[str, str]) -> str:
    if not isinstance(terms, dict) or not terms:
        raise ProtocolViolation("terms must be a nonempty object")
    for key, value in terms.items():
        if not isinstance(key, str) or not key or not isinstance(value, str) or not value:
            raise ProtocolViolation("terms must contain nonempty string keys and values")
    return digest(terms)


@dataclass(frozen=True)
class Mandate:
    """Private, participant-local delegated authority. Do not put it on the wire.

    Every term must have an explicit numeric bound or exact-value allowlist.
    Decimal strings are required; float input is never accepted.
    """
    principal: str
    counterparties: tuple[str, ...]
    approvers: tuple[str, ...]
    numeric: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    choices: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.principal or not self.counterparties or not self.approvers:
            raise ValueError("mandate needs a principal, counterparties and human approvers")
        if not self.numeric and not self.choices:
            raise ValueError("mandate must constrain at least one term")
        if set(self.numeric) & set(self.choices):
            raise ValueError("a term cannot have both numeric and choice rules")
        numbers = {}
        for term, bounds in self.numeric.items():
            if not isinstance(term, str) or not term or len(bounds) != 2:
                raise ValueError("invalid numeric bound")
            low, high = bounds
            for bound in (low, high):
                if not isinstance(bound, str) or not _DECIMAL.fullmatch(bound):
                    raise ValueError("numeric bounds must be finite canonical decimal strings")
            if Decimal(low) > Decimal(high):
                raise ValueError("lower bound exceeds upper bound")
            numbers[term] = (low, high)
        options = {}
        for term, values in self.choices.items():
            if not isinstance(term, str) or not term or not values:
                raise ValueError("invalid choice rule")
            if any(not isinstance(v, str) or not v for v in values):
                raise ValueError("choices must be nonempty strings")
            options[term] = tuple(values)
        object.__setattr__(self, "numeric", MappingProxyType(numbers))
        object.__setattr__(self, "choices", MappingProxyType(options))
        object.__setattr__(self, "counterparties", tuple(self.counterparties))
        object.__setattr__(self, "approvers", tuple(self.approvers))

    def check(self, terms: Mapping[str, str]) -> None:
        terms_digest(terms)
        expected = set(self.numeric) | set(self.choices)
        if set(terms) != expected:
            raise ProtocolViolation("terms fail mandate field allowlist")
        for field_name, (low, high) in self.numeric.items():
            value = terms[field_name]
            if not _DECIMAL.fullmatch(value):
                raise ProtocolViolation(f"{field_name} must be a finite canonical decimal string")
            try:
                amount = Decimal(value)
            except InvalidOperation as exc:
                raise ProtocolViolation("invalid decimal") from exc
            if not Decimal(low) <= amount <= Decimal(high):
                raise ProtocolViolation(f"{field_name} outside delegated authority")
        for field_name, values in self.choices.items():
            if terms[field_name] not in values:
                raise ProtocolViolation(f"{field_name} not authorized")


@dataclass(frozen=True)
class Argument:
    """Dialectical explanation. Textual premises are NOT machine-verified facts."""
    claim: str
    premises: tuple[str, ...]
    concession: str = ""

    def as_dict(self) -> dict:
        if not isinstance(self.claim, str) or not 1 <= len(self.claim) <= 240:
            raise ProtocolViolation("argument requires a concise claim")
        if not isinstance(self.premises, (tuple, list)) or not 1 <= len(self.premises) <= 8:
            raise ProtocolViolation("argument requires 1-8 premises")
        if any(not isinstance(p, str) or not 1 <= len(p) <= 240 for p in self.premises):
            raise ProtocolViolation("premises must be concise text")
        if not isinstance(self.concession, str) or len(self.concession) > 240:
            raise ProtocolViolation("invalid concession")
        return {"claim": self.claim, "premises": list(self.premises), "concession": self.concession}


def verify_transcript(events: list[dict]) -> bool:
    """Verify sequence and hash chain. Does not establish actor identity or completeness."""
    previous = GENESIS_HASH
    try:
        if not isinstance(events, list):
            return False
        for seq, entry in enumerate(events, start=1):
            if set(entry) != {"session_id", "seq", "kind", "actor", "data", "at", "previous_hash", "hash"}:
                return False
            if entry["seq"] != seq or entry["previous_hash"] != previous:
                return False
            payload = {k: v for k, v in entry.items() if k != "hash"}
            if digest(payload) != entry["hash"]:
                return False
            previous = entry["hash"]
        return True
    except (ValueError, TypeError, KeyError, OverflowError):
        return False


class Session:
    """One bilateral negotiation; event log is append-only through public methods."""

    def __init__(self, left: Mandate, right: Mandate, *,
                 session_id: str | None = None, max_offers: int = 12):
        if left.principal == right.principal:
            raise ValueError("parties must be distinct")
        if right.principal not in left.counterparties or left.principal not in right.counterparties:
            raise ProtocolViolation("counterparties lack reciprocal authorization")
        if not isinstance(max_offers, int) or isinstance(max_offers, bool) or max_offers < 1:
            raise ValueError("max_offers must be a positive integer")
        self.session_id = session_id or str(uuid4())
        self._mandates = {left.principal: left, right.principal: right}
        self.max_offers = max_offers
        self.state = "OPEN"
        self._events: list[dict] = []
        self._offer: dict[str, str] | None = None
        self._offer_hash: str | None = None
        self._offer_actor: str | None = None
        self._offers = 0
        self._confirmed: set[str] = set()
        self._approvals: dict[str, str] = {}

    @property
    def transcript(self) -> list[dict]:
        return deepcopy(self._events)

    @property
    def head_hash(self) -> str:
        return self._events[-1]["hash"] if self._events else GENESIS_HASH

    @property
    def offer_hash(self) -> str | None:
        return self._offer_hash

    def _party(self, actor: str) -> Mandate:
        if actor not in self._mandates:
            raise ProtocolViolation("unknown participant")
        return self._mandates[actor]

    def _append(self, kind: str, actor: str, data: dict) -> dict:
        entry = {
            "session_id": self.session_id,
            "seq": len(self._events) + 1,
            "kind": kind,
            "actor": actor,
            "data": deepcopy(data),
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "previous_hash": self.head_hash,
        }
        entry["hash"] = digest(entry)
        self._events.append(entry)
        return deepcopy(entry)

    def propose(self, actor: str, terms: dict[str, str], argument: Argument) -> dict:
        self._party(actor)
        if self.state not in ("OPEN", "NEGOTIATING"):
            raise ProtocolViolation("session is not accepting offers")
        if self._offer_actor == actor:
            raise ProtocolViolation("an agent cannot counter its own offer")
        if self._offers >= self.max_offers:
            raise ProtocolViolation("offer budget exhausted; escalate or terminate")
        self._mandates[actor].check(terms)
        reason = argument.as_dict()
        offered = deepcopy(terms)
        proposal_hash = terms_digest(offered)
        kind = "OFFER" if self._offers == 0 else "COUNTER"
        event = self._append(kind, actor, {
            "terms": offered, "terms_hash": proposal_hash, "argument": reason,
            "replaces": self._offer_hash,
        })
        self._offer = offered
        self._offer_hash = proposal_hash
        self._offer_actor = actor
        self._offers += 1
        self.state = "NEGOTIATING"
        return event

    def accept(self, actor: str, offer_hash: str) -> dict:
        self._party(actor)
        if self.state != "NEGOTIATING" or self._offer is None:
            raise ProtocolViolation("no live offer")
        if actor == self._offer_actor:
            raise ProtocolViolation("cannot accept one's own offer")
        if offer_hash != self._offer_hash:
            raise ProtocolViolation("stale or mismatched offer hash")
        self._mandates[actor].check(self._offer)
        event = self._append("ACCEPT", actor, {"terms_hash": self._offer_hash})
        self.state = "AWAITING_CONFIRMATION"
        return event

    def confirm(self, actor: str, terms: dict[str, str]) -> dict:
        self._party(actor)
        if self.state != "AWAITING_CONFIRMATION":
            raise ProtocolViolation("not awaiting independent confirmation")
        if actor in self._confirmed:
            raise ProtocolViolation("party already confirmed")
        self._mandates[actor].check(terms)
        if terms_digest(terms) != self._offer_hash:
            raise ProtocolViolation("independent term confirmation mismatch")
        event = self._append("CONFIRM", actor, {"terms_hash": self._offer_hash})
        self._confirmed.add(actor)
        if self._confirmed == set(self._mandates):
            self.state = "AWAITING_APPROVAL"
        return event

    def approve(self, actor: str, approver: str, offer_hash: str) -> dict:
        mandate = self._party(actor)
        if self.state != "AWAITING_APPROVAL":
            raise ProtocolViolation("both confirmations required before approval")
        if approver not in mandate.approvers:
            raise ProtocolViolation("approver not delegated in mandate")
        if actor in self._approvals:
            raise ProtocolViolation("principal already approved")
        if offer_hash != self._offer_hash:
            raise ProtocolViolation("approval does not match accepted terms")
        event = self._append("APPROVE", actor, {
            "approver": approver, "terms_hash": offer_hash,
            "notice": "approval only; no execution occurs",
        })
        self._approvals[actor] = approver
        if set(self._approvals) == set(self._mandates):
            self.state = "APPROVED"
        return event

    def terminate(self, actor: str, reason: str) -> dict:
        self._party(actor)
        if self.state in ("APPROVED", "TERMINATED"):
            raise ProtocolViolation("session is terminal")
        if not isinstance(reason, str) or not 1 <= len(reason) <= 240:
            raise ProtocolViolation("termination reason is required")
        event = self._append("TERMINATE", actor, {"reason": reason})
        self.state = "TERMINATED"
        return event

    def receipt(self) -> dict:
        if self.state != "APPROVED":
            raise ProtocolViolation("receipt requires confirmations and both approvals")
        return {
            "protocol": "OpenANP/0.1",
            "session_id": self.session_id,
            "status": "APPROVED_NOT_EXECUTED",
            "terms": deepcopy(self._offer),
            "terms_hash": self._offer_hash,
            "human_approvals": dict(self._approvals),
            "transcript_head_hash": self.head_hash,
            "event_count": len(self._events),
        }
