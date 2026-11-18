"""Conformance-oriented tests for the local OpenANP reference engine."""
import copy
import unittest

from examples.demo import demo
from openanp import (
    Argument, ConcessionPolicy, Mandate, ProtocolViolation,
    Session, terms_digest, verify_transcript,
)


def terms(price="102.00"):
    return {"unit_price": price, "quantity": "2", "currency": "USD",
            "asset": "FICTIONAL-TBILL", "settlement": "T+1"}


def mandates():
    a = Mandate("buyer", ("seller",), ("buyer-human",),
                {"unit_price": ("95.00", "105.00"), "quantity": ("1", "5")},
                {"currency": ("USD",), "asset": ("FICTIONAL-TBILL",), "settlement": ("T+1",)})
    b = Mandate("seller", ("buyer",), ("seller-human",),
                {"unit_price": ("101.00", "115.00"), "quantity": ("1", "5")},
                {"currency": ("USD",), "asset": ("FICTIONAL-TBILL",), "settlement": ("T+1",)})
    return a, b


REASON = Argument("Proposed bargain", ("Price quote is illustrative",), "Timely confirmation")


def session(**kw):
    return Session(*mandates(), session_id="test-session", **kw)


class ProtocolTests(unittest.TestCase):
    def test_complete_demo(self):
        receipt = demo()
        self.assertEqual(receipt["status"], "APPROVED_NOT_EXECUTED")
        self.assertEqual(receipt["terms"]["unit_price"], "104.00")
        self.assertEqual(receipt["event_count"], 9)

    def test_two_confirmations_and_approvals_required(self):
        s = session()
        s.propose("seller", terms("104.00"), REASON)
        s.accept("buyer", s.offer_hash)
        with self.assertRaises(ProtocolViolation):
            s.approve("buyer", "buyer-human", s.offer_hash)
        s.confirm("buyer", terms("104.00"))
        with self.assertRaises(ProtocolViolation):
            s.approve("buyer", "buyer-human", s.offer_hash)
        s.confirm("seller", terms("104.00"))
        s.approve("buyer", "buyer-human", s.offer_hash)
        with self.assertRaises(ProtocolViolation):
            s.receipt()
        s.approve("seller", "seller-human", s.offer_hash)
        self.assertEqual(s.state, "APPROVED")
        self.assertTrue(verify_transcript(s.transcript))
        with self.assertRaises(ProtocolViolation):
            s.terminate("buyer", "Too late")

    def test_proposer_mandate_and_allowlist(self):
        s = session()
        with self.assertRaises(ProtocolViolation):
            s.propose("buyer", terms("105.01"), REASON)
        with self.assertRaises(ProtocolViolation):
            s.propose("buyer", dict(terms("100.00"), unknown="x"), REASON)
        with self.assertRaises(ProtocolViolation):
            s.propose("buyer", dict(terms("100.00"), currency="EUR"), REASON)
        self.assertEqual(s.transcript, [])

    def test_float_and_nonfinite_rejected(self):
        a, _ = mandates()
        for bad in (102.0, "NaN", "Infinity", "1e2", "+102", "01.00"):
            with self.subTest(bad=bad):
                with self.assertRaises(ProtocolViolation):
                    a.check(dict(terms(), unit_price=bad))

    def test_reciprocal_authorization_and_unknown_actor(self):
        a, b = mandates()
        bad = Mandate("buyer", ("someone-else",), ("buyer-human",),
                      a.numeric, a.choices)
        with self.assertRaises(ProtocolViolation):
            Session(bad, b)
        with self.assertRaises(ProtocolViolation):
            session().propose("intruder", terms(), REASON)

    def test_turn_taking_and_own_acceptance(self):
        s = session()
        s.propose("buyer", terms("100.00"), REASON)
        with self.assertRaises(ProtocolViolation):
            s.propose("buyer", terms("101.00"), REASON)
        with self.assertRaises(ProtocolViolation):
            s.accept("buyer", s.offer_hash)

    def test_acceptance_must_pass_acceptor_private_mandate(self):
        s = session()
        s.propose("seller", terms("112.00"), REASON)
        with self.assertRaises(ProtocolViolation):
            s.accept("buyer", s.offer_hash)
        self.assertEqual(s.state, "NEGOTIATING")

    def test_stale_acceptance_hash(self):
        s = session()
        s.propose("buyer", terms("100.00"), REASON)
        old = s.offer_hash
        s.propose("seller", terms("104.00"), REASON)
        with self.assertRaises(ProtocolViolation):
            s.accept("buyer", old)
        self.assertEqual(s.state, "NEGOTIATING")

    def test_exact_independent_confirmation(self):
        s = session()
        s.propose("seller", terms("104.00"), REASON)
        s.accept("buyer", s.offer_hash)
        with self.assertRaises(ProtocolViolation):
            s.confirm("buyer", terms("104.0"))  # equal numerically, NOT identical terms
        self.assertEqual(s.transcript[-1]["kind"], "ACCEPT")
        s.confirm("buyer", terms("104.00"))
        with self.assertRaises(ProtocolViolation):
            s.confirm("buyer", terms("104.00"))

    def test_approver_and_digest_bound(self):
        s = session()
        s.propose("seller", terms("104.00"), REASON)
        s.accept("buyer", s.offer_hash)
        s.confirm("seller", terms("104.00"))
        s.confirm("buyer", terms("104.00"))
        with self.assertRaises(ProtocolViolation):
            s.approve("buyer", "fake-human", s.offer_hash)
        with self.assertRaises(ProtocolViolation):
            s.approve("buyer", "buyer-human", "0" * 64)
        self.assertEqual(s.state, "AWAITING_APPROVAL")

    def test_round_limit(self):
        s = session(max_offers=1)
        s.propose("buyer", terms("100.00"), REASON)
        with self.assertRaises(ProtocolViolation):
            s.propose("seller", terms("104.00"), REASON)

    def test_tamper_evident_transcript(self):
        s = session()
        original = terms("100.00")
        s.propose("buyer", original, REASON)
        original["unit_price"] = "0.00"
        self.assertEqual(s.transcript[0]["data"]["terms"]["unit_price"], "100.00")
        good = s.transcript
        self.assertTrue(verify_transcript(good))
        corrupted = copy.deepcopy(good)
        corrupted[0]["data"]["terms"]["unit_price"] = "99.00"
        self.assertFalse(verify_transcript(corrupted))
        corrupted = copy.deepcopy(good)
        corrupted[0]["previous_hash"] = "f" * 64
        self.assertFalse(verify_transcript(corrupted))

    def test_termination(self):
        s = session()
        s.terminate("buyer", "No commercial overlap")
        self.assertEqual(s.state, "TERMINATED")
        with self.assertRaises(ProtocolViolation):
            s.propose("seller", terms("104.00"), REASON)

    def test_argument_rejects_empty_premises(self):
        s = session()
        with self.assertRaises(ProtocolViolation):
            s.propose("buyer", terms("100.00"), Argument("because", ()))
        self.assertEqual(s.transcript, [])

    def test_concession_strategy(self):
        buyer = ConcessionPolicy("buyer", "98.00", "105.00")
        seller = ConcessionPolicy("seller", "110.00", "101.00")
        b = [float(buyer.quote(i)) for i in range(5)]
        a = [float(seller.quote(i)) for i in range(5)]
        self.assertEqual(b[0], 98.0)
        self.assertEqual(b[-1], 105.0)
        self.assertEqual(a[0], 110.0)
        self.assertEqual(a[-1], 101.0)
        self.assertEqual(b, sorted(b))
        self.assertEqual(a, sorted(a, reverse=True))
        self.assertFalse(buyer.acceptable("106.00", 4))
        self.assertTrue(buyer.acceptable("104.00", 4))

    def test_term_hash_is_key_order_invariant(self):
        original = terms("104.00")
        inverted = dict(reversed(list(original.items())))
        self.assertEqual(terms_digest(original), terms_digest(inverted))


if __name__ == "__main__":
    unittest.main()
