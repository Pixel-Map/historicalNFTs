#!/usr/bin/env python3
"""Collect bounded, read-only historical evidence with a resumable local cache."""

import argparse
import concurrent.futures
import datetime
import gzip
import hashlib
import json
import pathlib
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/etherr"
OUT = SOURCE / "history"
CACHE = ROOT / ".cache/etherr-history"
ROUTESCAN = "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api"
KNOWN = {
    "0xd875c876435a79b5eb2099d06aa97ffd4fb6fc9d",
    "0xb4e34890034a13325363b3226dce8eeec292d626",
}
DATA_API = "https://api.routescan.io/v2/network/mainnet/evm/1"
CALL_FIELDS = (
    "hash", "blockHash", "blockNumber", "timeStamp", "transactionIndex",
    "from", "to", "value", "methodId", "isError", "txreceipt_status", "contractAddress",
)
LOCK = threading.Lock()
NEXT_REQUEST = 0.0


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text())


def lookup(key, endpoint=ROUTESCAN, **query):
    global NEXT_REQUEST
    path = CACHE / (key + ".json")
    if path.exists():
        return read_json(path)
    url = endpoint + "?" + urllib.parse.urlencode(query)
    for attempt in range(3):
        with LOCK:
            wait = NEXT_REQUEST - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            NEXT_REQUEST = time.monotonic() + 0.55
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                data = json.load(response)
            native = endpoint != ROUTESCAN
            result = data.get("items" if native else "result")
            if not isinstance(result, list):
                raise ValueError(str(result)[:150])
            if not native and data.get("status") != "1" and not (
                not result and data.get("message", "").startswith("No ")
            ):
                raise ValueError(str(data.get("message"))[:150])
            evidence = {
                "url": url,
                "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "result": result,
                "paginated": bool(data.get("link", {}).get("nextToken") or data.get("link", {}).get("next")),
            }
            write_json(path, evidence)
            return evidence
        except (OSError, ValueError) as exc:
            error = str(exc)
            if isinstance(exc, urllib.error.HTTPError) and exc.code in {401, 402, 403, 429}:
                with LOCK:
                    NEXT_REQUEST = max(NEXT_REQUEST, time.monotonic() + 15)
            if attempt < 2:
                time.sleep(2 ** attempt)
    return {"url": url, "error": error}


def deployment(batch):
    addresses = ",".join(row["address"] for row in batch)
    return lookup(
        "creation-" + batch[0]["address"], module="contract",
        action="getcontractcreation", contractaddresses=addresses,
    )


def activity(row, block):
    return lookup(
        "activity-" + row["address"], module="account", action="txlist",
        address=row["address"], startblock=0, endblock=block,
        page=1, offset=8, sort="asc",
    )


def compact_activity(rows, block):
    pending = [
        row for row in rows if not (CACHE / ("activity-" + row["address"] + ".json")).exists()
    ]
    if not pending:
        return {"result": []}
    addresses = ",".join(row["address"] for row in pending)
    response = lookup(
        "direct-group-" + hashlib.sha256(addresses.encode()).hexdigest()[:24], DATA_API + "/transactions", toAddresses=addresses,
        blockNumberTo=block + 1, sort="asc", limit=100,
    )
    if "error" in response:
        return response
    results = {row["address"]: [] for row in pending}
    for item in response["result"]:
        address = (item.get("to") or "").lower()
        if address not in results or item["chainId"] != "1" or item["blockNumber"] > block:
            raise ValueError("unexpected data in address-filtered history")
        results[address].append({
            "hash": item["id"],
            "blockNumber": str(item["blockNumber"]),
            "timeStamp": str(int(datetime.datetime.fromisoformat(item["timestamp"]).timestamp())),
            "transactionIndex": str(item["index"]),
            "from": item["from"],
            "to": item["to"],
            "value": item["value"],
            "methodId": item.get("methodId"),
            "isError": "0" if item["status"] is True else "1",
        })
    for row in pending:
        address = row["address"]
        direct = results[address]
        if (response.get("paginated") or len(response["result"]) == 100) and len(direct) < 8:
            activity(row, block)
            continue
        write_json(CACHE / ("activity-" + address + ".json"), {**response, "result": direct[:8]})
    return response


def funded_flow(rows, side, through):
    address_list = [row["address"] for row in rows]
    addresses = ",".join(address_list)
    response = lookup(
        "flows-" + side + "-" + hashlib.sha256((addresses + through).encode()).hexdigest()[:24],
        DATA_API + "/internal-operations",
        **{side + "Addresses": addresses},
        timestampTo=through, sort="asc", limit=100, valueFromEq="1",
    )
    if "error" in response:
        return response
    results = {address: [] for address in address_list}
    for item in response["result"]:
        address = (item.get(side) or "").lower()
        if address not in results or item["chainId"] != "1":
            raise ValueError("unexpected data in address-filtered trace history")
        if item["status"] is True and int(item["value"]) > 0:
            results[address].append({
                key: item[key] for key in (
                    "txHash", "blockNumber", "timestamp", "opIndex", "from", "to", "value", "type",
                ) if key in item
            })
    for address, items in results.items():
        write_json(CACHE / (f"flows-{side}-{address}.json"), {
            **response, "result": items[:8],
            "paginated": response.get("paginated") or len(response["result"]) == 100,
        })
    return response


def extension_source(row):
    return lookup(
        "source-" + row["address"],
        module="contract", action="getsourcecode", address=row["address"],
    )


def funded_cutoff(balances):
    timestamp = datetime.datetime.fromisoformat(balances["blockTimestamp"])
    return (timestamp + datetime.timedelta(seconds=1)).isoformat()


def assemble_funded(rows):
    balances = read_json(OUT / "balances.json")
    cutoff = funded_cutoff(balances)
    evidence = {}
    for row in rows:
        address = row["address"]
        item = {"oldBalanceWei": row["balanceWei"], "newBalanceWei": balances["balanceWei"][address]}
        for side, label in (("from", "outbound"), ("to", "inbound")):
            path = CACHE / f"flows-{side}-{address}.json"
            if not path.exists():
                item[label] = {"status": "pending"}
                continue
            response = read_json(path)
            query = urllib.parse.parse_qs(urllib.parse.urlparse(response["url"]).query)
            if query.get("timestampTo") != [cutoff]:
                item[label] = {"status": "pending"}
                continue
            item[label] = {
                "status": "observed" if response["result"] else "none-returned",
                "queryPageTruncated": response.get("paginated", False),
                "url": response["url"],
                "checkedAt": response["checkedAt"],
                "samples": response["result"],
            }
        path = CACHE / ("source-" + address + ".json")
        if path.exists():
            response = read_json(path)
            source = next(iter(response["result"]), {})
            content = source.get("SourceCode", "")
            item["additionalSource"] = {
                "status": "provider-source-lead" if content else "none-returned",
                "url": response["url"],
                "contractName": source.get("ContractName"),
                "compilerVersion": source.get("CompilerVersion"),
                "sourceSha256": hashlib.sha256(content.encode()).hexdigest() if content else None,
            }
        evidence[address] = item
    write_json(OUT / "funded-flows.json", {
        "scope": "Sampled early indexed successful nonzero ETH operations by direction. Index coverage, paging and protocol obligations need independent review.",
        "blockNumber": balances["blockNumber"], "blockHash": balances["blockHash"],
        "records": evidence,
    })


def source_surface(row):
    if row["sourceStatus"] != "available":
        return None
    path = SOURCE / "contracts" / (row["address"] + ".json.gz")
    with gzip.open(path, "rt") as handle:
        source = json.load(handle)["sourceResponse"]
    return {
        "files": sorted(source.get("sources", {})),
        "verification": source.get("match"),
        "functions": sorted({
            item["name"] + "(" + ",".join(arg["type"] for arg in item["inputs"]) + ")"
            for item in source.get("abi", []) if item.get("type") == "function"
        }),
        "events": sorted({
            item["name"] + "(" + ",".join(arg["type"] for arg in item["inputs"]) + ")"
            for item in source.get("abi", []) if item.get("type") == "event"
        }),
    }


def project_row(item, fields):
    result = {key: item[key] for key in fields if key in item}
    if "input" in item and fields == CALL_FIELDS:
        calldata = bytes.fromhex(item["input"].removeprefix("0x"))
        result["methodId"] = "0x" + calldata[:4].hex() if len(calldata) >= 4 else None
        result["inputSha256"] = hashlib.sha256(calldata).hexdigest()
    return result


def evidence_result(response, key, fields):
    if not response:
        return {"status": "pending"}
    if "error" in response:
        return {"status": "lookup-error", "url": response["url"], "error": response["error"]}
    result = response["result"]
    if key:
        result = [item for item in result if item.get("contractAddress", "").lower() == key]
    return {
        "status": "observed" if result else "none-returned",
        "url": response["url"],
        "checkedAt": response["checkedAt"],
        "rows": [project_row(item, fields) for item in result],
    }


def assemble(rows, batches, block):
    evidence = {}
    deployers = {}
    families = {}
    findings_path = OUT / "findings.json"
    findings = read_json(findings_path) if findings_path.exists() else {"addresses": {}, "families": []}
    reviewed_addresses = findings["addresses"]
    reviewed_families = {item["runtimeSha256"]: item for item in findings["families"]}
    archive_sources = set()
    archive_leads_path = OUT / "source-leads.json"
    if archive_leads_path.exists():
        archive_sources.update(read_json(archive_leads_path)["communitySource"])
    archive_index_path = OUT / "source-index.json"
    if archive_index_path.exists():
        for archive in read_json(archive_index_path).values():
            archive_sources.update(archive["matches"])
    supplements_path = OUT / "creation-supplements.json"
    supplements = read_json(supplements_path) if supplements_path.exists() else {}
    traces_path = OUT / "factory-traces.json"
    traces = read_json(traces_path) if traces_path.exists() else {}
    for row in rows:
        families.setdefault(row["runtimeSha256"], []).append(row["address"])
    for batch in batches:
        path = CACHE / ("creation-" + batch[0]["address"] + ".json")
        response = read_json(path) if path.exists() else None
        for row in batch:
            address = row["address"]
            path = CACHE / ("activity-" + address + ".json")
            txs = evidence_result(read_json(path) if path.exists() else None, None, CALL_FIELDS)
            creation = evidence_result(
                response, address, ("contractAddress", "contractCreator", "txHash", "contractFactory"),
            )
            if creation["status"] != "observed" and address in supplements:
                creation = supplements[address]
            for item in creation.get("rows", []):
                for trace in traces.get(address, {}).get("traces", []):
                    if trace["txHash"] == item["txHash"]:
                        item["blockNumber"] = str(trace["blockNumber"])
                        item["timeStamp"] = str(int(datetime.datetime.fromisoformat(trace["timestamp"]).timestamp()))
                        item["factoryTraceIndex"] = trace["opIndex"]
                        break
                creator = item.get("contractFactory") or item.get("contractCreator")
                if creator:
                    deployers.setdefault(creator.lower(), []).append(address)
            hashes = {item["txHash"] for item in creation.get("rows", [])}
            for item in txs.get("rows", []):
                if item["hash"] in hashes:
                    for deployment_row in creation["rows"]:
                        if deployment_row["txHash"] == item["hash"]:
                            deployment_row["blockNumber"] = item["blockNumber"]
                            deployment_row["timeStamp"] = item["timeStamp"]
                            if item.get("blockHash"):
                                deployment_row["blockHash"] = item["blockHash"]
            calls = [
                item for item in txs.get("rows", [])
                if item.get("hash") not in hashes and (item.get("to") or "").lower() == address
            ]
            samples = [
                item for item in calls
                if item.get("isError") == "0" and item.get("txreceipt_status") != "0"
                and int(item["blockNumber"]) <= block
            ]
            surface = source_surface(row)
            review = reviewed_addresses.get(address)
            family = reviewed_families.get(row["runtimeSha256"])
            source_lead = address in archive_sources
            if review:
                next_step = review["nextCheck"]
            elif family:
                next_step = "Check initialized state and deployment history for the reviewed fungible runtime."
            elif source_lead and not surface:
                next_step = "Compare the archived source and its compiler output with the pinned runtime."
            elif samples and surface:
                next_step = "Interpret the sampled successful call against verified source and historical state."
            elif samples:
                next_step = "Check the sampled call's receipts and recover source for the called code."
            elif txs["status"] == "pending":
                next_step = "Capture earliest direct transactions, then check internal calls and logs."
            else:
                next_step = "Check internal calls, logs and historical state for evidence of use."
            evidence[address] = {
                "creation": creation,
                "directActivity": txs,
                "firstSuccessfulDirectCallSample": samples[0]["hash"] if samples and hashes else None,
                "runtimeFamilySize": len(families[row["runtimeSha256"]]),
                "capturedSourceSurface": surface,
                "snapshotBalanceWei": row["balanceWei"],
                "classification": "unresolved",
                "reviewedAddressFinding": review["status"] if review else None,
                "reviewedRuntimeFinding": family["codeClassification"] if family else None,
                "externalSourceLead": source_lead,
                "nextCheck": next_step,
            }
    write_json(OUT / "evidence.json", {
        "chainId": 1,
        "throughBlock": block,
        "activityScope": "Up to eight earliest indexed direct transactions per candidate",
        "exactRuntimeFamilies": {k: v for k, v in families.items() if len(v) > 1},
        "sharedDeploymentActors": {k: v for k, v in deployers.items() if len(v) > 1},
        "records": evidence,
    })
    for field in ("creation", "directActivity"):
        counts = {}
        for item in evidence.values():
            status = item[field]["status"]
            counts[status] = counts.get(status, 0) + 1
        print(field, counts, flush=True)


def collect_factory_traces():
    evidence = read_json(OUT / "evidence.json")
    by_transaction = {}
    for item in evidence["records"].values():
        for row in item["creation"].get("rows", []):
            if row.get("contractFactory"):
                by_transaction.setdefault(row["txHash"], []).append(row)

    def get_transaction(tx_hash):
        return tx_hash, lookup(
            "factory-transaction-" + tx_hash,
            DATA_API + "/internal-operations", txHash=tx_hash, limit=100,
        )

    output = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for tx_hash, response in pool.map(get_transaction, by_transaction):
            for deployment in by_transaction[tx_hash]:
                address = deployment["contractAddress"].lower()
                factory = deployment["contractFactory"].lower()
                matches = [
                    row for row in response.get("result", [])
                    if row.get("txHash") == tx_hash and row.get("chainId") == "1"
                    and row.get("type") in {"CREATE", "CREATE2"} and row.get("status") is True
                    and (row.get("from") or "").lower() == factory
                    and (row.get("to") or "").lower() == address
                ]
                output[address] = {
                    "transactionHash": tx_hash,
                    "status": "observed" if matches else (
                        "lookup-error" if "error" in response else "none-returned"
                    ),
                    "url": response["url"],
                    "checkedAt": response.get("checkedAt"),
                    "queryPageTruncated": response.get("paginated", False),
                    "traces": matches,
                }
    write_json(OUT / "factory-traces.json", output)
    print("Factory deployment traces:", sum(x["status"] == "observed" for x in output.values()),
          "of", len(output), flush=True)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--assemble", action="store_true")
    parser.add_argument("--funded", action="store_true")
    parser.add_argument("--factory-traces", action="store_true")
    args = parser.parse_args()
    rows = [row for row in read_json(SOURCE / "records.json") if row["address"] not in KNOWN]
    block = read_json(SOURCE / "source.json")["blockNumber"]
    batches = [rows[i:i + 5] for i in range(0, len(rows), 5)]
    funded = [row for row in rows if row["balanceWei"] != "0"]
    if args.collect:
        priority = sorted(rows, key=lambda row: (
            row["year"] != "2015", row["balanceWei"] == "0", row["sourceStatus"] != "available",
        ))
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            jobs = []
            if args.funded:
                balances = read_json(OUT / "balances.json")
                through = funded_cutoff(balances)
                for i in range(0, len(funded), 5):
                    for side in ("from", "to"):
                        jobs.append(pool.submit(funded_flow, funded[i:i + 5], side, through))
                missing = sorted(
                    (row for row in funded if row["sourceStatus"] != "available"),
                    key=lambda row: int(row["balanceWei"]), reverse=True,
                )
                jobs.extend(pool.submit(extension_source, row) for row in missing[:25])
            for i, batch in enumerate(batches):
                jobs.append(pool.submit(deployment, batch))
                group = priority[i * 5:(i + 1) * 5]
                if group:
                    jobs.append(pool.submit(compact_activity, group, block))
            for i, job in enumerate(concurrent.futures.as_completed(jobs), 1):
                result = job.result()
                if "error" in result:
                    print("Lookup incomplete:", result["error"], result["url"], flush=True)
                if i % 100 == 0:
                    print(f"Completed {i}/{len(jobs)} lookups", flush=True)
    if args.collect or args.assemble:
        assemble(rows, batches, block)
    if args.funded:
        assemble_funded(funded)
    if args.factory_traces:
        collect_factory_traces()


if __name__ == "__main__":
    main()
