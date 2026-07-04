"""PINS.json structural gate (pass two, leg 1).

Run: python3 -m tests.test_pins

Asserts the pins file parses, carries exactly the expected fields, and that
every head is a well-formed 40-hex string. CI cannot confirm the heads name
real commits in foreign repos; that confirmation is the chair's at witness,
against the repos on axioma. The repo's own history is git's job and is
deliberately not pinned here (a self-referential pin is the Y-round shape
one layer up).
"""

import json
import os
import re

HERE = os.path.dirname(__file__)
PINS = os.path.join(HERE, "..", "PINS.json")

TOP_FIELDS = {"calculus_version", "registry_version", "pinned"}
PIN_FIELDS = {"name", "role", "head", "pinned"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED = {
    "axioma-spec": "9a20f026a3ad3de68a758783891623f2fa2f6de4",
    "exp1-runner": "4d2bf333f242593687cf379e8c19319fdcc5a19e",
}


def main():
    with open(PINS) as fh:
        pins = json.load(fh)
    assert set(pins) == TOP_FIELDS, "unexpected top-level fields: %s" % (
        set(pins) ^ TOP_FIELDS)
    assert pins["calculus_version"] == "FCC-001-v0.4.1"
    assert pins["registry_version"] == "DVEC-001 v1.4"
    names = set()
    for entry in pins["pinned"]:
        assert set(entry) == PIN_FIELDS, "pin fields wrong: %s" % entry
        assert HEX40.match(entry["head"]), (
            "%s head is not 40-hex" % entry["name"])
        assert entry["name"] in EXPECTED, "unexpected pin %s" % entry["name"]
        assert entry["head"] == EXPECTED[entry["name"]], (
            "%s head drifted from the ruled pin" % entry["name"])
        names.add(entry["name"])
    assert names == set(EXPECTED), "missing pins: %s" % (
        set(EXPECTED) - names)
    print("  PINS.json: fields exact, heads well-formed, pins match ruling")
    print("\nall pins tests passed")


if __name__ == "__main__":
    main()
