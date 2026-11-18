"""Replay a real mixed-wrapper example against two LogicPearl provenance rules."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64


def condition(field, value):
    return {"op": "compare", "left": {"field": field}, "cmp": "eq",
            "right": {"kind": "literal", "value": value}}


def verify_release(wrapper, original, year, release):
    receipt = release["receipt"]
    event = release["log"]
    token = int(event["data"][-64:], 16)
    assert receipt["status"] == "0x1" and receipt["transactionHash"] == event["transactionHash"]
    assert any(log["address"] == wrapper and log["data"] == event["data"]
               and log["topics"] == event["topics"] for log in receipt["logs"])
    burn = next(log for log in receipt["logs"] if log["address"] == wrapper
                and len(log["topics"]) == 4 and log["topics"][0] == TRANSFER
                and log["topics"][2] == ZERO and int(log["topics"][3], 16) == token)
    returned = next(log for log in receipt["logs"] if log["address"] == original
                    and len(log["topics"]) >= 3 and log["topics"][0] == TRANSFER
                    and log["topics"][1][-40:] == wrapper[2:]
                    and log["topics"][2] == burn["topics"][1])
    if year == 2019:
        assert int(returned["topics"][3], 16) == int(event["topics"][1], 16)
    return receipt["transactionHash"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logicpearl", required=True, type=Path)
    args = parser.parse_args()
    binary = str(args.logicpearl.expanduser().resolve())
    d = json.loads((ROOT / "research/catalogue/dada-wrapper.json").read_text())
    wrapper = d["wrapper"]
    assert d["sourceMatch"] == "exact_match"
    fields = {
        "wrapper": {"kind": "scalar", "value_type": "string"},
        "origin_year": {"kind": "scalar", "value_type": "integer"},
    }
    wrapper_matches = condition("wrapper", wrapper)
    policies = {
        "address-only": wrapper_matches,
        "address-and-origin": {"op": "all", "args": [wrapper_matches, condition("origin_year", 2017)]},
    }
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "input.json"
        for name, expr in policies.items():
            (root / f"{name}.json").write_text(json.dumps({
                "schema_version": "logicpearl.evidence_policy.v1", "id": name,
                "inputs": fields, "condition": expr,
            }))
        for year, want in ((2017, "met"), (2019, "not_met"), (None, "unknown")):
            facts = {"wrapper": wrapper}
            if year is not None:
                sample = d["activeSamples"][str(year)]
                assert sample["ownerWord"] != ZERO
                assert sample["wrapEvent"]["address"] == wrapper
                signature = f"Wrapped{year}(uint256,uint256,uint256)"
                assert sample["wrapEvent"]["topics"][0] == d["wrapTopics"][signature]
                assert int(sample["wrapEvent"]["data"][-64:], 16) == int(sample["tokenId"])
                facts["origin_year"] = year
            data.write_text(json.dumps(facts))
            values = {
                name: json.loads(subprocess.check_output(
                    [binary, "evidence", "run", str(root / f"{name}.json"), str(data)],
                    text=True,
                ))["truth"]
                for name in policies
            }
            assert values == {"address-only": "met", "address-and-origin": want}, values
            results[str(year)] = values
        run = subprocess.run([binary, "evidence", "verify", str(root / "address-only.json"),
                              str(root / "address-and-origin.json"), "--entails"],
                             capture_output=True, text=True)
        verdict = json.loads(run.stdout)
        assert run.returncode == 1 and verdict["verdict"]["status"] == "counterexample", verdict
    releases = {
        year: verify_release(wrapper, d["originals"][str(year)], year,
                             d["unwrapExamples"][f"Unwrapped{year}(uint256,uint256,uint256)"])
        for year in (2017, 2019)
    }
    print(json.dumps({"origins": results, "formal_comparison": verdict, "release_receipts": releases}, indent=2))


if __name__ == "__main__":
    main()
