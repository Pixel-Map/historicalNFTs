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
