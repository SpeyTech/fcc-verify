# fcc-verify

The FCC-001 verdict program. Adjudicates a falsifiable claim under the
Falsifiable Claim Calculus (FCC-001): given a claimant evidence chain and
a refuter attempt chain, it emits exactly one of UPHELD, REFUTED,
INVALID-ATTEMPT, INVALID-CLAIM, deterministically, from the committed
rules alone. No prose adjudication.

The SDK is how you make a claim, fcc-verify is how your enemy checks it,
and they share a specification, not code. The verifier depends on no
claimant-side tooling: an adjudicator sharing the claimant's arithmetic or
frame reader would let one bug hide in both, which is the shared-instrument
error Tier B exists to catch.

This repository is minimal by design. A third party adjudicating or
refuting a claim clones exactly this: the FCC-001 specification, the
verifier, and its golden vectors. It does not need the experiment runner,
the mock tools, or the agent loop. The verifier carries its own verifying
reader, since reading foreign chains (claimant and refuter) is its first
job, and it performs the registry membership check that the runner's
integrity-only reader defers to it (cause MALFORMED).

This repository's head is the "Verifier commit" pin in the FCC-001
commitment object C, completing the pin triple: harness (axioma-l0),
experiment (exp1-runner), verifier (fcc-verify), each artefact minimal.

Registered against DVEC-001 v1.4 (AX:FCC evidence tag block). Verdict
records are AX:FCC:VERDICT:v1.

William Murray, Spey Systems Ltd (SC889983), Inverness.
