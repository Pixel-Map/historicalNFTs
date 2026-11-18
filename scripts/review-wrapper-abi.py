"""Learn DADA origin from public ABI outputs and test on a later event cohort."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / "research/catalogue"


def features(row):
    uri = urlsplit(row["tokenURI"] or "")
    match = re.fullmatch(r"([0-9]+)\.json", uri.path.rsplit("/", 1)[-1])
    output = {
        "returns_owner": row["ownerOfResponded"],
        "returns_https": uri.scheme == "https",
        "host": uri.hostname or "missing",
    }
    if match:
        output["uri_number"] = int(match[1])
        assert output["uri_number"] == int(row["token_id"])
        assert output["uri_number"] < 2 ** 53
    return output


def write_csv(path, rows, fields):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*fields, "is_2017"])
        writer.writeheader()
        for row in rows:
            report = {key: row["features"][key] for key in fields}
            report["is_2017"] = row["origin_year"] == 2017
            writer.writerow({k: str(v).lower() if isinstance(v, bool) else v for k, v in report.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logicpearl", required=True, type=Path)
    args = parser.parse_args()
    binary = str(args.logicpearl.expanduser().resolve())
    d, proof = (
        json.loads((ROOT / file).read_text())
        for file in ("dada-abi-observations.json", "dada-wrapper.json")
    )
    for key in ("chainId", "wrapper", "blockNumber", "blockHash", "runtimeSha256"):
        assert d[key] == proof[key], key
    ids = set()
    rows = d["rows"]
    for row in rows:
        year = row["origin_year"]
        assert row["token_id"] not in ids
        ids.add(row["token_id"])
        assert str(int(row["log_data"][-64:], 16)) == row["token_id"]
        assert row["topic"] == proof["wrapTopics"][f"Wrapped{year}(uint256,uint256,uint256)"]
        assert (row["split"] == "test") == (row["block"] >= d["holdoutStartBlock"])
        row["features"] = features(row)
    cohorts = {split: [row for row in rows if row["split"] == split] for split in ("train", "test")}
    complete = {split: [row for row in group if "uri_number" in row["features"]]
                for split, group in cohorts.items()}
    reports = {}
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name, fields, groups in (
            ("status-and-host", ("returns_owner", "returns_https", "host"), cohorts),
            ("include-uri-number", ("returns_owner", "returns_https", "host", "uri_number"), complete),
        ):
            traces = folder / f"{name}.csv"
            archive = folder / name
            write_csv(traces, groups["train"], fields)
            build = subprocess.run([binary, "build", str(traces), "--label-column", "is_2017",
                                    "--output-dir", str(archive)], capture_output=True, text=True)
            if name == "status-and-host":
                collisions = {}
                for row in groups["train"]:
                    signature = tuple(row["features"][key] for key in fields)
                    collisions.setdefault(signature, set()).add(row["origin_year"])
                mixed_patterns = sum(len(labels) > 1 for labels in collisions.values())
                assert build.returncode != 0 and mixed_patterns, build.stderr
                reports[name] = {"conflicting_output_patterns": mixed_patterns,
                                 "error": build.stderr.strip()}
                continue
            assert build.returncode == 0, build.stderr
            subprocess.run([binary, "artifact", "verify", str(archive)], check=True, capture_output=True)
            counts = Counter()
            matched = set()
            for row in groups["test"]:
                case = {k: row["features"][k] for k in fields}
                result = json.loads(subprocess.check_output(
                    [binary, "run", str(archive), "-", "--json"], input=json.dumps(case), text=True))
                expected = row["origin_year"] == 2017
                counts["correct"] += result["allow"] == expected
                counts["prefix_heuristic_correct"] += str(case["uri_number"]).startswith(
                    str(row["origin_year"]))
                counts["evaluated"] += 1
                matched.update(rule["label"] for rule in result["matched_rules"])
            reports[name] = {**counts, "abstained": len(cohorts["test"]) - counts["evaluated"],
                             "matched_rules": sorted(matched),
                             "training_evaluated": len(groups["train"])}
            challenge = d["challenge"]
            assert challenge["readBlock"] == d["blockNumber"]
            assert challenge["wrapEvent"]["address"] == d["wrapper"]
            assert challenge["wrapEvent"]["topics"][0] == proof["wrapTopics"]["Wrapped2019(uint256,uint256,uint256)"]
            assert int(challenge["wrapEvent"]["data"][-64:], 16) == int(challenge["tokenId"])
            case = features({"tokenURI": challenge["tokenURI"],
                             "ownerOfResponded": challenge["ownerOfResponded"],
                             "token_id": challenge["tokenId"]})
            candidate = json.loads(subprocess.check_output(
                [binary, "run", str(archive), "-", "--json"], input=json.dumps(case), text=True))
            assert candidate["allow"] is True and challenge["originYear"] == 2019
            reports[name]["live_read_counterexample"] = {
                "token_id": challenge["tokenId"], "event_year": challenge["originYear"],
                "predicted_year": 2017, "observed_wrap_transaction": challenge["wrapEvent"]["transactionHash"],
                "matched_rules": [rule["label"] for rule in candidate["matched_rules"]],
            }
    replay = d["sameIdRewrapped"]
    earlier, later = replay["earlierBurn"], replay["laterWrap"]
    assert earlier["address"] == later["address"] == d["wrapper"]
    assert int(earlier["blockNumber"], 16) < int(later["blockNumber"], 16)
    assert earlier["data"][-64:] == later["data"][-64:]
    assert int(later["data"][-64:], 16) == int(replay["wrappedTokenId"])

    sizes = {split: dict(Counter(row["origin_year"] for row in group))
             for split, group in cohorts.items()}
    print(json.dumps({"cohorts": sizes, "results": reports,
                      "same_id_rewrapped": {"token_id": replay["wrappedTokenId"],
                                            "earlier": earlier["transactionHash"],
                                            "later": later["transactionHash"]}}, indent=2))


if __name__ == "__main__":
    main()
