"""fccverify.reader: the verifier's own frame reader (requirement 2, Y4).

Reimplemented from the FCC-001 frame format of record, NOT imported from the
claimant's chain.py. The verifier reads foreign chains (claimant and refuter),
so sharing the writer's reader would let one bug hide in both. This is the
Tier B instrument for chain reading.

Frame format of record:
    u32le tag_len | tag | u64le payload_len | payload | commit[32]
    commit  = SHA-256(tag || LE64(payload_len) || payload)
    genesis = e0 = commit("AX:STATE:v1", GENESIS_PAYLOAD)
              L0 = SHA-256("AX:LEDGER:v1" || e0)
    extend  = Ln = SHA-256("AX:LEDGER:v1" || Ln-1 || commit)

Two checks on read:
    integrity  - commit and link recomputation, torn-frame refusal
    membership - tag is in the DVEC v1.4 evidence registry (cause MALFORMED)

The membership check is what the runner's integrity-only read_frames defers
to the verifier. An unregistered tag on a foreign chain is MALFORMED here.
"""

import hashlib
import struct

from fccverify.registry import REGISTERED_EVIDENCE_TAGS

CHAIN_TAG = b"AX:LEDGER:v1"
TAG_STATE = b"AX:STATE:v1"
GWL_TAG_MAX = 32
GWL_PAYLOAD_MAX = 1 << 20

# Byte-identical to AX_GENESIS_PAYLOAD in axioma-audit audit.h and to
# chain.py GENESIS_PAYLOAD. Reproduced here from the spec of record, not
# imported, so the verifier shares no code with the writer.
GENESIS_PAYLOAD = (
    b'{"component":"axilog-core",'
    b'"evidence_type":"AX:STATE:v1",'
    b'"is_terminal":false,'
    b'"platform":"universal",'
    b'"state_hash":"'
    + b"0" * 64 +
    b'"}'
)


class ReaderError(Exception):
    """A structural fault in a chain: torn frame, bad length, commit or link
    divergence. Distinct from a membership fault, which is reported as a
    finding rather than raised, so the caller can attribute it to a verdict
    cause."""


def commit(tag: bytes, payload: bytes) -> bytes:
    """axilog_commit (SRS-007): domain-separated SHA-256.
    commit = SHA-256(tag || LE64(len(payload)) || payload)."""
    h = hashlib.sha256()
    h.update(tag)
    h.update(struct.pack("<Q", len(payload)))
    h.update(payload)
    return h.digest()


def genesis_head() -> bytes:
    e0 = commit(TAG_STATE, GENESIS_PAYLOAD)
    return hashlib.sha256(CHAIN_TAG + e0).digest()


def extend(prev_head: bytes, cmt: bytes) -> bytes:
    return hashlib.sha256(CHAIN_TAG + prev_head + cmt).digest()


class Frame:
    """One decoded frame. index is 0-based position in the chain."""

    __slots__ = ("index", "tag", "payload", "commit", "head_after",
                 "registered")

    def __init__(self, index, tag, payload, cmt, head_after, registered):
        self.index = index
        self.tag = tag
        self.payload = payload
        self.commit = cmt
        self.head_after = head_after
        self.registered = registered

    def __repr__(self):
        return "Frame(%d, %r, registered=%s)" % (
            self.index, self.tag, self.registered)


def read_frames(data: bytes):
    """Parse and verify a chain from bytes. Yields Frame objects in order.

    Raises ReaderError on any structural fault: torn frame, out-of-bound
    length, commit mismatch, or link divergence. These are integrity faults
    and mean the chain is not a valid chain at all.

    Does NOT raise on an unregistered tag: it sets Frame.registered False and
    yields the frame, so the caller attributes membership to the MALFORMED
    verdict cause at the well-formedness stage rather than conflating a
    structural fault with a registry fault.
    """
    head = genesis_head()
    idx = 0
    off = 0
    n = len(data)
    while off < n:
        frame_start = off
        if off + 4 > n:
            raise ReaderError("torn tag_len at %d" % frame_start)
        (tag_len,) = struct.unpack("<I", data[off:off + 4])
        off += 4
        if tag_len == 0 or tag_len > GWL_TAG_MAX:
            raise ReaderError("bad tag_len %d at %d" % (tag_len, frame_start))
        if off + tag_len > n:
            raise ReaderError("torn tag at %d" % frame_start)
        tag = data[off:off + tag_len]
        off += tag_len
        if off + 8 > n:
            raise ReaderError("torn payload_len at %d" % frame_start)
        (payload_len,) = struct.unpack("<Q", data[off:off + 8])
        off += 8
        if payload_len == 0 or payload_len > GWL_PAYLOAD_MAX:
            raise ReaderError(
                "bad payload_len %d at %d" % (payload_len, frame_start))
        if off + payload_len > n:
            raise ReaderError("torn payload at %d" % frame_start)
        payload = data[off:off + payload_len]
        off += payload_len
        if off + 32 > n:
            raise ReaderError("torn commit at %d" % frame_start)
        stored = data[off:off + 32]
        off += 32
        recomputed = commit(tag, payload)
        if stored != recomputed:
            raise ReaderError(
                "commit mismatch at frame %d (%s)"
                % (idx, tag.decode("latin-1")))
        head = extend(head, recomputed)
        registered = tag in REGISTERED_EVIDENCE_TAGS
        yield Frame(idx, tag, payload, recomputed, head, registered)
        idx += 1


def read_chain_file(path: str):
    """Convenience: read a chain from a file path. Returns a list of Frames.
    Structural faults raise ReaderError; membership is per-frame."""
    with open(path, "rb") as fh:
        data = fh.read()
    return list(read_frames(data))
