"""Replay address-scoped catalogue decisions using LogicPearl's evidence CLI."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def compare(field, right):
    return {"op": "compare", "left": {"field": field}, "cmp": "eq", "right": right}


def check_policy(id, predicate):
    fields = {"claimed_address": "string", "reviewed_address": "string", "confirmed": "boolean"}
    return {
        "schema_version": "logicpearl.evidence_policy.v1",
        "id": id,
        "inputs": {name: {"kind": "scalar", "value_type": kind} for name, kind in fields.items()},
        "condition": {"op": "all", "args": [
            compare("claimed_address", {"kind": "ref", "reference": {"field": "reviewed_address"}}),
            predicate,
        ]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logicpearl", required=True, type=Path)
    args = parser.parse_args()
    path = ROOT / "research/catalogue/review.json"
    rows = json.loads(path.read_text())["collections"]
    v11 = rows["etheria"]["v11"]
    pride = rows["pridepunks"]
    city = rows["cryptocities"]
    tests = [
        ("etheria-v1-1-previous", v11["previousAddress"],
         v11["creatorDocumentedAddress"], bool(v11["creatorDocumentedAddressCodeBytes"]), "not_met"),
        ("etheria-v1-1-corrected", v11["creatorDocumentedAddress"],
         v11["creatorDocumentedAddress"], bool(v11["creatorDocumentedAddressCodeBytes"]), "met"),
        ("pride-punks-previous-controller", pride["token"], pride["observedOwner"],
         bool(pride["ownerCodeBytes"]), "not_met"),
        ("pride-punks-corrected-controller", pride["observedOwner"], pride["observedOwner"],
         bool(pride["ownerCodeBytes"]), "met"),
        ("cryptocities-immutable-cap", city["original"], city["original"], city["immutableCap"], "unknown"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name, claimed, reviewed, confirmed, expected in tests:
            policy = check_policy(name, compare("confirmed", {"kind": "literal", "value": True}))
            facts = {"claimed_address": claimed, "reviewed_address": reviewed, "confirmed": confirmed}
            spec = directory / "policy.json"
            data = directory / "facts.json"
            spec.write_text(json.dumps(policy))
            data.write_text(json.dumps(facts))
            result = json.loads(subprocess.check_output(
                [str(args.logicpearl.expanduser().resolve()), "evidence", "run", spec, data],
                text=True,
            ))
            assert result["truth"] == expected, result
            print(f"{name}: {result['truth']}")


if __name__ == "__main__":
    main()
