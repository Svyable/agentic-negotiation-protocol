"""Fictional Treasury-bill negotiation. Human approvals are simulated labels only."""
import json
from openanp import Argument, Mandate, Session, verify_transcript


def demo() -> dict:
    buyer = Mandate(
        principal="Treasury-A",
        counterparties=("Dealer-B",),
        approvers=("buyer-human-01",),
        numeric={"unit_price": ("95.00", "105.00"), "quantity": ("1", "5")},
        choices={"currency": ("USD",), "asset": ("FICTIONAL-TBILL",), "settlement": ("T+1",)},
    )
    seller = Mandate(
        principal="Dealer-B",
        counterparties=("Treasury-A",),
        approvers=("seller-human-01",),
        numeric={"unit_price": ("101.00", "115.00"), "quantity": ("1", "5")},
        choices={"currency": ("USD",), "asset": ("FICTIONAL-TBILL",), "settlement": ("T+1",)},
    )
    s = Session(buyer, seller, session_id="demo-tbill-001", max_offers=6)

    def package(price: str) -> dict[str, str]:
        return {"unit_price": price, "quantity": "2", "currency": "USD",
                "asset": "FICTIONAL-TBILL", "settlement": "T+1"}

    s.propose("Treasury-A", package("98.00"), Argument(
        "Opening indication", ("Illustrative internal quote input",)))
    s.propose("Dealer-B", package("110.00"), Argument(
        "Offer requires a higher unit price", ("Illustrative dealer quote",),
        "Firm settlement schedule"))
    s.propose("Treasury-A", package("102.00"), Argument(
        "Price improvement for the same settlement", ("Price remains within buyer mandate",),
        "Improved price"))
    s.propose("Dealer-B", package("104.00"), Argument(
        "Can narrow the spread", ("Quantity and settlement remain unchanged",),
        "Reduced ask"))
    final = package("104.00")
    s.accept("Treasury-A", s.offer_hash)
    # Independent submissions: each side sends the full exact terms.
    s.confirm("Treasury-A", dict(final))
    s.confirm("Dealer-B", dict(final))
    # These are mock human identifiers, NOT verified human identity/signatures.
    s.approve("Treasury-A", "buyer-human-01", s.offer_hash)
    s.approve("Dealer-B", "seller-human-01", s.offer_hash)
    assert verify_transcript(s.transcript)
    return s.receipt()


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, sort_keys=True))
