#!/usr/bin/env python3
"""Refresh mainnet balances at one finalized block, preserving the previous snapshot."""

import datetime
import json
import time
import urllib.request

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "research/etherr"
RPC = "https://ethereum-rpc.publicnode.com"


def query(calls):
    payload = [
        {"jsonrpc": "2.0", "id": i, "method": method, "params": params}
        for i, (method, params) in enumerate(calls)
    ]
    request = urllib.request.Request(
        RPC, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        results = {item["id"]: item for item in json.load(response)}
    return [results[i]["result"] for i in range(len(calls))]


def main():
    chain, block = query([("eth_chainId", []), ("eth_getBlockByNumber", ["finalized", False])])
    assert chain == "0x1"
    rows = [
        row for row in json.loads((ROOT / "records.json").read_text())
        if row["balanceWei"] != "0"
    ]
    balances = {}
    for i in range(0, len(rows), 10):
        batch = rows[i:i + 10]
        results = query([
            ("eth_getBalance", [row["address"], block["number"]]) for row in batch
        ])
        balances.update({
            row["address"]: str(int(value, 16)) for row, value in zip(batch, results)
        })
        time.sleep(1.1)
    confirmed, = query([("eth_getBlockByNumber", [block["number"], False])])
    assert confirmed["hash"] == block["hash"]
    assert len(balances) == len(rows)
    out = ROOT / "history" / "balances.json"
    out.parent.mkdir(exist_ok=True)
    temporary = out.with_suffix(".tmp")
    temporary.write_text(json.dumps({
        "chainId": 1,
        "blockNumber": int(block["number"], 16),
        "blockHash": block["hash"],
        "blockTimestamp": datetime.datetime.fromtimestamp(
            int(block["timestamp"], 16), datetime.timezone.utc,
        ).isoformat(),
        "rpc": RPC,
        "coverage": "all addresses with nonzero balance in the original snapshot",
        "balanceWei": balances,
    }, indent=2) + "\n")
    temporary.replace(out)
    print(f"Captured {len(balances)} balances at {int(block['number'], 16)}")


if __name__ == "__main__":
    main()
