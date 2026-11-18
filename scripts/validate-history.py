"""Check the second-pass evidence against the unchanged source snapshot."""

import collections
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "research/etherr"
HISTORY = ROOT / "history"
KNOWN = {
    "0xd875c876435a79b5eb2099d06aa97ffd4fb6fc9d",
    "0xb4e34890034a13325363b3226dce8eeec292d626",
}


def read(path):
    return json.loads(path.read_text())


def address(value):
    return bool(re.fullmatch(r"0x[0-9a-fA-F]{40}", value))


def tx_hash(value):
    return bool(re.fullmatch(r"0x[0-9a-fA-F]{64}", value))


snapshot = read(ROOT / "source.json")
original = {row["address"]: row for row in read(ROOT / "records.json")}
assert KNOWN <= original.keys()
candidates = {a: item for a, item in original.items() if a not in KNOWN}
history = read(HISTORY / "evidence.json")
evidence = history["records"]
assert evidence.keys() == candidates.keys()
assert history["chainId"] == snapshot["chainId"] == 1
assert history["throughBlock"] == snapshot["blockNumber"]
families = collections.defaultdict(list)
actors = collections.defaultdict(list)
for a, item in evidence.items():
    baseline = candidates[a]
    families[baseline["runtimeSha256"]].append(a)
    assert item["snapshotBalanceWei"] == baseline["balanceWei"]
    assert item["classification"] == "unresolved" and item["nextCheck"]
    assert bool(item["capturedSourceSurface"]) == (baseline["sourceStatus"] == "available")
    creation = item["creation"]
    direct = item["directActivity"]
    for section in (creation, direct):
        assert section["status"] in {"observed", "none-returned", "pending", "lookup-error"}
        assert bool(section.get("rows")) == (section["status"] == "observed")
    for row in creation.get("rows", []):
        assert row["contractAddress"].lower() == a and tx_hash(row["txHash"])
        creator = row.get("contractFactory") or row["contractCreator"]
        assert address(creator)
        actors[creator.lower()].append(a)
    txs = direct.get("rows", [])
    assert len(txs) <= 8
    assert all(tx_hash(tx["hash"]) and int(tx["blockNumber"]) <= history["throughBlock"] for tx in txs)
    ordering = [(int(tx["blockNumber"]), int(tx["transactionIndex"])) for tx in txs]
    assert ordering == sorted(ordering)
    if sample := item["firstSuccessfulDirectCallSample"]:
        tx = next(tx for tx in txs if tx["hash"] == sample)
        assert tx["to"].lower() == a and tx["isError"] == "0"
        assert sample not in {row["txHash"] for row in creation["rows"]}
assert history["exactRuntimeFamilies"] == {k: v for k, v in families.items() if len(v) > 1}
assert history["sharedDeploymentActors"] == {k: v for k, v in actors.items() if len(v) > 1}
assert all(item["runtimeFamilySize"] == len(families[candidates[a]["runtimeSha256"]]) for a, item in evidence.items())

factory_deployments = {
    a: row for a, item in evidence.items()
    for row in item["creation"]["rows"] if row.get("contractFactory")
}
factory_traces = read(HISTORY / "factory-traces.json")
assert factory_traces.keys() == factory_deployments.keys()
for a, result in factory_traces.items():
    deployment = factory_deployments[a]
    assert result["transactionHash"] == deployment["txHash"]
    assert bool(result["traces"]) == (result["status"] == "observed")
    for trace in result["traces"]:
        assert trace["txHash"] == deployment["txHash"]
        assert trace["chainId"] == "1" and trace["status"] is True
        assert trace["type"] in {"CREATE", "CREATE2"}
        assert trace["from"].lower() == deployment["contractFactory"].lower()
        assert trace["to"].lower() == a
        assert trace["blockNumber"] == int(deployment["blockNumber"]) <= history["throughBlock"]

funded = {a for a, item in original.items() if int(item["balanceWei"]) > 0}
balances = read(HISTORY / "balances.json")
assert balances["balanceWei"].keys() == funded
assert balances["chainId"] == 1 and balances["blockNumber"] > snapshot["blockNumber"]
assert tx_hash(balances["blockHash"])
assert all(re.fullmatch(r"0|[1-9][0-9]*", v) for v in balances["balanceWei"].values())
if independent := balances.get("independentCheck"):
    assert independent["blockHash"] == balances["blockHash"]
    expected = dict(sorted(balances["balanceWei"].items(), key=lambda item: int(item[1]), reverse=True)[:5])
    assert independent["balanceWei"] == expected
flows = read(HISTORY / "funded-flows.json")
assert flows["blockNumber"] == balances["blockNumber"] and flows["blockHash"] == balances["blockHash"]
assert flows["records"].keys() == (funded & candidates.keys())
for a, item in flows["records"].items():
    assert item["oldBalanceWei"] == original[a]["balanceWei"]
    assert item["newBalanceWei"] == balances["balanceWei"][a]
    for side, field in (("outbound", "from"), ("inbound", "to")):
        sample = item[side]
        assert sample["status"] in {"observed", "none-returned", "pending", "lookup-error"}
        assert bool(sample.get("samples")) == (sample["status"] == "observed")
        for tx in sample.get("samples", []):
            assert tx[field].lower() == a and int(tx["value"]) > 0 and tx_hash(tx["txHash"])
            assert tx["blockNumber"] <= balances["blockNumber"]

leads = read(HISTORY / "source-leads.json")
assert leads["communitySource"].keys() <= original.keys()
assert leads["ethereumHistory"].keys() == {a for a in candidates if candidates[a]["year"] == "2015"}
for a, lead in leads["ethereumHistory"].items():
    if lead.get("bytecodeComparison") == "matches-indexed-creation-input":
        txs = evidence[a]["directActivity"]["rows"]
        tx = next(tx for tx in txs if tx["hash"] == lead["deployment_tx_hash"])
        assert tx["inputSha256"] == lead["providerBytecodeSha256"]

index = read(HISTORY / "source-index.json")
assert len(index) == 2
for archive in index.values():
    assert re.fullmatch(r"[0-9a-f]{40}", archive["reference"])
    assert archive["matches"].keys() <= original.keys()
    for a, matches in archive["matches"].items():
        assert matches
        for match in matches:
            assert a[2:] in match["path"].lower()
            assert re.fullmatch(r"[0-9a-f]{40}", match["gitBlobSha"])

findings = read(HISTORY / "findings.json")
assert findings["addresses"].keys() <= candidates.keys()
for a, finding in findings["addresses"].items():
    assert finding["finding"] and finding["nextCheck"]
    if published := finding.get("publishedRuntimeEvidence"):
        assert published["sha256"] == candidates[a]["runtimeSha256"]
    if compilation := finding.get("compilationEvidence"):
        assert compilation["runtimeSha256"] == candidates[a]["runtimeSha256"]
        assert any(
            row["txHash"] == compilation["creationTransaction"]
            for row in evidence[a]["creation"]["rows"]
        )
        assert re.fullmatch(r"[0-9a-f]{64}", compilation["creationInputSha256"])
    if activity := finding.get("activityEvidence"):
        assert tx_hash(activity["transactionHash"]) and tx_hash(activity["blockHash"])
        registrar_change, mint, wrapped = activity["logs"]
        assert registrar_change["address"] == a
        assert mint["address"] == wrapped["address"]
        assert mint["topics"][1] == "0x" + "0" * 64
        domain = activity["domainIdHex"]
        assert domain[2:] == registrar_change["data"][2:66]
        assert domain == mint["topics"][3] == wrapped["topics"][2]
abis = read(HISTORY / "recompiled-abis.json")
assert abis.keys() == {
    a for a, finding in findings["addresses"].items() if finding.get("compilationEvidence")
}
for a, result in abis.items():
    proof = findings["addresses"][a]["compilationEvidence"]
    for key in ("contract", "runtimeSha256", "creationInputSha256"):
        assert result[key] == proof[key]
    assert result["abi"] and all(isinstance(item, dict) for item in result["abi"])
for f in findings["families"]:
    assert len(families[f["runtimeSha256"]]) > 1
    source = candidates[f["representative"]]
    assert source["runtimeSha256"] == f["runtimeSha256"] and source["sourceRuntimeAgrees"]
    with gzip.open(ROOT / "contracts" / (source["address"] + ".json.gz"), "rt") as handle:
        assert f["sourceFile"] in json.load(handle)["sourceResponse"]["sources"]
print(f"Validated {len(evidence)} candidate records, {len(funded)} balances and {len(findings['families'])} family findings")
