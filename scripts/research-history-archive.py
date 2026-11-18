#!/usr/bin/env python3
"""Cross-reference archived source and early Ethereum History entries by exact address."""

import argparse
import hashlib
import json
import pathlib
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "research/etherr"
CACHE = ROOT / ".cache/etherr-history/archive"
COMMIT = "475bf1f3a9507f54a1ae5959d753e9a36ca262bc"
REPO = "https://github.com/rllola/ethereum-contract-scraper"
HISTORY = "https://www.ethereumhistory.com"


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def community_matches(addresses, tar_path):
    matches = {}
    with tarfile.open(tar_path) as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith("/info.json"):
                continue
            parent = member.name.rsplit("/", 1)[0]
            path = (parent + "/contract.sol").split("/", 1)[1]
            source = archive.extractfile(parent + "/contract.sol").read()
            for entry in json.load(archive.extractfile(member)):
                address = entry["address"].lower()
                if address in addresses:
                    matches.setdefault(address, []).append({
                        "label": parent.rsplit("/", 1)[-1],
                        "source": f"{REPO}/blob/{COMMIT}/{urllib.parse.quote(path)}",
                        "sourceSha256": hashlib.sha256(source).hexdigest(),
                        "status": "address-listed-recompilation-pending",
                    })
    return matches


def lookup(address):
    path = CACHE / (address + ".json")
    if path.exists():
        return
    url = HISTORY + "/api/agent/contracts/" + address
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.load(response)["data"]
        if data["address"].lower() != address:
            raise ValueError("archive address mismatch")
        fields = (
            "deployment_tx_hash", "deployment_block", "deployment_timestamp", "deployer_address",
            "etherscan_contract_name", "token_name", "token_symbol", "verification_status",
            "verification_method",
        )
        result = {key: data[key] for key in fields if data.get(key) is not None}
        result["hasEditorialDescription"] = bool(data.get("short_description"))
        result["links"] = [
            {"title": item.get("title"), "url": item["url"]}
            for item in data.get("links", []) if item.get("url", "").startswith("https://")
        ]
        code = data.get("runtime_bytecode")
        if code:
            result["runtimeSha256"] = hashlib.sha256(bytes.fromhex(code.removeprefix("0x"))).hexdigest()
        save(path, {"status": "address-match", "url": url, **result})
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            save(path, {"status": "not-found", "url": url})
        else:
            raise
    finally:
        time.sleep(3.2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-2015", action="store_true")
    parser.add_argument("--community-tar", type=pathlib.Path, required=True)
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = json.loads((DATA / "records.json").read_text())
    community = community_matches({row["address"] for row in rows}, args.community_tar)
    out = DATA / "history"
    out.mkdir(exist_ok=True)
    if args.archive_2015:
        for row in rows:
            if row["year"] != "2015":
                continue
            try:
                lookup(row["address"])
            except (OSError, ValueError, KeyError) as exc:
                print(f"Archive lookup stopped at {row['address']}: {exc}", flush=True)
                break
    archive = {}
    for row in rows:
        address = row["address"]
        path = CACHE / (address + ".json")
        if path.exists():
            record = json.loads(path.read_text())
            provider_hash = record.pop("runtimeSha256", None)
            if provider_hash:
                record["providerBytecodeSha256"] = provider_hash
                activity = CACHE.parent / ("activity-" + address + ".json")
                if activity.exists():
                    history = json.loads(activity.read_text())["result"]
                    for tx in history:
                        if tx["hash"] == record.get("deployment_tx_hash") and tx.get("input"):
                            calldata_hash = hashlib.sha256(
                                bytes.fromhex(tx["input"].removeprefix("0x"))
                            ).hexdigest()
                            if calldata_hash == provider_hash:
                                record["bytecodeComparison"] = "matches-indexed-creation-input"
                                break
                if "bytecodeComparison" not in record:
                    record["bytecodeComparison"] = (
                        "matches-snapshot-runtime" if provider_hash == row["runtimeSha256"]
                        else "different-from-snapshot-runtime"
                    )
            archive[address] = record
    save(out / "source-leads.json", {
        "communitySourceCommit": COMMIT,
        "communitySource": community,
        "ethereumHistory": archive,
    })
    print(f"{len(community)} community source leads, {len(archive)} archive lookups", flush=True)


if __name__ == "__main__":
    main()
