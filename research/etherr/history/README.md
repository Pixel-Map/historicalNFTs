# Deployment and activity research

This is the second research pass on **the 0xzxch list**. It keeps the original
source rows and its Ethereum snapshot intact. Two exact catalogue matches are
excluded from the 2,575-address candidate pass. The research evidence and
reviewed findings can be joined using the lowercase contract address.

- [evidence.json](evidence.json) records the creation transaction reported by
  Routescan, up to eight earliest indexed direct transactions through block
  26,443,825, exact runtime and deployment actor groups, the ABI surface where
  source was captured, and an address-specific next check.
  [creation-supplements.json](creation-supplements.json) contains a deployment
  verified from its indexed receipt after the bulk creation endpoint omitted it.
  [factory-traces.json](factory-traces.json) records indexed internal CREATE
  evidence for children deployed through a factory.
- [findings.json](findings.json) records reviewed readings of representative
  source, original project documentation, and particular transactions. A finding
  about a shared runtime applies to executable code. Deployment parameters,
  project identity, and transaction history remain specific to each address.
- [balances.json](balances.json) refreshes the exact wei balances for all
  addresses funded in the original snapshot at one new finalized block. A second
  RPC provider agreed on the block hash and the five largest balances.
- [funded-flows.json](funded-flows.json) samples indexed ETH operations in both
  directions and records source lookups for the 25 largest funded candidates
  missing captured source. A positive balance or a historical payout alone
  establishes neither liabilities nor entitlement. No transaction was sent.
- [source-leads.json](source-leads.json) matches an archived Solidity corpus by
  address and checks Ethereum History's entries for all 87 candidates dated
  2015. In these 87 entries, the field labeled runtime by that provider matches
  the **creation transaction input**. Runtime equivalence is a separate check.
- [source-index.json](source-index.json) searches pinned archived source
  repositories by exact address. Each link is a source lead. Compiler settings
  and runtime correspondence still need review.

`observed` means the indexed query returned a sample. `none-returned` means the
query returned no sample under its recorded filters. `pending` means a lookup
is outstanding. Grouped ETH flow samples include paging information and can be
incomplete for an individual address. Early direct calls can be setup, tests,
or failures that returned without a revert. ERC transfer semantics and actual
ownership changes require source, receipt logs, execution traces, or historical
state. Some public RPC endpoints prune execution history before block
15,500,000. The research files distinguish provider-indexed results from
separately verified evidence.

The highest-priority manual work is to confirm item-level use, version history,
and asset storage for nonstandard candidates, and to reconcile funded contracts
with their documented obligations. The candidate baseline keeps NFT and
recoverability decisions unresolved. Reviewed observations are additive.

## Reproduce or resume

From the repository root:

1. Run `python3 scripts/research-history-balances.py` to create a new balance
   snapshot. Save a copy of the previous snapshot when refreshing research.
2. Run `python3 scripts/research-history.py --collect --funded`. It uses the
   local `.cache/etherr-history/` checkpoint and stays below Routescan's
   documented keyless request rate. To regenerate from captured responses, use
   `--assemble --funded`. Then run `--factory-traces` to corroborate the
   factory deployments, then assemble again to join the child creation blocks.
3. Obtain the tarball for
   [ethereum-contract-scraper at the pinned commit](https://github.com/rllola/ethereum-contract-scraper/tree/475bf1f3a9507f54a1ae5959d753e9a36ca262bc).
   Run `python3 scripts/research-history-archive.py --archive-2015 --community-tar PATH`.
4. Run `python3 scripts/research-history-source-index.py` with an authenticated
   GitHub CLI to cross-check the pinned source trees.
5. Run `python3 scripts/validate-research.py` and
   `python3 scripts/validate-history.py` offline.

## Reproduce the featured Solidity matches

[findings.json](findings.json) records five byte-for-byte matches for creation
input and runtime bytecode. Use the pinned source file as published, including
comments. The source, compiler and output hashes in the finding identify the
specific inputs and results.

- **EtherId:** use the `solc@0.3.5` npm package and
  `solc.compile(sourceText, 0).contracts.EtherId`.
- **Etheria prototypes:** follow the [creator's verification recipe](https://github.com/cyrusadkisson/etheria_source/blob/0ec8b64ee6dbb0812a1ad6ce173b79b6a2a64b4e/NKNVELSC/README.md)
  with the exact compiler file listed for the address. Run each file in a
  fresh process and enable the optimizer.

Hash the compiled `bytecode` and `runtimeBytecode` properties as bytes
decoded from hex. Compare the former to the creation transaction input and
the latter to the original snapshot's runtime artifact.
