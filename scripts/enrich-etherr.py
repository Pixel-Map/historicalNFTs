"""Capture balance, runtime code and available verified source for all research leads.
Read-only. Resumable artifacts are pinned to the first scan's Ethereum block.
"""
import concurrent.futures
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import sys
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research' / 'etherr'
ARTIFACTS = OUT / 'contracts'
ARTIFACTS.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('scan', ROOT / 'scripts' / 'research-etherr.py')
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)
scan.RPC = 'https://ethereum-rpc.publicnode.com'
records = json.loads((OUT / 'records.json').read_text())
manifest = json.loads((OUT / 'source.json').read_text())
block = hex(manifest['blockNumber'])
chain, snapshot = scan.rpc([('eth_chainId', []), ('eth_getBlockByNumber', [block, False])])
assert chain['result'] == '0x1' and snapshot['result']['hash'] == manifest['blockHash']
lookup_address = next((arg.split('=', 1)[1].lower() for arg in sys.argv if arg.startswith('--lookup-address=')), None)

def capture(row):
    address = row['address']
    target = ARTIFACTS / (address + '.json.gz')
    if target.exists():
        with gzip.open(target, 'rt') as f:
            previous = json.load(f)
        if address != lookup_address:
            return previous['summary']
    time.sleep(1.25)
    scan.RPC = 'https://rpc.flashbots.net'
    balance = scan.rpc([('eth_getBalance', [address, block])])[0]
    scan.RPC = 'https://ethereum-rpc.publicnode.com'
    code = scan.rpc([('eth_getCode', [address, 'latest'])])[0]
    if 'error' in balance or 'error' in code:
        raise RuntimeError(f'RPC failure for {address}')
    runtime = code['result']
    assert hashlib.sha256(bytes.fromhex(runtime[2:])).hexdigest() == row['runtimeSha256']
    wei = int(balance['result'], 16)
    eth = f'{wei // 10**18}.{wei % 10**18:018d}'.rstrip('0').rstrip('.')
    url = f'https://sourcify.dev/server/v2/contract/1/{address}?fields=sources,abi,runtimeBytecode.onchainBytecode'
    verified = None
    source_status = 'not-queried-provider-limit'
    # Sourcify's API is for single-contract lookups, not bulk collection.
    # Preserve results already captured; further lookups must be explicitly individual.
    for attempt in range(1 if address == lookup_address else 0):
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                verified = json.load(response)
            source_status = 'available' if verified.get('runtimeMatch') in ['match', 'exact_match'] else 'unverified'
            break
        except urllib.error.HTTPError as error:
            if error.code == 404:
                source_status = 'not-found'
                break
            if error.code == 429:
                source_status = 'provider-rate-limited'
                break
            if error.code not in [429, 500, 502, 503, 504]:
                source_status = 'lookup-error'
                break
            time.sleep(2 ** attempt)
            source_status = 'lookup-error'
        except Exception:
            time.sleep(2 ** attempt)
            source_status = 'lookup-error'
    abi = verified.get('abi', []) if verified else []
    functions = [item for item in abi if item.get('type') == 'function']
    withdrawal = [{'name': f['name'], 'inputs': f.get('inputs', []), 'stateMutability': f.get('stateMutability')} for f in functions
                  if any(word in f.get('name', '').lower() for word in ['withdraw', 'claim', 'refund', 'payout', 'cashout', 'collect', 'sweep'])]
    # A source match is only treated as evidence for this runtime if it agrees with the RPC snapshot.
    provider_code = verified.get('runtimeBytecode', {}).get('onchainBytecode') if verified else None
    source_agrees = bool(provider_code and provider_code.lower() == runtime.lower())
    summary = dict(row, balanceWei=str(wei), balanceEth=eth, sourceStatus=source_status,
                   sourceRuntimeAgrees=source_agrees, sourceURL=url, abiFunctionCount=len(functions),
                   withdrawalFunctions=withdrawal,
                   evaluation={'nftStatus': 'unresolved', 'assetDataLocation': 'not-reviewed',
                               'staticSupply': 'not-reviewed', 'nonfungible': 'not-reviewed',
                               'activeDevelopment': 'not-reviewed', 'openseaVerification': 'not-reviewed',
                               'wrapperAndUnwrap': 'not-reviewed', 'securityConcerns': 'not-reviewed',
                               'ethRecoverability': 'not-assessed'})
    artifact = {'address': address, 'chainId': 1, 'blockNumber': manifest['blockNumber'],
                'blockHash': manifest['blockHash'], 'summary': summary, 'runtimeBytecode': runtime,
                'balanceRPC': 'https://rpc.flashbots.net', 'runtimeCodeRPC': scan.RPC,
                'runtimeCodeRetrievalTag': 'latest; SHA-256 verified identical to the original block-pinned eth_getCode capture',
                'sourceProvider': 'Sourcify', 'sourceResponse': verified}
    with gzip.open(target, 'wt', encoding='utf-8') as output:
        json.dump(artifact, output)
    return summary

summaries = []
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    for row in pool.map(capture, records):
        summaries.append(row)
        if len(summaries) % 100 == 0:
            print(f'{len(summaries)}/{len(records)} balance/code/source captures', flush=True)
assert len(summaries) == len(records)
(OUT / 'records.json').write_text(json.dumps(summaries, indent=2) + '\n')
manifest['enrichment'] = {'balance': 'eth_getBalance at the same block',
                          'artifacts': 'contracts/{address}.json.gz contains actual runtime bytecode, summary and available Sourcify response',
                          'sourceVerification': 'Provider runtime match and exact equality against RPC runtime recorded separately; source lookup failure is not proof that verified source does not exist elsewhere.',
                          'eth': 'A positive balance is ETH held at this block, not evidence of recoverability. Withdraw/claim/refund ABI names are leads, not proof of permission or entitlement.'}
manifest['attribution'] = {'name': 'the 0xzxch list', 'author': '0xzxch', 'url': 'https://x.com/0xzxch/status/2122996595637588119'}
manifest['sourceLookupLimitation'] = 'Sourcify returned a rate-limit response stating that this API is for single-contract lookups, not bulk collection. Bulk source requests were stopped. Previously captured responses are preserved; remaining addresses have runtime bytecode and balance artifacts with source lookup explicitly incomplete. The script permits one explicit --lookup-address=0x... lookup at a time and does not retry rate limits.'
manifest['balanceRPCProviders'] = ['https://ethereum-rpc.publicnode.com', 'https://rpc.flashbots.net']
manifest['archiveRPCNote'] = 'PublicNode completed the initial runtime scan. As the pinned block aged, its free endpoint required an archive token. Remaining balances were read through Flashbots at the identical mainnet block (block hash verified). Remaining raw code was retrieved at latest through PublicNode and accepted only when its SHA-256 exactly matched the original block-pinned code hash. A mismatch fails capture; code changes are never silently substituted. Older artifacts without explicit provider fields used PublicNode at the pinned block.'
(OUT / 'source.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Enrichment complete for every contract.', flush=True)
