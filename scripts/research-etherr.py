"""Capture source rows and read-only, block-pinned bytecode evidence for every address.

This is automated triage, not a determination of NFT status. No transactions are sent.
Run: python3 scripts/research-etherr.py
"""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research' / 'etherr'
OUT.mkdir(parents=True, exist_ok=True)
RPC = 'https://ethereum-rpc.publicnode.com'
SOURCE = 'https://etherr.eth.limo/'
SELECTORS = {
    '01ffc9a7': 'supportsInterface(bytes4)', '6352211e': 'ownerOf(uint256)',
    'c87b56dd': 'tokenURI(uint256)', '2f745c59': 'tokenOfOwnerByIndex(address,uint256)',
    '42842e0e': 'safeTransferFrom(address,address,uint256)',
    'b88d4fde': 'safeTransferFrom(address,address,uint256,bytes)',
    '70a08231': 'balanceOf(address)', 'a9059cbb': 'transfer(address,uint256)',
    '23b872dd': 'transferFrom(address,address,uint256)', '18160ddd': 'totalSupply()',
    '095ea7b3': 'approve(address,uint256)',
}

def rpc(calls):
    payload = [{'jsonrpc': '2.0', 'id': i, 'method': method, 'params': params}
               for i, (method, params) in enumerate(calls)]
    for attempt in range(5):
        try:
            request = urllib.request.Request(RPC, data=json.dumps(payload).encode(),
                                             headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.load(response)
            indexed = {r['id']: r for r in result}
            if len(indexed) != len(calls):
                raise ValueError('Incomplete RPC batch')
            ordered = [indexed[i] for i in range(len(calls))]
            if any('rate limit' in json.dumps(item.get('error', {})).lower() for item in ordered):
                raise RuntimeError('RPC rate limit; backing off')
            return ordered
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)

manifest_path = OUT / 'source.json'
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    rows = json.loads((OUT / 'source-records.json').read_text())
else:
    with urllib.request.urlopen(SOURCE, timeout=45) as response:
        html = response.read()
        ipfs = response.headers.get('x-ipfs-path')
    match = re.search(r'const DATA=(\[.*?\]);', html.decode(), re.S)
    rows = json.loads(match.group(1))
    assert len({r['address'].lower() for r in rows}) == len(rows)
    assert all(re.fullmatch(r'0x[0-9a-fA-F]{40}', r['address']) for r in rows)
    chain, block = rpc([('eth_chainId', []), ('eth_getBlockByNumber', ['latest', False])])
    assert chain['result'] == '0x1'
    block = block['result']
    manifest = {'url': SOURCE, 'title': 'Claimables 2015-2017',
                'capturedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'sourceHtmlSha256': hashlib.sha256(html).hexdigest(), 'ipfsPath': ipfs,
                'chainId': 1, 'blockNumber': int(block['number'], 16),
                'blockHash': block['hash'], 'rpc': RPC, 'count': len(rows),
                'methodology': 'Every address: eth_getCode at the same block; disassemble PUSH4 operands; when supportsInterface selector is present, eth_call ERC165, invalid ID, ERC721 and ERC1155 with 30000 gas. These are heuristic signals only. Missing selectors do not rule out historical NFTs; proxies and nonstandard designs require source/storage/event research. Source labels are unverified and retained verbatim. No claim, mint, approval or transaction is performed.'}
    (OUT / 'source-records.json').write_text(json.dumps(rows, indent=2) + '\n')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')

block_tag = hex(manifest['blockNumber'])
checkpoint = OUT / '.checkpoint.jsonl'
done = {}
if checkpoint.exists():
    for line in checkpoint.read_text().splitlines():
        item = json.loads(line)
        done[item['address'].lower()] = item

def inspect(batch):
    replies = rpc([('eth_getCode', [row['address'], block_tag]) for row in batch])
    output = []
    for row, reply in zip(batch, replies):
        item = dict(row, address=row['address'].lower(), status='unresolved', review='automated-triage-only')
        if 'error' in reply:
            raise RuntimeError(json.dumps(reply['error']))
        code = bytes.fromhex(reply['result'][2:])
        pushes = set()
        i = 0
        while i < len(code):
            opcode = code[i]
            size = opcode - 0x5f if 0x60 <= opcode <= 0x7f else 0
            if size == 4 and i + 4 < len(code):
                pushes.add(code[i + 1:i + 5].hex())
            i += 1 + size
        found = [{'selector': '0x' + s, 'signature': SELECTORS[s]} for s in sorted(pushes & SELECTORS.keys())]
        item.update(codeBytes=len(code), runtimeSha256=hashlib.sha256(code).hexdigest(), selectors=found)
        item['signal'] = 'nft-method-signal' if pushes & {'6352211e', 'c87b56dd', '2f745c59', '42842e0e', 'b88d4fde'} else ('token-method-signal' if pushes & {'a9059cbb', '70a08231'} else ('no-runtime-code' if not code else 'nonstandard-or-other'))
        item['interfaces'] = {}
        if '01ffc9a7' in pushes:
            interfaces = [('erc165', '01ffc9a7'), ('invalid', 'ffffffff'), ('erc721', '80ac58cd'), ('erc1155', 'd9b67a26')]
            results = rpc([('eth_call', [{'to': item['address'], 'data': '0x01ffc9a7' + interface + '0' * 56, 'gas': hex(30000)}, block_tag]) for _, interface in interfaces])
            for (label, _), result in zip(interfaces, results):
                item['interfaces'][label] = result.get('result', result.get('error'))
        output.append(item)
    return output

pending = [r for r in rows if r['address'].lower() not in done]
batches = [pending[i:i + 15] for i in range(0, len(pending), 15)]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool, checkpoint.open('a') as log:
    for result in pool.map(inspect, batches):
        for item in result:
            log.write(json.dumps(item) + '\n')
            done[item['address']] = item
        log.flush()
        print(f'{len(done)}/{len(rows)} contracts inspected at block {manifest["blockNumber"]}', flush=True)

assert len(done) == len(rows)
ordered = [done[r['address'].lower()] for r in rows]
(OUT / 'records.json').write_text(json.dumps(ordered, indent=2) + '\n')
print('Complete. NFT status remains unresolved until evidence is reviewed.', flush=True)
