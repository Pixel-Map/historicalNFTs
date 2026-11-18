#!/usr/bin/env python3
"""Cross-check candidate addresses against two pinned public source archives."""

import concurrent.futures
import json
import pathlib
import re
import subprocess
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "research/etherr"
CACHE = ROOT / ".cache/etherr-history/source-index"
ARCHIVES = {
    "tintinweb/smart-contract-sanctuary-ethereum": (
        "015d0105102504dc8733a18c3543f87f1829a5e8", "contracts/mainnet",
    ),
    "smartbugs/smartbugs-wild": (
        "91ec17573d3e0f42cc7d4a6d2883b941901c26e5", "contracts",
    ),
}


def tree(repo, ref):
    path = CACHE / (repo.split("/")[-1] + "-" + ref + ".json")
    if path.exists():
        return json.loads(path.read_text())
    payload = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/git/trees/{ref}"], text=True, timeout=45,
    )
    data = json.loads(payload)
    if data.get("truncated"):
        raise ValueError(f"Truncated tree {repo} {ref}")
    path.write_text(payload)
    return data


def resolve(repo, ref, path):
    for name in path.split("/"):
        ref = next(item["sha"] for item in tree(repo, ref)["tree"] if item["path"] == name)
    return ref


def inspect(repo, ref, path, addresses):
    hits = {}
    for item in tree(repo, ref)["tree"]:
        match = re.match(r"^(?:0x)?([0-9a-fA-F]{40})(?:_|\.)", item["path"])
        if item["type"] != "blob" or not match:
            continue
        address = "0x" + match[1].lower()
        if address in addresses:
            hits.setdefault(address, []).append({
                "path": path + "/" + item["path"],
                "gitBlobSha": item["sha"],
                "status": "address-listed-recompilation-pending",
            })
    return hits


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    addresses = {
        row["address"] for row in json.loads((DATA / "records.json").read_text())
    }
    output = {}
    for repo, (ref, path) in ARCHIVES.items():
        if repo == "smartbugs/smartbugs-wild":
            root = resolve(repo, ref, path)
            jobs = [(root, path, addresses)]
            permalink = f"https://github.com/{repo}/tree/{ref}/{path}"
        else:
            root = resolve(repo, ref, path)
            prefix_addresses = {}
            for address in addresses:
                prefix_addresses.setdefault(address[2:4], set()).add(address)
            jobs = [
                (item["sha"], path + "/" + item["path"], prefix_addresses[item["path"]])
                for item in tree(repo, root)["tree"] if item["path"] in prefix_addresses
            ]
            permalink = f"https://github.com/{repo}/tree/{ref}/{path}"
        by_address = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            lookups = [
                pool.submit(inspect, repo, sha, directory, subset)
                for sha, directory, subset in jobs
            ]
            for lookup in concurrent.futures.as_completed(lookups):
                for address, hits in lookup.result().items():
                    by_address.setdefault(address, []).extend(hits)
        output[repo] = {
            "reference": ref,
            "tree": root,
            "path": path,
            "url": permalink,
            "searchedTrees": len(jobs),
            "matches": dict(sorted(by_address.items())),
        }
        print(repo, "matched", len(by_address), "candidate addresses", flush=True)
    out = DATA / "history" / "source-index.json"
    out.parent.mkdir(exist_ok=True)
    temporary = out.with_suffix(".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n")
    temporary.replace(out)


if __name__ == "__main__":
    main()
