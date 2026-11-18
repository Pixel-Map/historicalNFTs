# Catalogue evidence review

[review.json](review.json) records the evidence for the Etheria, Pride Punks
and CryptoCities corrections. Chain reads describe a named block. The Etheria
supply and version history come from the creator's documentation. The
Pride Punks owner observation identifies the contract that held that role at
the checked block. CryptoCities' null values preserve uncertainty about the
original supply and cap enforcement.

To check source consistency for the full catalogue, run
`python3 scripts/validate-catalogue.py` from the repository root with PyYAML
installed. CI runs the same check. To reproduce the partial-evidence decisions
for the corrected records, use the LogicPearl CLI with its evidence commands:

```sh
python3 scripts/review-catalogue-evidence.py \
  --logicpearl ~/Documents/LogicPearl/logicpearl/target/debug/logicpearl
```

Follow the same process for each new claim: specify the deployment and role,
tie evidence to that exact subject, and leave assertions unresolved when
coverage is incomplete. Assess identity, transfer behavior, supply caps,
administrative control, metadata, and wrapper provenance as distinct claims.
The policy evaluates reviewed observations rather than extracting source code or
inferring what a missing observation means.

## DADA wrapper provenance and reversibility

[dada-wrapper.json](dada-wrapper.json) records the exact-matched wrapper source,
two origin samples with owner and metadata URI reads at a finalized block, and
successful historical unwrap receipts for both branches. Each receipt contains
a wrapper burn and a transfer from the corresponding original back to the
burned token's holder. This establishes observed reversibility, while individual
eligibility still depends on the asset and contract state. The source's
owner-controlled metadata base URI describes the wrapper transport and makes
no claim about storage of the original artwork.

Run `python3 scripts/review-wrapper-provenance.py --logicpearl PATH` from the
repository root with the evidence CLI. The same wrapper address passes the
loose test for both samples. The version-aware rule passes the 2017 sample,
rejects the 2019 sample for a 2017 provenance claim, and returns unknown when the
origin is missing. The verifier also checks implication in the declared policy
domain. These checks use the bounded archived observations as inputs.

### Read-only ABI learning pilot

[dada-abi-observations.json](dada-abi-observations.json) contains 77 distinct
wrapped token IDs from indexed events, and public read-only `ownerOf` and
`tokenURI` outputs read at the same finalized block. The event branch labels the
origin. The cohorts are split by event time and token IDs never repeat across
folds. The input IDs and event data are withheld from the learner. The second
trial uses the numeric filename extracted from the actual metadata response.

`python3 scripts/review-wrapper-abi.py --logicpearl PATH` reproduces the
[result](dada-abi-result.json). Call success and HTTPS hostname alone collide
across origin years. The numeric response let LogicPearl learn a threshold
and classify all 38 readable later samples. One later sample had no numeric
metadata response and was left unresolved. A separate search of 252 indexed
2019 wrap events found a still-readable 2019 token below the learned threshold
that the compiled classifier mislabels as 2017. The event-backed policy is
the authority for that example. The observed prefix heuristic also got all
38 readable holdout cases right and gets the challenge right. Its behavior
outside the sampled/verified domain is unproven, too.

A separate 2019 event pair documents the same wrapped ID being burned and
later reissued. When assessing ownership or age, distinguish the original
asset's identity, its wrapping history and its existence at the observed block.
