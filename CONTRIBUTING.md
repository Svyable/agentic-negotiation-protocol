# Contributing to OpenANP

The early project needs falsifiable specifications and working interoperation tests, not slogans. Contributions should preserve:

1. **Authority:** a counterparty never sets another principal's mandate; checks fail closed.
2. **Correctness:** all term economics use exact decimal strings; acceptance and confirmation are hash-bound.
3. **Separations:** negotiation, human approval, and execution are different operations.
4. **Independence:** never imply we implement BNY's patent-pending system. Cite public prior art, including A2CN and Concordia.
5. **Reviewability:** include a minimal reproducible test for any new state transition or negotiation primitive.

Run `python -m unittest discover -s tests -v` and `python -m examples.demo` before filing a PR. For incompatible changes, revise the specification, test vectors and version together.

High-value contributions: formal state invariants, signed transcript receipts, conformance vectors, A2A extension mapping, independent mandate-validation services, multiparty-veto semantics, human escalation, and adversarial tests.