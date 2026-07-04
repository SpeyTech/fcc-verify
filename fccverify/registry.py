"""fccverify.registry: the DVEC-001 v1.4 evidence tag set.

The verifier's own copy of the registry, for the membership check on foreign
chains. This is a fifth reader of the registry in the sense of the DVEC v1.4
amendment, but it is adversary-side, not claimant-side: it exists to reject an
unregistered tag on a chain the verifier did not write. It derives from the
same specification as the four enforcing copies (dvec.h, ledger.c, chain.py,
ax-rtm-verify.py), never from their code.

DVEC-001 v1.4 registered the AX:FCC block alongside the base evidence tags.
Chain tags (AX:LEDGER:v1, DVM:*) are protocol prefixes, not evidence types,
and are not members of this set: a chain tag appearing as an evidence record
tag is itself a fault.
"""

# Base evidence tags (DVEC-001 4.4).
TAG_STATE = b"AX:STATE:v1"
TAG_TRANS = b"AX:TRANS:v1"
TAG_OBS = b"AX:OBS:v1"
TAG_POLICY = b"AX:POLICY:v1"
TAG_PROOF = b"AX:PROOF:v1"

# FCC-001 claim tags (registered DVEC-001 v1.4).
TAG_FCC_C = b"AX:FCC:C:v1"
TAG_FCC_TS = b"AX:FCC:TS:v1"
TAG_FCC_DEV = b"AX:FCC:DEV:v1"
TAG_FCC_REG = b"AX:FCC:REG:v1"
TAG_FCC_VERDICT = b"AX:FCC:VERDICT:v1"

REGISTERED_EVIDENCE_TAGS = frozenset({
    TAG_STATE, TAG_TRANS, TAG_OBS, TAG_POLICY, TAG_PROOF,
    TAG_FCC_C, TAG_FCC_TS, TAG_FCC_DEV, TAG_FCC_REG, TAG_FCC_VERDICT,
})

# Chain tags, explicitly not evidence types. Named so the verifier can
# distinguish "chain tag misused as evidence" from "unknown tag".
CHAIN_TAGS = frozenset({
    b"AX:LEDGER:v1", b"DVM:LEDGER:v1", b"DVM:STATE:v1", b"DVM:INGRESS:v1",
})
