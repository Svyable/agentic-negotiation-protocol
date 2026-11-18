"""Private-side, bounded concession policy; never transmitted to a counterparty."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

from .core import ProtocolViolation


@dataclass(frozen=True)
class ConcessionPolicy:
    side: str  # "buyer" or "seller"
    aspiration: str
    reservation: str
    rounds: int = 5
    quantum: str = "0.01"

    def __post_init__(self) -> None:
        if self.side not in ("buyer", "seller") or self.rounds < 2:
            raise ValueError("invalid concession policy")
        a, r = Decimal(self.aspiration), Decimal(self.reservation)
        if not a.is_finite() or not r.is_finite() or not Decimal(self.quantum).is_finite() or Decimal(self.quantum) <= 0:
            raise ValueError("values must be finite")
        if (self.side == "buyer" and a > r) or (self.side == "seller" and a < r):
            raise ValueError("reservation direction conflicts with side")

    def quote(self, round_index: int) -> str:
        if not isinstance(round_index, int) or isinstance(round_index, bool) or not 0 <= round_index < self.rounds:
            raise ProtocolViolation("round index outside concession plan")
        fraction = Decimal(round_index) / Decimal(self.rounds - 1)
        # Back-loaded concessions: preserve bargaining room until later rounds.
        amount = Decimal(self.aspiration) + (Decimal(self.reservation) - Decimal(self.aspiration)) * fraction * fraction
        return format(amount.quantize(Decimal(self.quantum), rounding=ROUND_HALF_EVEN), "f")

    def acceptable(self, offered_price: str, round_index: int) -> bool:
        price, threshold = Decimal(offered_price), Decimal(self.quote(round_index))
        if not price.is_finite():
            return False
        return price <= threshold if self.side == "buyer" else price >= threshold
