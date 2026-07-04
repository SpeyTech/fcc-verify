"""fccverify.buildvec: construct golden vector chains by hand.

Test and vector-authoring helper, NOT part of the verdict path. It writes
evidence chains in the frame format of record so the golden vectors are real
committed chains the verifier reads through its own reader.

Transport (corrected per the v1.4 registry, P5):
  claimant chain   AX:FCC:C:v1     the commitment C
  refuter chain    AX:FCC:REG:v1   the attempt genesis (C hash, alpha', N',
                                   completion rule, beacon rule)
                   AX:OBS:v1       per-trial outcome observations, and the
                                   two snapshot fingerprint records (start/end)

Hand-derivation means each vector's k, n, alpha', delta, claimed verdict and
sign are chosen by hand in VECTORS.md so the expected verdict is computable
without running the verifier; this builder serialises those choices.
"""

import json
import struct

from fccverify.reader import commit
from fccverify.registry import (TAG_FCC_C, TAG_FCC_REG, TAG_OBS, TAG_STATE)


def frame_bytes(tag: bytes, payload: bytes) -> bytes:
    cmt = commit(tag, payload)
    return (struct.pack("<I", len(tag)) + tag
            + struct.pack("<Q", len(payload)) + payload + cmt)


def build_chain(records):
    """records: list of (tag, payload_bytes). Returns the chain as bytes."""
    out = b""
    for tag, payload in records:
        out += frame_bytes(tag, payload)
    return out


def _canon(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def claim_c_payload(verdict, delta_num, delta_den, sign=None,
                    alpha_prime_num=1, alpha_prime_den=100, extra=None):
    """A field-complete AX:FCC:C:v1 payload. decision_rule carries the claimed
    verdict, band (delta), and sign; R carries the committed alpha'. Values
    the verdict path reads are real; the rest are placeholders."""
    dr = {"verdict": verdict, "delta_num": delta_num, "delta_den": delta_den}
    if sign is not None:
        dr["sign"] = sign
    data = {
        "seed_core": "00" * 32,
        "battery_blob": "64f2f601d3f3e988d77e14bd6e780d402954808c",
        "pool_blob": "12b1478dfdafbf69eed9af669174b0d5ba767e54",
        "estimator_code": "e791b35",
        "decision_rule": dr,
        "N": 2500,
        "alpha": {"num": 5, "den": 100},
        "R": {"tiers": ["A", "B"],
              "alpha_prime_num": alpha_prime_num,
              "alpha_prime_den": alpha_prime_den},
        "snapshot_predicate": "fingerprint-battery-v1",
        "pattern_set_version": "SRS-EC-001@v1",
        "adapter_version": "gateway@1",
        "redactor_version": "redact@1",
        "verifier_commit": "TBD-PASS-TWO",
        "calculus_version": "FCC-001-v0.4.1",
        "spending_schedule": "OBF-3look",
        "episode_completion_rule": "all-or-void",
        "beacon_rule": {"calendars": ["a", "b"], "K": 1, "D": 6},
        "w_min": {"num": 5, "den": 1000},
    }
    if extra:
        data.update(extra)
    return _canon(data)


def claim_c_hash_of(c_payload):
    """The AX:FCC:C:v1 commit hash, hex. This is what a refuter genesis must
    commit to bind the attempt to the claim (FCC-7.1)."""
    return commit(TAG_FCC_C, c_payload).hex()


def build_claim_chain(c_payload):
    return build_chain([(TAG_STATE, b'{"state":"open"}'),
                        (TAG_FCC_C, c_payload)])


def reg_payload(claim_c_hash, n_prime, alpha_prime_num=1, alpha_prime_den=100):
    """AX:FCC:REG:v1 attempt genesis (FCC-7.1)."""
    return _canon({
        "claim_c_hash": claim_c_hash,
        "alpha_prime_num": alpha_prime_num,
        "alpha_prime_den": alpha_prime_den,
        "n_prime": n_prime,
        "episode_completion_rule": "all-or-void",
        "beacon_rule": {"calendars": ["a", "b"], "K": 1, "D": 6},
    })


def obs_trial(success):
    return _canon({"kind": "trial", "success": bool(success)})


def snapshot(endpoint):
    return _canon({"kind": "snapshot", "endpoint": endpoint})


def build_refuter_chain(claim_c_hash, k, n, n_prime=None,
                        alpha_prime_num=1, alpha_prime_den=100,
                        with_bracket=True, with_genesis=True,
                        genesis_count=1, override_c_hash=None,
                        omit_reg_field=None, mutate_reg=None,
                        misorder_bracket=False):
    """Build a refuter chain: genesis + n trials (k successes) + snapshot
    bracket. Knobs let the vector set exercise the INVALID-ATTEMPT causes.

    n_prime defaults to n (complete). Set n_prime != n for the exact-N'
    completeness vectors (below is INCOMPLETE, above is FABRICATION).
    override_c_hash swaps the bound C hash (FABRICATION binding failure).
    omit_reg_field drops one genesis field (FABRICATION closure failure).
    mutate_reg, a dict->dict callable, edits the genesis payload before
    serialisation (type-fault vectors).
    genesis_count > 1 exercises the single-genesis rule.
    with_genesis=False omits the genesis entirely.
    misorder_bracket=True places both fingerprint markers before the trials
    (present but not enclosing: the Q3 vector).
    """
    if n_prime is None:
        n_prime = n
    records = [(TAG_STATE, b'{"state":"refuter"}')]

    if with_genesis:
        bound = override_c_hash if override_c_hash is not None else claim_c_hash
        reg = json.loads(reg_payload(bound, n_prime,
                                     alpha_prime_num, alpha_prime_den))
        if omit_reg_field:
            reg.pop(omit_reg_field, None)
        if mutate_reg:
            reg = mutate_reg(reg)
        reg_bytes = _canon(reg)
        for _ in range(genesis_count):
            records.append((TAG_FCC_REG, reg_bytes))

    if misorder_bracket:
        records.append((TAG_OBS, snapshot("start")))
        records.append((TAG_OBS, snapshot("end")))
        for i in range(n):
            records.append((TAG_OBS, obs_trial(i < k)))
        return build_chain(records)

    if with_bracket:
        records.append((TAG_OBS, snapshot("start")))
    for i in range(n):
        records.append((TAG_OBS, obs_trial(i < k)))
    if with_bracket:
        records.append((TAG_OBS, snapshot("end")))

    return build_chain(records)
