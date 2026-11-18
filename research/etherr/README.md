# the 0xzxch list

Attributed to [@0xzxch's post](https://x.com/0xzxch/status/2122996595637588119), using the contract rows published at https://etherr.eth.limo/.

This directory preserves every source address and automated, read-only evidence. It is a research queue, not a list of confirmed NFTs or claimable funds. Exact address matches to existing catalogue contracts are computed by the frontend from this same source revision; name similarity alone never removes a candidate.

- `source-records.json`: the original 2,577 rows, with source labels, names and dates unchanged.
- `source.json`: capture time, source HTML SHA-256, Ethereum block number/hash, RPC provider and methodology.
- `records.json`: per-address code signals, ETH balance and unresolved evaluation fields.
- `contracts/{address}.json.gz`: actual runtime bytecode, balance evidence and the available Sourcify source/ABI response for that address.
- `preliminary-notes.json`: explicitly bounded source readings with file/line references; these do not establish a completed review or recovery eligibility.

Run `python3 scripts/research-etherr.py`, then `python3 scripts/enrich-etherr.py` from the repository root. Scripts resume the recorded snapshot instead of silently mixing blocks. A new snapshot should use a new versioned directory rather than overwriting the provenance of this capture. The ignored checkpoint is only a local resume aid; committed records and artifacts are the deliverables.

Run `python3 scripts/validate-research.py` to independently validate complete coverage, source-row preservation, bytecode hashes, balances, block identity and source-note prerequisites without network access. Sourcify bulk requests were stopped after its API returned a rate limit and stated that bulk collection is unsupported. Remaining source lookups are explicitly incomplete. The enrichment script defaults to reusing captured source only; `--lookup-address=0x...` permits one individually requested lookup, without retrying rate limits.

PUSH4 operands are limited heuristic leads. They can collide, be unused, or belong to proxy code. Old NFTs can predate standard interfaces, and a token-like interface does not by itself rule out historical collectible behavior. Source labels such as FUNGIBLE_TOKEN and NFT are unverified source assertions. They are not the research conclusion.

Sourcify's source verification and an exact comparison of its runtime against the RPC snapshot are recorded separately. An unsuccessful lookup does not prove that no verified source exists elsewhere. No automated source analysis establishes the interpretation of the Solidity or contract permissions.

ETH balances are exact wei values at the recorded block. A positive balance does not establish recoverability, permission, entitlement, solvency, or absence of obligations to users. Withdrawal/claim/refund-like ABI names are investigation leads only. No claim, mint, approval, wallet action or transaction is performed.

The evaluation worksheet uses the catalogue's dimensions but keeps unknowns unknown: NFT classification, non-fungibility, fixed supply, asset storage, wrapper/unwrap behavior, development status, marketplace status, and security concerns. Promotion into `nfts/` requires a sourced human interpretation; no letter grade is invented for unreviewed contracts.

See [deployment and activity research](history/README.md) for the second-pass
evidence, archival source leads, ETH balance refresh, and reviewed findings.
