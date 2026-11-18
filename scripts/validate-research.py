"""Validate full per-address evidence coverage without making network requests."""
import collections
import decimal
import gzip
import hashlib
import json
from pathlib import Path

decimal.getcontext().prec = 100
root = Path(__file__).resolve().parents[1] / 'research' / 'etherr'
source = json.loads((root / 'source.json').read_text())
originals = json.loads((root / 'source-records.json').read_text())
records = json.loads((root / 'records.json').read_text())
notes = json.loads((root / 'preliminary-notes.json').read_text())
assert len(records) == len(originals) == source['count']
assert len({row['address'] for row in records}) == len(records)
original = {row['address'].lower(): row for row in originals}
for row in records:
    assert row['address'] in original
    assert all(row[field] == original[row['address']][field] for field in ['name', 'created', 'year', 'category', 'kind'])
    assert row['status'] == 'unresolved' and row['review'] == 'automated-triage-only'
    assert row['evaluation']['ethRecoverability'] == 'not-assessed'
    assert decimal.Decimal(row['balanceEth']) * decimal.Decimal(10**18) == decimal.Decimal(row['balanceWei'])
    with gzip.open(root / 'contracts' / (row['address'] + '.json.gz'), 'rt') as file:
        artifact = json.load(file)
    assert artifact['address'] == row['address']
    assert artifact['blockHash'] == source['blockHash'] and artifact['blockNumber'] == source['blockNumber']
    code = bytes.fromhex(artifact['runtimeBytecode'][2:])
    assert len(code) == row['codeBytes']
    assert hashlib.sha256(code).hexdigest() == row['runtimeSha256']
    assert artifact['summary']['balanceWei'] == row['balanceWei']
    if row['sourceRuntimeAgrees']:
        assert artifact['sourceResponse']['runtimeBytecode']['onchainBytecode'].lower() == artifact['runtimeBytecode'].lower()
    for note in notes.get(row['address'], []):
        assert row['sourceRuntimeAgrees'] and note['file'] in artifact['sourceResponse']['sources']
assert set(notes).issubset(original)
assert len(list((root / 'contracts').glob('*.json.gz'))) == len(records)
print(json.dumps({'validated': len(records), 'funded': sum(int(row['balanceWei']) > 0 for row in records),
                  'sourceStatuses': dict(collections.Counter(row['sourceStatus'] for row in records)),
                  'sourceRuntimeMatches': sum(row['sourceRuntimeAgrees'] for row in records),
                  'allClassifications': 'unresolved', 'snapshotBlock': source['blockNumber']}, indent=2))
