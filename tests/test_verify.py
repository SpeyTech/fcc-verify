"""Golden replay and determinism tests (requirement 8).

Run: python3 -m tests.test_verify

  1. Golden replay: every committed vector reproduces its manifest verdict.
  2. Determinism: adjudicating the same input twice yields a byte-identical
     verdict record.
"""

import json
import os

from fccverify import verdict

HERE = os.path.dirname(__file__)
GOLDEN = os.path.join(HERE, "..", "golden")


def _load_manifest():
    with open(os.path.join(GOLDEN, "manifest.json")) as fh:
        return json.load(fh)


def _read(name):
    with open(os.path.join(GOLDEN, name), "rb") as fh:
        return fh.read()


def _refuter_for(entry):
    if not entry.get("has_refuter"):
        return None
    return _read(entry["name"].replace(".bin", ".refuter.bin"))


def test_golden_replay():
    manifest = _load_manifest()
    for entry in manifest:
        claim = _read(entry["name"])
        ref = _refuter_for(entry)
        v = verdict.adjudicate(claim, refuter_bytes=ref, attempt_count=1)
        assert v.verdict == entry["expected"], (
            "%s: expected %s got %s" % (entry["name"], entry["expected"],
                                        v.verdict))
        assert v.cause == entry["cause"], (
            "%s: expected cause %s got %s" % (entry["name"], entry["cause"],
                                              v.cause))
    print("  golden replay: %d vectors reproduce their verdict" % len(manifest))


def test_determinism():
    manifest = _load_manifest()
    for entry in manifest:
        claim = _read(entry["name"])
        ref = _refuter_for(entry)
        r1 = json.dumps(verdict.adjudicate(
            claim, refuter_bytes=ref, attempt_count=1).as_record(),
            sort_keys=True)
        r2 = json.dumps(verdict.adjudicate(
            claim, refuter_bytes=ref, attempt_count=1).as_record(),
            sort_keys=True)
        assert r1 == r2, (
            "%s: verdict record not byte-identical across runs" % entry["name"])
    print("  determinism: %d records byte-identical across two runs"
          % len(manifest))


def main():
    test_golden_replay()
    test_determinism()
    print("\nall tests passed")


if __name__ == "__main__":
    main()
